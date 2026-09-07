"""The shared nav/footer stay in sync, and headings form a real outline.

Covers the Phase 1 and Phase 2 work: chrome is now generated from
tools/nav.html and tools/footer.html by tools/sync-nav.sh, and every page's
headings descend one level at a time so the document outline is usable by a
screen reader and legible to search engines.
"""

import glob
import os
import subprocess
import unittest

import sitelib as S

SYNC = os.path.join(S.ROOT, "tools", "sync-nav.sh")
CHROME_PAGES = S.BUILT_PAGES + ["404.html"]
ALL_HTML = sorted(
    os.path.basename(p) for p in glob.glob(os.path.join(S.ROOT, "*.html"))
)


class TestChromeSync(unittest.TestCase):
    def test_sync_script_is_executable(self):
        self.assertTrue(os.path.exists(SYNC), "tools/sync-nav.sh is missing")
        self.assertTrue(os.access(SYNC, os.X_OK), "tools/sync-nav.sh is not executable")

    def test_partials_exist(self):
        for partial in ("tools/nav.html", "tools/footer.html"):
            with self.subTest(partial=partial):
                self.assertTrue(os.path.exists(os.path.join(S.ROOT, partial)))

    def test_no_page_has_drifted_from_the_partials(self):
        """The real guard: if anyone hand-edits a nav or footer in one page,
        this fails and names the file."""
        result = subprocess.run(
            [SYNC, "--check"], capture_output=True, text=True, cwd=S.ROOT
        )
        self.assertEqual(
            result.returncode, 0, f"chrome is out of sync:\n{result.stdout}"
        )

    def test_every_page_carries_both_markers(self):
        for name in CHROME_PAGES:
            source = S.Page.load(name).source
            for marker in ("NAV:START", "NAV:END", "FOOTER:START", "FOOTER:END"):
                with self.subTest(page=name, marker=marker):
                    self.assertIn(marker, source, f"{name} has no {marker}")

    def test_chrome_uses_root_absolute_links(self):
        """One identical block has to work on every page, 404 included, so the
        shared links cannot be relative."""
        for name in CHROME_PAGES:
            page = S.Page.load(name)
            nav = page.find("ul", cls="nav-links")
            for anchor in nav.find_all("a"):
                href = anchor.get("href")
                with self.subTest(page=name, href=href):
                    self.assertTrue(
                        href.startswith("/"), f"{name} nav link {href} is relative"
                    )

    def test_active_link_logic_matches_the_markup(self):
        """script.js compares basenames now; if that regressed to a raw href
        comparison the active state would silently stop working."""
        js = S.read_js()
        self.assertNotIn(
            "link.getAttribute('href') === current",
            js,
            "the nav active-state check is back to comparing raw hrefs",
        )


class TestHeadingOutline(unittest.TestCase):
    def headings_outside_footer(self, page):
        out = []
        for node in page.find_all():
            if node.tag not in ("h1", "h2", "h3", "h4"):
                continue
            if any(a.tag == "footer" for a in node.ancestors()):
                continue
            out.append((int(node.tag[1]), node.line, node.stripped_text()))
        return out

    def test_headings_never_skip_a_level(self):
        for name in ALL_HTML:
            if name in S.REDIRECT_STUBS or name.startswith("google"):
                continue
            page = S.Page.load(name)
            previous = 0
            for level, line, text in self.headings_outside_footer(page):
                with self.subTest(page=name, line=line, heading=text):
                    if previous:
                        self.assertLessEqual(
                            level,
                            previous + 1,
                            f"{name}:{line} jumps h{previous} to h{level}",
                        )
                    previous = level

    def test_first_heading_is_the_h1(self):
        for name in ALL_HTML:
            if name in S.REDIRECT_STUBS or name.startswith("google"):
                continue
            page = S.Page.load(name)
            levels = [level for level, _, _ in self.headings_outside_footer(page)]
            if not levels:
                continue
            with self.subTest(page=name):
                self.assertEqual(levels[0], 1, f"{name} does not open with its h1")


class TestPortfolioContent(unittest.TestCase):
    """portfolio.html used to be an h1 and a bare 15MB PDF: nothing for search
    to rank on a priority-0.9 page, and a 15MB download on open."""

    def test_portfolio_has_readable_content(self):
        page = S.Page.load("portfolio.html")
        body = " ".join(
            p.stripped_text()
            for p in page.find_all("p")
            if not any(a.tag == "footer" for a in p.ancestors())
        )
        self.assertGreater(
            len(body.split()), 200, "portfolio.html still has almost no indexable text"
        )

    def test_portfolio_has_sections(self):
        page = S.Page.load("portfolio.html")
        self.assertGreaterEqual(
            len(page.find_all("h2")), 3, "portfolio.html has no section structure"
        )

    def test_heavy_pdf_is_behind_a_closed_details(self):
        page = S.Page.load("portfolio.html")
        for obj in page.find_all("object"):
            with self.subTest(data=obj.get("data")):
                holders = [a for a in obj.ancestors() if a.tag == "details"]
                self.assertTrue(
                    holders, "the portfolio PDF still loads on page open"
                )
                self.assertIsNone(
                    holders[0].get("open"), "the PDF embed opens by default"
                )

    def test_details_has_a_summary(self):
        for details in S.Page.load("portfolio.html").find_all("details"):
            with self.subTest(line=details.line):
                summary = details.find("summary")
                self.assertIsNotNone(summary)
                self.assertTrue(summary.stripped_text())


if __name__ == "__main__":
    unittest.main()
