"""SPEC: the updates section.

Architecture, decided with the team: no CMS and no build step. A writer sends a
.docx, it is approved as a document, and tools/docx2post.py converts it into a
page under eruptions/. Posts are one file each; eruptions.html, eruptions.xml and
sitemap.xml are all generated from those files by tools/rebuild_eruptions.py, so
they cannot drift.

What the tests hold to:

  * every post is a real page with its own chrome, metadata and permalink,
    because the whole point is sending a sponsor one specific post,
  * every post carries the four things the team agreed each one must have:
    photos, a numbers band, a spend line, a thanks, and a what's next,
  * the index, the chips and the feed always match the files on disk.
"""

import datetime
import email.utils
import glob
import os
import re
import subprocess
import unittest
import xml.etree.ElementTree as ET

import sitelib as S

INDEX = "eruptions.html"
FEED = "eruptions.xml"
TAGS = {"build", "outreach", "competition", "funding"}
REBUILD = os.path.join(S.ROOT, "tools", "rebuild_eruptions.py")


def post_files():
    return sorted(glob.glob(os.path.join(S.ROOT, "eruptions", "*.html")))


def post_pages():
    return [S.Page.load(os.path.relpath(p, S.ROOT)) for p in post_files()]


def post_article(page):
    return page.find("article", cls="post")


class SpecEruptionsExist(unittest.TestCase):
    def test_index_is_built(self):
        self.assertTrue(S.built(INDEX), f"{INDEX} has not been built yet")

    def test_feed_is_built(self):
        self.assertTrue(S.built(FEED), f"{FEED} has not been built yet")

    def test_at_least_one_post(self):
        self.assertTrue(post_files(), "there are no posts in eruptions/")

    def test_converter_and_rebuilder_exist(self):
        """The publishing route is a tool, not a hand-edit."""
        for tool in ("tools/docx2post.py", "tools/rebuild_eruptions.py"):
            with self.subTest(tool=tool):
                self.assertTrue(os.path.exists(os.path.join(S.ROOT, tool)))


@unittest.skipUnless(post_files(), "no posts yet")
class SpecPostPages(unittest.TestCase):
    def test_each_post_is_one_article_with_a_permalink(self):
        for page in post_pages():
            with self.subTest(post=page.name):
                article = post_article(page)
                self.assertIsNotNone(article, "no <article class=post>")
                slug = os.path.splitext(os.path.basename(page.name))[0]
                self.assertEqual(
                    article.get("id"), slug, "post id does not match its filename"
                )

    def test_each_post_is_dated(self):
        for page in post_pages():
            with self.subTest(post=page.name):
                stamp = post_article(page).find("time")
                self.assertIsNotNone(stamp, "post has no <time>")
                datetime.date.fromisoformat(stamp.get("datetime"))

    def test_each_post_has_a_title_and_a_byline(self):
        for page in post_pages():
            with self.subTest(post=page.name):
                self.assertEqual(
                    len(page.find_all("h1")), 1, "a post needs exactly one h1"
                )
                byline = page.find("p", cls="post-by")
                self.assertIsNotNone(byline, "post has no byline")
                self.assertTrue(byline.stripped_text())

    def test_each_post_is_tagged(self):
        for page in post_pages():
            with self.subTest(post=page.name):
                self.assertIn(post_article(page).get("data-tag"), TAGS)

    def test_each_post_carries_the_agreed_sections(self):
        """Photos, numbers, spend, thanks and what's next were agreed as
        required in every post. Enforcing it here is what stops post seven
        quietly becoming three paragraphs."""
        for page in post_pages():
            article = post_article(page)
            with self.subTest(post=page.name):
                self.assertTrue(
                    article.find_all("figure", cls="post-figure"),
                    "post has no photos",
                )
                band = article.find("section", cls="stats")
                self.assertIsNotNone(band, "post has no numbers band")
                self.assertGreaterEqual(len(band.find_all("div", cls="stat")), 2)
                for panel in ("post-spend", "post-thanks", "post-next"):
                    self.assertIsNotNone(
                        article.find(cls=panel), f"post has no {panel} section"
                    )

    def test_spend_section_points_at_the_open_books(self):
        for page in post_pages():
            spend = post_article(page).find(cls="post-spend")
            hrefs = [S.normalise_href(a.get("href")) for a in spend.find_all("a")]
            with self.subTest(post=page.name):
                self.assertIn(
                    "sponsors.html", hrefs, "the spend section does not link the books"
                )

    def test_each_post_is_shareable(self):
        for page in post_pages():
            slug = os.path.splitext(os.path.basename(page.name))[0]
            expected = f"{S.SITE_ORIGIN}/eruptions/{slug}.html"
            with self.subTest(post=page.name):
                self.assertEqual(page.link_rel("canonical"), expected)
                self.assertEqual(page.prop("og:url"), expected)
                self.assertEqual(page.prop("og:type"), "article")
                self.assertTrue(page.prop("og:image"))
                self.assertTrue(page.meta("description"))

    def test_each_post_advertises_the_feed(self):
        for page in post_pages():
            types = {
                link.get("type")
                for link in page.find_all("link")
                if "alternate" in (link.get("rel") or "")
            }
            with self.subTest(post=page.name):
                self.assertIn("application/rss+xml", types)

    def test_each_post_links_back_to_the_index(self):
        for page in post_pages():
            hrefs = [S.normalise_href(a.get("href")) for a in page.find_all("a")]
            with self.subTest(post=page.name):
                self.assertIn("eruptions.html", hrefs)


