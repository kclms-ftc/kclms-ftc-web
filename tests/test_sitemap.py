"""sitemap.xml and robots.txt stay in step with the pages that exist."""

import datetime
import os
import unittest
import xml.etree.ElementTree as ET

import sitelib as S

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
VALID_FREQ = {
    "always", "hourly", "daily", "weekly", "monthly", "yearly", "never",
}


def sitemap_entries():
    tree = ET.parse(os.path.join(S.ROOT, "sitemap.xml"))
    entries = []
    for url in tree.getroot().findall("sm:url", NS):
        entries.append(
            {
                "loc": url.findtext("sm:loc", namespaces=NS),
                "lastmod": url.findtext("sm:lastmod", namespaces=NS),
                "changefreq": url.findtext("sm:changefreq", namespaces=NS),
                "priority": url.findtext("sm:priority", namespaces=NS),
            }
        )
    return entries


def loc_to_page(loc):
    path = loc[len(S.SITE_ORIGIN) :].lstrip("/")
    return path or "index.html"


class TestSitemap(unittest.TestCase):
    def setUp(self):
        self.entries = sitemap_entries()

    def test_parses_and_is_not_empty(self):
        self.assertTrue(self.entries, "sitemap.xml lists no URLs")

    def test_locs_are_absolute_and_unique(self):
        locs = [e["loc"] for e in self.entries]
        self.assertEqual(len(locs), len(set(locs)), "sitemap has duplicate URLs")
        for loc in locs:
            with self.subTest(loc=loc):
                self.assertTrue(loc.startswith(S.SITE_ORIGIN), f"{loc} is not absolute")

    def test_every_listed_page_exists(self):
        for entry in self.entries:
            page = loc_to_page(entry["loc"])
            with self.subTest(loc=entry["loc"]):
                self.assertTrue(S.built(page), f"sitemap lists missing page {page}")

    def test_every_built_page_is_listed(self):
        listed = {loc_to_page(e["loc"]) for e in self.entries}
        for name in S.BUILT_PAGES:
            with self.subTest(page=name):
                self.assertIn(
                    name, listed, f"{name} exists but is not in sitemap.xml"
                )

    def test_no_noindex_page_is_listed(self):
        listed = {loc_to_page(e["loc"]) for e in self.entries}
        for name in list(S.REDIRECT_STUBS) + S.UNLISTED_PAGES:
            with self.subTest(page=name):
                self.assertNotIn(name, listed, f"{name} is noindex but is in sitemap")

    def test_lastmod_is_a_sane_date(self):
        today = datetime.date.today()
        for entry in self.entries:
            with self.subTest(loc=entry["loc"]):
                self.assertIsNotNone(entry["lastmod"], "entry has no lastmod")
                stamp = datetime.date.fromisoformat(entry["lastmod"])
                self.assertLessEqual(
                    stamp, today, f"{entry['loc']} lastmod is in the future"
                )

    def test_changefreq_and_priority_valid(self):
        for entry in self.entries:
            with self.subTest(loc=entry["loc"]):
                self.assertIn(entry["changefreq"], VALID_FREQ)
                self.assertTrue(0.0 <= float(entry["priority"]) <= 1.0)

    def test_robots_points_at_the_sitemap(self):
        with open(os.path.join(S.ROOT, "robots.txt"), encoding="utf-8") as handle:
            robots = handle.read()
        self.assertIn(f"{S.SITE_ORIGIN}/sitemap.xml", robots)


if __name__ == "__main__":
    unittest.main()
