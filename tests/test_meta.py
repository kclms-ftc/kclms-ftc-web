"""SEO and social metadata. Sponsors find this site through search and through
links pasted into chats, so the cards have to be right on every page."""

import os
import unittest

import sitelib as S


def canonical_for(name):
    if name == "index.html":
        return f"{S.SITE_ORIGIN}/"
    return f"{S.SITE_ORIGIN}/{name}"


class TestMeta(unittest.TestCase):
    def test_title_present_and_branded(self):
        for name in S.BUILT_PAGES:
            page = S.Page.load(name)
            with self.subTest(page=name):
                self.assertTrue(page.title, f"{name} has no <title>")
                self.assertIn(
                    "Volcanix", page.title, f"{name} title is not branded"
                )
                self.assertLessEqual(
                    len(page.title), 70, f"{name} title will be truncated in search"
                )

    def test_description_present_and_sized(self):
        for name in S.BUILT_PAGES:
            page = S.Page.load(name)
            description = page.meta("description")
            with self.subTest(page=name):
                self.assertTrue(description, f"{name} has no meta description")
                self.assertGreaterEqual(
                    len(description), 50, f"{name} description is too thin"
                )

    def test_canonical_matches_filename(self):
        for name in S.BUILT_PAGES:
            page = S.Page.load(name)
            with self.subTest(page=name):
                self.assertEqual(
                    page.link_rel("canonical"),
                    canonical_for(name),
                    f"{name} canonical is wrong",
                )

    def test_open_graph_complete(self):
        required = [
            "og:type",
            "og:url",
            "og:title",
            "og:description",
            "og:image",
            "og:site_name",
        ]
        for name in S.BUILT_PAGES:
            page = S.Page.load(name)
            for prop in required:
                with self.subTest(page=name, prop=prop):
                    self.assertTrue(page.prop(prop), f"{name} missing {prop}")

    def test_og_url_matches_canonical(self):
        for name in S.BUILT_PAGES:
            page = S.Page.load(name)
            with self.subTest(page=name):
                self.assertEqual(page.prop("og:url"), canonical_for(name))

    def test_og_image_exists_on_disk(self):
        for name in S.BUILT_PAGES:
            page = S.Page.load(name)
            image = page.prop("og:image") or ""
            with self.subTest(page=name, image=image):
                self.assertTrue(
                    image.startswith(S.SITE_ORIGIN),
                    f"{name} og:image must be an absolute URL",
                )
                relative = image[len(S.SITE_ORIGIN) :].lstrip("/")
                self.assertTrue(
                    os.path.exists(os.path.join(S.ROOT, relative)),
                    f"{name} og:image {relative} is not in the repo",
                )

    def test_twitter_card(self):
        for name in S.BUILT_PAGES:
            page = S.Page.load(name)
            with self.subTest(page=name):
                self.assertEqual(page.meta("twitter:card"), "summary_large_image")
                self.assertTrue(page.meta("twitter:image"), f"{name} has no twitter:image")

    def test_indexable(self):
        for name in S.BUILT_PAGES:
            page = S.Page.load(name)
            with self.subTest(page=name):
                self.assertIn("index", (page.meta("robots") or "index, follow"))

    def test_json_ld_is_valid_json(self):
        for name in S.BUILT_PAGES:
            with self.subTest(page=name):
                blocks = S.Page.load(name).json_ld()  # raises on malformed JSON
                for block in blocks:
                    self.assertEqual(
                        block.get("@context"),
                        "https://schema.org",
                        f"{name} JSON-LD is missing the schema.org context",
                    )

    def test_interior_pages_have_breadcrumbs(self):
        """Breadcrumbs are what put the section name under the search result."""
        for name in S.BUILT_PAGES:
            if name == "index.html":
                continue
            page = S.Page.load(name)
            types = []
            for block in page.json_ld():
                for entry in block.get("@graph", [block]):
                    types.append(entry.get("@type"))
            with self.subTest(page=name):
                self.assertIn(
                    "BreadcrumbList", types, f"{name} has no BreadcrumbList"
                )


if __name__ == "__main__":
    unittest.main()
