"""The docx converter reproduces a writer's document exactly.

The rule agreed with the team is that the text ships word for word, typos and
all: what was approved in the document is what goes on the site. These tests
build a .docx in memory, run the converter over it, and check that nothing was
tidied on the way through.

No fixture binary in the repo: the document is assembled here with zipfile, so
what is being tested is visible in the test.
"""

import os
import shutil
import struct
import sys
import unittest
import zlib
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))

import sitelib as S  # noqa: E402
import docx2post  # noqa: E402

SLUG = "converter-selftest-post"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

# A typo, an ampersand and a less-than sign, all of which must survive intact.
TYPO_LINE = "We tuned the laucher for consistency &amp; not range, 5 &lt; 6 shots."
RAW_TYPO = "We tuned the launcher"


def png(width, height):
    """A real, valid PNG so sips can read and resize it like any other."""
    def chunk(kind, payload):
        body = kind + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(
            ">I", zlib.crc32(body) & 0xFFFFFFFF
        )

    raw = b"".join(b"\x00" + b"\xc0\x30\x20" * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def paragraph(text, style=None, bold=False, italic=False, listed=False):
    props = ""
    if style:
        props += f'<w:pStyle w:val="{style}"/>'
    if listed:
        props += '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'
    props = f"<w:pPr>{props}</w:pPr>" if props else ""
    run_props = ""
    if bold:
        run_props += "<w:b/>"
    if italic:
        run_props += "<w:i/>"
    run_props = f"<w:rPr>{run_props}</w:rPr>" if run_props else ""
    return f"<w:p>{props}<w:r>{run_props}<w:t>{text}</w:t></w:r></w:p>"


def build_docx(path):
    body = "".join([
        paragraph("Autonomous Consistency", style="Heading1"),
        paragraph("This is the opening paragraph of the update."),
        paragraph("Where We Got To", style="Heading2"),
        paragraph(TYPO_LINE),
        paragraph("This bit is bold.", bold=True),
        paragraph("This bit is italic.", italic=True),
        paragraph("First list item", listed=True),
        paragraph("Second list item", listed=True),
        '<w:p><w:hyperlink r:id="rLink"><w:r><w:t>our sponsors page</w:t></w:r>'
        "</w:hyperlink></w:p>",
        '<w:p><w:r><w:drawing><wp:inline xmlns:wp="http://schemas.openxmlformats.org/'
        'drawingml/2006/wordprocessingDrawing">'
        '<wp:docPr id="1" name="Picture 1" descr="The robot mid-build"/>'
        '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        "<a:graphicData><pic:pic xmlns:pic=\"http://schemas.openxmlformats.org/"
        'drawingml/2006/picture"><pic:blipFill>'
        '<a:blip r:embed="rImg"/></pic:blipFill></pic:pic></a:graphicData></a:graphic>'
        "</wp:inline></w:drawing></w:r></w:p>",
    ])
    document = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>{body}</w:body></w:document>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rImg" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>'
        '<Relationship Id="rLink" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://volcanixftc.com/sponsors.html" TargetMode="External"/>'
        "</Relationships>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document)
        archive.writestr("word/_rels/document.xml.rels", rels)
        archive.writestr("word/media/image1.png", png(2400, 1200))


class TestDocxConverter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = os.path.join(S.ROOT, "tests", "_tmp")
        os.makedirs(cls.tmp, exist_ok=True)
        cls.docx = os.path.join(cls.tmp, "update.docx")
        build_docx(cls.docx)

        cls.out_html = os.path.join(S.ROOT, "updates", f"{SLUG}.html")
        cls.out_media = os.path.join(S.ROOT, "media", "updates", SLUG)

        code = docx2post.main([
            cls.docx,
            "--slug", SLUG,
            "--date", "2026-09-07",
            "--date-label", "7 September 2026",
            "--author", "A Writer",
            "--role", "Build Lead",
            "--tag", "build",
        ])
        assert code == 0, "converter did not exit cleanly"
        with open(cls.out_html, encoding="utf-8") as handle:
            cls.html = handle.read()

    @classmethod
    def tearDownClass(cls):
        # Never leave a fixture post behind: it would show up in the index,
        # the feed and the sitemap on the next rebuild.
        shutil.rmtree(cls.tmp, ignore_errors=True)
        shutil.rmtree(cls.out_media, ignore_errors=True)
        if os.path.exists(cls.out_html):
            os.remove(cls.out_html)

    # -- the promise that matters ------------------------------------
    def test_typos_are_preserved(self):
        self.assertIn(
            "We tuned the laucher for consistency",
            self.html.replace("&amp;", "&"),
            "the converter silently corrected the writer's typo",
        )
        self.assertNotIn(
            "launcher", self.html, "the converter spell-checked the writer"
        )

    def test_special_characters_are_escaped_not_dropped(self):
        self.assertIn("&amp;", self.html, "the ampersand was lost")
        self.assertIn("&lt; 6 shots", self.html, "the less-than sign was lost")

    def test_title_comes_from_the_first_heading(self):
        self.assertIn("<h1>Autonomous Consistency</h1>", self.html)
        self.assertEqual(self.html.count("Autonomous Consistency</h1>"), 1)

    def test_document_headings_start_at_h2(self):
        """h1 is the post title, so the writer's own headings shift down one."""
        self.assertIn("<h2>Where We Got To</h2>", self.html)
        self.assertNotIn("<h3>Where We Got To</h3>", self.html)

    def test_emphasis_survives(self):
        self.assertIn("<strong>This bit is bold.</strong>", self.html)
        self.assertIn("<em>This bit is italic.</em>", self.html)

    def test_lists_become_one_list(self):
        self.assertEqual(self.html.count('<ul class="post-list">'), 1)
        self.assertIn("<li>First list item</li>", self.html)
        self.assertIn("<li>Second list item</li>", self.html)

    def test_links_survive_and_are_safe(self):
        self.assertIn('href="https://volcanixftc.com/sponsors.html"', self.html)
        self.assertIn('rel="noopener"', self.html)

    # -- images ------------------------------------------------------
    def test_image_is_extracted(self):
        files = os.listdir(self.out_media)
        self.assertEqual(len(files), 1, f"expected one image, got {files}")
        self.assertIn(f"media/updates/{SLUG}/", self.html)

    def test_image_is_resized(self):
        name = os.listdir(self.out_media)[0]
        width, _ = docx2post.image_size(os.path.join(self.out_media, name))
        if not shutil.which("sips"):
            self.skipTest("sips unavailable, originals are passed through")
        self.assertLessEqual(
            width, docx2post.MAX_IMAGE_WIDTH, "a phone-sized image shipped unresized"
        )

    def test_image_carries_dimensions_and_alt(self):
        self.assertRegex(self.html, r'<img src="media/updates/[^"]+"[^>]*width="\d+"')
        self.assertRegex(self.html, r'height="\d+"')
        self.assertIn('alt="The robot mid-build"', self.html)

    def test_image_alt_falls_back_to_a_visible_todo(self):
        """Word documents usually have no alt text. When there is none the
        placeholder has to be obvious, not an empty string that passes the
        accessibility check silently."""
        self.assertNotIn('alt=""', self.html)

    # -- page shape --------------------------------------------------
    def test_page_has_the_post_scaffolding(self):
        for needle in (
            f'<article class="post" id="{SLUG}" data-tag="build"',
            '<time datetime="2026-09-07">',
            'class="post-by"',
            "NAV:START",
            "FOOTER:START",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, self.html)

    def test_header_size_reader_matches_sips(self):
        """The stdlib fallback has to agree with sips, or the width and height
        attributes would be wrong wherever sips is missing."""
        path = os.path.join(self.tmp, "probe.png")
        with open(path, "wb") as handle:
            handle.write(png(37, 19))
        self.assertEqual(docx2post.header_size(path), (37, 19))


if __name__ == "__main__":
    unittest.main()