@unittest.skipUnless(S.built(INDEX), f"{INDEX} not built")
class SpecEruptionsIndex(unittest.TestCase):
    def rows(self):
        return S.Page.load(INDEX).find_all("div", cls="row-item")

    def index_rows(self):
        holder = S.Page.load(INDEX).find("div", cls="update-index")
        return holder.find_all("div", cls="row-item") if holder else []

    def test_headline(self):
        self.assertEqual(S.Page.load(INDEX).find("h1").stripped_text(), "Eruptions")

    def test_latest_post_is_featured(self):
        """The newest post gets a card of its own at the top of the page."""
        featured = S.Page.load(INDEX).find("article", cls="featured-post")
        self.assertIsNotNone(featured, "the latest post is not featured")
        newest = os.path.splitext(os.path.basename(post_files()[-1]))[0]
        dates = {
            os.path.splitext(os.path.basename(p))[0]:
                post_article(S.Page.load(os.path.relpath(p, S.ROOT)))
                .find("time").get("datetime")
            for p in post_files()
        }
        newest = max(dates, key=dates.get)
        hrefs = [a.get("href") for a in featured.find_all("a")]
        self.assertTrue(
            any(newest in (h or "") for h in hrefs),
            f"the featured card is not the newest post ({newest})",
        )
        self.assertTrue(featured.find("img"), "the featured card has no photo")
        self.assertTrue(featured.find("p").stripped_text(), "no excerpt shown")

    def test_previous_list_holds_every_post_but_the_featured_one(self):
        self.assertEqual(
            len(self.index_rows()),
            max(len(post_files()) - 1, 0),
            "the Previous Eruptions list and the files in eruptions/ have diverged",
        )

    def test_previous_section_is_labelled(self):
        headings = " ".join(
            b.stripped_text().lower()
            for b in S.Page.load(INDEX).find_all("div", cls="section-banner")
        )
        self.assertIn("latest eruption", headings)
        self.assertIn("previous eruptions", headings)

    def test_rows_link_real_posts_newest_first(self):
        hrefs = []
        for row in self.index_rows():
            link = row.find("a")
            self.assertIsNotNone(link, "index row links nowhere")
            href = link.get("href")
            hrefs.append(href)
            self.assertTrue(
                os.path.exists(S.local_target(href)), f"{href} does not resolve"
            )
        slugs = [os.path.splitext(os.path.basename(h))[0] for h in hrefs]
        dates = []
        for slug in slugs:
            page = S.Page.load(f"eruptions/{slug}.html")
            dates.append(post_article(page).find("time").get("datetime"))
        self.assertEqual(dates, sorted(dates, reverse=True), "posts are out of order")

    def test_rows_are_labelled_and_summarised(self):
        for row in self.index_rows():
            with self.subTest(row=row.line):
                self.assertTrue(row.find("span", cls="row-label").stripped_text())
                self.assertTrue(row.find("p").stripped_text())

    def test_chips_cover_every_tag_in_use(self):
        chips = S.Page.load(INDEX).find_all("button", cls="chip")
        values = {c.get("data-filter") for c in chips}
        self.assertIn("all", values, "there is no All chip")
        for page in post_pages():
            tag = post_article(page).get("data-tag")
            with self.subTest(tag=tag):
                self.assertIn(tag, values, f"no chip for the {tag} tag")

    def test_index_explains_the_cadence(self):
        text = S.Page.load(INDEX).root.stripped_text().lower()
        self.assertIn("milestone", text, "the page never says how often it updates")

    def test_feed_is_discoverable(self):
        """The visible subscribe panel was dropped, so the feed has to stay
        discoverable from the head for readers and crawlers."""
        page = S.Page.load(INDEX)
        alternates = [
            link for link in page.find_all("link")
            if "alternate" in (link.get("rel") or "")
        ]
        self.assertTrue(
            any(link.get("type") == "application/rss+xml" for link in alternates),
            "eruptions.html no longer advertises its feed",
        )


@unittest.skipUnless(S.built(FEED), f"{FEED} not built")
class SpecEruptionsFeed(unittest.TestCase):
    def setUp(self):
        self.channel = ET.parse(os.path.join(S.ROOT, FEED)).getroot().find("channel")

    def test_channel_metadata(self):
        for tag in ("title", "link", "description"):
            with self.subTest(tag=tag):
                self.assertTrue((self.channel.findtext(tag) or "").strip())

    def test_one_item_per_post(self):
        self.assertEqual(len(self.channel.findall("item")), len(post_files()))

    def test_items_link_the_post_pages(self):
        links = [i.findtext("link") for i in self.channel.findall("item")]
        for path in post_files():
            slug = os.path.splitext(os.path.basename(path))[0]
            url = f"{S.SITE_ORIGIN}/eruptions/{slug}.html"
            with self.subTest(post=slug):
                self.assertIn(url, links)

    def test_pubdates_parse(self):
        for item in self.channel.findall("item"):
            with self.subTest(item=item.findtext("title")):
                parsed = email.utils.parsedate_to_datetime(item.findtext("pubDate"))
                self.assertIsInstance(parsed, datetime.datetime)


class SpecGeneratedFilesAreCurrent(unittest.TestCase):
    def test_index_feed_and_sitemap_are_regenerated(self):
        """The standing alarm: add a post and forget to rebuild, and this
        fails naming the stale file."""
        result = subprocess.run(
            ["python3", REBUILD, "--check"],
            capture_output=True, text=True, cwd=S.ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
