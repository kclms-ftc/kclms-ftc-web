"""SPEC: the nav restructure.

Nav goes to Home / Team / Updates / Resources / Sponsors -- five slots, so it
still fits on a phone once Updates lands. Events is reachable from Updates, the
footer and the homepage rather than a sixth button.

The nav block is copied into every page by hand today, which the issue-5 notes
already flag as costing six file edits per change. These tests pin the block so
the copies cannot drift, and require the sync script that does the copying.
"""

import os
import re
import unittest

import sitelib as S

SYNC_SCRIPT = os.path.join(S.ROOT, "tools", "sync-nav.sh")
MARKER_START = "NAV:START"
MARKER_END = "NAV:END"


class SpecNav(unittest.TestCase):
    def test_nav_matches_the_canonical_order(self):
        for name in S.BUILT_PAGES:
            with self.subTest(page=name):
                self.assertEqual(
                    S.Page.load(name).nav_items(),
                    S.NAV,
                    f"{name} nav does not match the canonical nav",
                )

    def test_404_nav_matches_too(self):
        """404 writes root-absolute hrefs on purpose; normalised it is the same
        nav as everywhere else."""
        self.assertEqual(S.Page.load("404.html").nav_items(), S.NAV)

    def test_nav_is_five_items(self):
        self.assertEqual(
            len(S.NAV), 5, "a sixth nav button wraps the slab on small screens"
        )

    def test_footer_explore_covers_every_page(self):
        for name in S.BUILT_PAGES:
            with self.subTest(page=name):
                self.assertEqual(
                    S.Page.load(name).footer_explore(),
                    S.FOOTER_EXPLORE,
                    f"{name} footer Explore does not match the canonical list",
                )

    def test_events_is_reachable_without_a_nav_slot(self):
        targets = [t for _, t in S.FOOTER_EXPLORE]
        self.assertIn("events.html", targets, "Events must be linked from the footer")
        self.assertNotIn(
            "events.html", [t for _, t in S.NAV], "Events should not take a nav slot"
        )

    def test_nav_markers_present(self):
        for name in S.BUILT_PAGES:
            source = S.Page.load(name).source
            with self.subTest(page=name):
                self.assertIn(MARKER_START, source, f"{name} has no {MARKER_START}")
                self.assertIn(MARKER_END, source, f"{name} has no {MARKER_END}")

    def test_marked_nav_block_is_identical_across_pages(self):
        pattern = re.compile(
            re.escape(MARKER_START) + r"(.*?)" + re.escape(MARKER_END), re.S
        )
        blocks = {}
        for name in S.BUILT_PAGES:
            match = pattern.search(S.Page.load(name).source)
            self.assertIsNotNone(match, f"{name} has no marked nav block")
            blocks[name] = match.group(1)
        reference = blocks[S.BUILT_PAGES[0]]
        for name, block in blocks.items():
            with self.subTest(page=name):
                self.assertEqual(
                    block, reference, f"{name} nav block differs byte-for-byte"
                )

    def test_sync_script_exists_and_runs(self):
        self.assertTrue(
            os.path.exists(SYNC_SCRIPT), "tools/sync-nav.sh is missing"
        )
        self.assertTrue(
            os.access(SYNC_SCRIPT, os.X_OK), "tools/sync-nav.sh is not executable"
        )

    def test_sitemap_covers_the_new_pages(self):
        with open(os.path.join(S.ROOT, "sitemap.xml"), encoding="utf-8") as handle:
            sitemap = handle.read()
        for page in ("resources.html", "updates.html", "events.html"):
            with self.subTest(page=page):
                self.assertIn(page, sitemap, f"{page} is missing from sitemap.xml")


if __name__ == "__main__":
    unittest.main()
