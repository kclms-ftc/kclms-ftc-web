"""Links and assets: nothing points at a file that is not there."""

import glob
import os
import unittest

import sitelib as S

ALL_HTML = sorted(
    os.path.basename(p) for p in glob.glob(os.path.join(S.ROOT, "*.html"))
)

# Attributes that carry a URL we can resolve on disk.
URL_ATTRS = ("href", "src", "data")


def local_refs(page):
    for node in page.find_all():
        for attr in URL_ATTRS:
            value = node.get(attr)
            if not value or value.startswith("#") or S.is_external(value):
                continue
            yield node, attr, value


class TestLinks(unittest.TestCase):
    def test_local_references_resolve(self):
        for name in ALL_HTML:
            page = S.Page.load(name)
            for node, attr, value in local_refs(page):
                target = S.local_target(value)
                with self.subTest(page=name, ref=value, line=node.line):
                    self.assertTrue(
                        os.path.exists(target),
                        f"{name}:{node.line} <{node.tag} {attr}=\"{value}\"> "
                        f"does not resolve",
                    )

    def test_in_page_anchors_resolve(self):
        for name in ALL_HTML:
            page = S.Page.load(name)
            ids = set(page.ids())
            for anchor in page.find_all("a"):
                href = anchor.get("href") or ""
                if not href.startswith("#") or href == "#":
                    continue
                with self.subTest(page=name, anchor=href):
                    self.assertIn(
                        href[1:], ids, f"{name}:{anchor.line} {href} has no target"
                    )

    def test_new_tab_links_are_safe(self):
        for name in ALL_HTML:
            page = S.Page.load(name)
            for anchor in page.find_all("a"):
                if anchor.get("target") != "_blank":
                    continue
                rel = (anchor.get("rel") or "").split()
                with self.subTest(page=name, href=anchor.get("href")):
                    self.assertIn(
                        "noopener",
                        rel,
                        f"{name}:{anchor.line} target=_blank without rel=noopener",
                    )

    def test_no_page_links_to_a_redirect_stub(self):
        """Stubs exist for inbound traffic only. Linking one internally costs a
        needless hop and leaks a dead URL back into the site."""
        for name in S.BUILT_PAGES:
            page = S.Page.load(name)
            for anchor in page.find_all("a"):
                target = S.normalise_href(anchor.get("href"))
                with self.subTest(page=name, href=anchor.get("href")):
                    self.assertNotIn(
                        target,
                        S.REDIRECT_STUBS,
                        f"{name}:{anchor.line} links the {target} stub; "
                        f"link {S.REDIRECT_STUBS.get(target)} directly",
                    )

    def test_pdfs_are_downloadable(self):
        """Every inline PDF embed is paired with a download link, because most
        phones will not render the object."""
        for name in S.BUILT_PAGES:
            page = S.Page.load(name)
            for obj in page.find_all("object"):
                data = obj.get("data") or ""
                if not data.endswith(".pdf"):
                    continue
                links = [a.get("href") for a in page.find_all("a")]
                with self.subTest(page=name, pdf=data):
                    self.assertIn(
                        data, links, f"{name} embeds {data} with no download link"
                    )


if __name__ == "__main__":
    unittest.main()
