"""Accessibility and layout-stability basics."""

import glob
import os
import unittest

import sitelib as S

ALL_HTML = sorted(
    os.path.basename(p) for p in glob.glob(os.path.join(S.ROOT, "*.html"))
)

# Icon-only anchors need a label; these carry visible text instead.
def has_accessible_name(anchor):
    if anchor.stripped_text():
        return True
    if anchor.get("aria-label") or anchor.get("title"):
        return True
    for img in anchor.find_all("img"):
        if img.get("alt"):
            return True
    return False


class TestAccessibility(unittest.TestCase):
    def test_images_have_alt(self):
        for name in ALL_HTML:
            page = S.Page.load(name)
            for img in page.find_all("img"):
                with self.subTest(page=name, line=img.line, src=img.get("src")):
                    self.assertIsNotNone(
                        img.get("alt"),
                        f"{name}:{img.line} <img> has no alt attribute",
                    )

    def test_decorative_images_are_hidden(self):
        """An empty alt is only correct when the image is also hidden from the
        accessibility tree."""
        for name in ALL_HTML:
            page = S.Page.load(name)
            for img in page.find_all("img"):
                if img.get("alt") != "":
                    continue
                with self.subTest(page=name, line=img.line):
                    self.assertEqual(
                        img.get("aria-hidden"),
                        "true",
                        f"{name}:{img.line} empty alt without aria-hidden",
                    )

    def test_images_declare_dimensions(self):
        """width/height on every image is what keeps the poster layout from
        jumping while it loads."""
        for name in ALL_HTML:
            page = S.Page.load(name)
            for img in page.find_all("img"):
                with self.subTest(page=name, line=img.line, src=img.get("src")):
                    self.assertTrue(
                        img.get("width") and img.get("height"),
                        f"{name}:{img.line} <img> has no width/height",
                    )

    def test_below_fold_images_are_lazy(self):
        for name in ALL_HTML:
            page = S.Page.load(name)
            for img in page.find_all("img"):
                if img.get("fetchpriority") == "high":
                    continue
                with self.subTest(page=name, line=img.line, src=img.get("src")):
                    self.assertEqual(
                        img.get("loading"),
                        "lazy",
                        f"{name}:{img.line} is neither preloaded nor lazy",
                    )

    def test_links_have_accessible_names(self):
        for name in ALL_HTML:
            page = S.Page.load(name)
            for anchor in page.find_all("a"):
                with self.subTest(page=name, line=anchor.line):
                    self.assertTrue(
                        has_accessible_name(anchor),
                        f"{name}:{anchor.line} link has no accessible name",
                    )

    def test_exactly_one_h1(self):
        for name in ALL_HTML:
            if name in S.REDIRECT_STUBS or name.startswith("google"):
                continue
            page = S.Page.load(name)
            with self.subTest(page=name):
                self.assertEqual(
                    len(page.find_all("h1")), 1, f"{name} must have exactly one h1"
                )

    def test_svgs_are_hidden_or_labelled(self):
        for name in ALL_HTML:
            page = S.Page.load(name)
            for svg in page.find_all("svg"):
                with self.subTest(page=name, line=svg.line):
                    labelled = svg.get("aria-hidden") == "true" or svg.get("aria-label")
                    self.assertTrue(
                        labelled, f"{name}:{svg.line} svg is neither hidden nor labelled"
                    )


if __name__ == "__main__":
    unittest.main()
