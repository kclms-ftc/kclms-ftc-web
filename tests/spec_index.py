"""SPEC: the homepage picks up the two new pages.

A sponsor who lands cold on the homepage should see that the team is active
this month without hunting for it, and should be able to reach the log and the
calendar from there.
"""

import re
import unittest

import sitelib as S

PAGE = "index.html"


def page():
    return S.Page.load(PAGE)


class SpecHomepageTeasers(unittest.TestCase):
    def test_latest_update_teaser_exists(self):
        block = page().find(cls="latest-update")
        self.assertIsNotNone(
            block, "homepage does not surface the most recent update"
        )

    def test_teaser_deep_links_a_specific_post(self):
        block = page().find(cls="latest-update")
        if block is None:
            self.skipTest("no teaser block yet")
        hrefs = [a.get("href") or "" for a in block.find_all("a")]
        self.assertTrue(
            any(re.search(r"updates/[a-z0-9-]+\.html$", h) for h in hrefs),
            "the teaser links the section but not a specific post",
        )

    def test_teaser_is_dated(self):
        block = page().find(cls="latest-update")
        if block is None:
            self.skipTest("no teaser block yet")
        stamp = block.find("time")
        self.assertIsNotNone(stamp, "the teaser does not show when it was written")
        self.assertRegex(stamp.get("datetime") or "", r"^\d{4}-\d{2}")

    def test_next_event_is_surfaced(self):
        block = page().find(cls="next-event")
        self.assertIsNotNone(block, "homepage does not surface the next event")
        hrefs = [a.get("href") or "" for a in block.find_all("a")]
        self.assertTrue(
            any("events.html" in h for h in hrefs), "next-event does not link events"
        )

    def test_homepage_links_both_new_pages(self):
        hrefs = [S.normalise_href(a.get("href")) for a in page().find_all("a")]
        for target in ("updates.html", "events.html"):
            with self.subTest(target=target):
                self.assertIn(target, hrefs, f"homepage never links {target}")


if __name__ == "__main__":
    unittest.main()
