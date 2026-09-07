"""SPEC: updates.html, the monthly team log.

This is the page sponsors and mentors get pointed at instead of a meeting, and
it is written by rotating students. So the contract is about two things:

  1. a sponsor can deep-link one month (every post is anchored),
  2. a student can add next month's post without breaking anything (the index,
     the tags and the feed all have to stay in step with the posts).

Expected post markup:

    <article class="post" id="2025-09" data-tag="build">
      <p class="post-date"><time datetime="2025-09">September 2025</time></p>
      <h3>Title of the update</h3>
      <p class="post-by">Ansh Gupta &middot; Build Lead</p>
      ...
    </article>
"""

import datetime
import email.utils
import os
import re
import unittest
import xml.etree.ElementTree as ET

import sitelib as S

PAGE = "updates.html"
FEED = "updates.xml"
ID_RE = re.compile(r"^\d{4}-\d{2}$")
TAGS = {"build", "outreach", "competition", "funding"}
TEMPLATE_MARKER = "COPY FROM HERE"


class SpecUpdatesExist(unittest.TestCase):
    """The one unskipped check: until these land, everything below is dormant.
    Keeps the red signal to two lines instead of forty errors."""

    def test_page_is_built(self):
        self.assertTrue(S.built(PAGE), f"{PAGE} has not been built yet")

    def test_feed_is_built(self):
        self.assertTrue(S.built(FEED), f"{FEED} has not been built yet")


def page():
    return S.Page.load(PAGE)


def posts():
    return page().find_all("article", cls="post")


@unittest.skipUnless(S.built(PAGE), f"{PAGE} not built yet")
class SpecUpdatesPage(unittest.TestCase):
    def test_headline(self):
        heading = page().find("h1")
        self.assertEqual(heading.stripped_text(), "Updates")

    def test_has_posts(self):
        self.assertGreaterEqual(len(posts()), 1, "updates.html has no posts")

    def test_post_ids_are_year_month_and_unique(self):
        ids = [p.get("id") for p in posts()]
        for post_id in ids:
            with self.subTest(post=post_id):
                self.assertIsNotNone(post_id, "a post has no id to link to")
                self.assertRegex(
                    post_id, ID_RE, f"post id {post_id} is not YYYY-MM"
                )
        self.assertEqual(len(ids), len(set(ids)), "duplicate post ids")

    def test_posts_are_newest_first(self):
        ids = [p.get("id") for p in posts()]
        self.assertEqual(ids, sorted(ids, reverse=True), "posts are out of order")

    def test_each_post_has_a_dated_time_element(self):
        for post in posts():
            with self.subTest(post=post.get("id")):
                stamp = post.find("time")
                self.assertIsNotNone(stamp, "post has no <time>")
                self.assertEqual(
                    stamp.get("datetime"),
                    post.get("id"),
                    "post <time> disagrees with the post id",
                )

    def test_each_post_has_a_title_and_a_byline(self):
        for post in posts():
            with self.subTest(post=post.get("id")):
                self.assertIsNotNone(post.find("h3"), "post has no h3 title")
                byline = post.find("p", cls="post-by")
                self.assertIsNotNone(byline, "post has no byline")
                self.assertTrue(
                    byline.stripped_text(), "post byline is empty"
                )

    def test_each_post_is_tagged(self):
        for post in posts():
            tag = post.get("data-tag")
            with self.subTest(post=post.get("id")):
                self.assertIn(tag, TAGS, f"unknown tag {tag!r}")

    def test_index_lists_every_post_in_order(self):
        rows = page().find_all("div", cls="row-item")
        self.assertEqual(
            len(rows), len(posts()), "the index and the posts have diverged"
        )
        anchors = []
        for row in rows:
            link = row.find("a")
            self.assertIsNotNone(link, "an index row does not link anywhere")
            anchors.append(link.get("href"))
        self.assertEqual(anchors, [f"#{p.get('id')}" for p in posts()])

    def test_index_rows_are_labelled_and_summarised(self):
        for row in page().find_all("div", cls="row-item"):
            with self.subTest(row=row.line):
                label = row.find("span", cls="row-label")
                self.assertIsNotNone(label, "index row has no date label")
                self.assertTrue(label.stripped_text())
                summary = row.find("p")
                self.assertIsNotNone(summary, "index row has no summary")
                self.assertTrue(summary.stripped_text())

    def test_filter_chips_cover_the_tags_in_use(self):
        chips = page().find_all("button", cls="chip")
        values = {c.get("data-filter") for c in chips}
        self.assertIn("all", values, "there is no All chip")
        used = {p.get("data-tag") for p in posts()}
        for tag in used:
            with self.subTest(tag=tag):
                self.assertIn(tag, values, f"no chip for the {tag} tag")

    def test_stats_bands_are_well_formed(self):
        """A post may carry a numbers band; if it does, it needs real stats."""
        for post in posts():
            band = post.find("section", cls="stats")
            if band is None:
                continue
            with self.subTest(post=post.get("id")):
                stats = band.find_all("div", cls="stat")
                self.assertGreaterEqual(len(stats), 2)
                for stat in stats:
                    number = stat.find("span", cls="stat-number")
                    self.assertIsNotNone(number)
                    self.assertTrue(number.get("data-target"))

    def test_copy_paste_template_is_present(self):
        """The rota is students, not developers. The next post has to be a
        copy-paste, and the template must not render."""
        comments = " ".join(page().comments)
        self.assertIn(
            TEMPLATE_MARKER,
            comments,
            "no commented-out post template for the next writer",
        )

    def test_explains_the_cadence(self):
        text = page().root.stripped_text().lower()
        self.assertTrue(
            "month" in text,
            "the page never tells a sponsor how often it is updated",
        )


@unittest.skipUnless(S.built(FEED), f"{FEED} not built yet")
class SpecUpdatesFeed(unittest.TestCase):
    def setUp(self):
        self.tree = ET.parse(os.path.join(S.ROOT, FEED))
        self.channel = self.tree.getroot().find("channel")

    def test_channel_metadata(self):
        for tag in ("title", "link", "description"):
            with self.subTest(tag=tag):
                self.assertTrue((self.channel.findtext(tag) or "").strip())

    def test_one_item_per_post(self):
        items = self.channel.findall("item")
        self.assertEqual(
            len(items), len(posts()), "the feed and the posts have diverged"
        )

    def test_items_link_to_post_anchors(self):
        links = [i.findtext("link") for i in self.channel.findall("item")]
        for post in posts():
            anchor = f"{S.SITE_ORIGIN}/{PAGE}#{post.get('id')}"
            with self.subTest(post=post.get("id")):
                self.assertIn(anchor, links, f"feed does not link {anchor}")

    def test_pubdates_parse(self):
        for item in self.channel.findall("item"):
            raw = item.findtext("pubDate")
            with self.subTest(item=item.findtext("title")):
                self.assertIsNotNone(raw, "item has no pubDate")
                parsed = email.utils.parsedate_to_datetime(raw)
                self.assertIsInstance(parsed, datetime.datetime)


@unittest.skipUnless(S.built(PAGE), f"{PAGE} not built yet")
class SpecUpdatesDiscoverable(unittest.TestCase):
    def test_feed_is_advertised_in_the_head(self):
        alternates = [
            link
            for link in page().find_all("link")
            if "alternate" in (link.get("rel") or "")
        ]
        types = {link.get("type") for link in alternates}
        self.assertIn(
            "application/rss+xml", types, "updates.html does not advertise the feed"
        )


if __name__ == "__main__":
    unittest.main()
