"""The retired URLs stay alive as meta-refresh stubs."""

import unittest

import sitelib as S


class TestRedirects(unittest.TestCase):
    def test_stub_exists_and_points_at_a_real_page(self):
        for stub, target in S.REDIRECT_STUBS.items():
            with self.subTest(stub=stub):
                self.assertTrue(S.built(stub), f"{stub} is missing")
                self.assertTrue(S.built(target), f"{stub} points at missing {target}")

    def test_stub_refreshes_immediately(self):
        for stub, target in S.REDIRECT_STUBS.items():
            page = S.Page.load(stub)
            refresh = None
            for meta in page.find_all("meta"):
                if (meta.get("http-equiv") or "").lower() == "refresh":
                    refresh = meta.get("content")
            with self.subTest(stub=stub):
                self.assertIsNotNone(refresh, f"{stub} has no refresh")
                delay, _, url = refresh.partition(";")
                self.assertEqual(delay.strip(), "0", f"{stub} does not redirect at once")
                self.assertEqual(
                    S.normalise_href(url.strip().removeprefix("url=").strip()),
                    target,
                    f"{stub} refreshes to the wrong page",
                )

    def test_stub_is_noindex_and_canonical(self):
        for stub, target in S.REDIRECT_STUBS.items():
            page = S.Page.load(stub)
            with self.subTest(stub=stub):
                self.assertIn("noindex", page.meta("robots") or "")
                canonical = page.link_rel("canonical")
                self.assertIsNotNone(canonical, f"{stub} has no canonical")
                self.assertEqual(S.normalise_href(canonical), target)

    def test_stub_has_a_manual_link_out(self):
        """A visitor with meta-refresh disabled must not hit a dead end."""
        for stub, target in S.REDIRECT_STUBS.items():
            page = S.Page.load(stub)
            targets = [S.normalise_href(a.get("href")) for a in page.find_all("a")]
            with self.subTest(stub=stub):
                self.assertIn(target, targets, f"{stub} has no manual link to {target}")

    def test_404_is_noindex_but_followable(self):
        page = S.Page.load("404.html")
        robots = page.meta("robots") or ""
        self.assertIn("noindex", robots)
        self.assertIn("follow", robots)


if __name__ == "__main__":
    unittest.main()
