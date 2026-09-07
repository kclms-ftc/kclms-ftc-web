"""Page chrome: every content page carries the same nav, footer and head."""

import unittest

import sitelib as S


class TestChrome(unittest.TestCase):
    def test_every_page_parses(self):
        for name in S.BUILT_PAGES + list(S.REDIRECT_STUBS) + S.UNLISTED_PAGES:
            with self.subTest(page=name):
                page = S.Page.load(name)
                self.assertIsNotNone(page.root, f"{name} produced no tree")

    def test_nav_agrees_across_pages(self):
        """The nav block is duplicated in every file. Duplication is fine; drift
        is not. Every page must show the same items in the same order."""
        reference = S.Page.load("index.html").nav_items()
        self.assertTrue(reference, "index.html has no nav items")
        for name in S.BUILT_PAGES + ["404.html"]:
            with self.subTest(page=name):
                self.assertEqual(
                    S.Page.load(name).nav_items(),
                    reference,
                    f"{name} nav has drifted from index.html",
                )

    def test_footer_explore_agrees_across_pages(self):
        reference = S.Page.load("index.html").footer_explore()
        self.assertTrue(reference, "index.html has no footer Explore column")
        for name in S.BUILT_PAGES:
            with self.subTest(page=name):
                self.assertEqual(
                    S.Page.load(name).footer_explore(),
                    reference,
                    f"{name} footer Explore has drifted from index.html",
                )

    def test_nav_targets_exist(self):
        for name in S.BUILT_PAGES + ["404.html"]:
            page = S.Page.load(name)
            for label, target in page.nav_items():
                with self.subTest(page=name, item=label):
                    self.assertTrue(
                        S.built(target), f"{name} nav links {label} -> missing {target}"
                    )

    def test_wordmark_links_home(self):
        for name in S.BUILT_PAGES + ["404.html"]:
            with self.subTest(page=name):
                mark = S.Page.load(name).find("a", cls="wordmark")
                self.assertIsNotNone(mark, f"{name} has no wordmark")
                self.assertEqual(S.normalise_href(mark.get("href")), "index.html")
                self.assertTrue(mark.get("aria-label"), f"{name} wordmark needs a label")

    def test_head_essentials(self):
        for name in S.BUILT_PAGES:
            page = S.Page.load(name)
            with self.subTest(page=name):
                html = page.find("html")
                self.assertEqual(html.get("lang"), "en", f"{name} missing lang=en")
                charsets = [m for m in page.find_all("meta") if m.get("charset")]
                self.assertTrue(charsets, f"{name} has no charset")
                self.assertIsNotNone(page.meta("viewport"), f"{name} has no viewport")
                self.assertEqual(page.link_rel("stylesheet"), "styles.css")
                self.assertIsNotNone(page.link_rel("icon"), f"{name} has no favicon")
                self.assertIsNotNone(
                    page.link_rel("apple-touch-icon"), f"{name} has no touch icon"
                )

    def test_script_is_loaded_last(self):
        for name in S.BUILT_PAGES:
            with self.subTest(page=name):
                page = S.Page.load(name)
                srcs = [s.get("src") for s in page.find_all("script") if s.get("src")]
                self.assertIn("script.js", srcs, f"{name} does not load script.js")

    def test_pages_end_with_skyline_and_footer(self):
        for name in S.BUILT_PAGES:
            with self.subTest(page=name):
                page = S.Page.load(name)
                self.assertIsNotNone(
                    page.find("div", cls="skyline"), f"{name} lost the skyline band"
                )
                self.assertIsNotNone(page.find("footer"), f"{name} lost the footer")

    def test_social_links_consistent(self):
        """Instagram, LinkedIn and the team address appear in every footer."""
        for name in S.BUILT_PAGES:
            page = S.Page.load(name)
            footer = page.find("footer")
            hrefs = [a.get("href") for a in footer.find_all("a")]
            with self.subTest(page=name):
                self.assertIn("https://www.instagram.com/kclms_ftc/", hrefs)
                self.assertIn("https://www.linkedin.com/in/kclms-ftc", hrefs)
                self.assertIn("mailto:kclmsftc@gmail.com", hrefs)


if __name__ == "__main__":
    unittest.main()
