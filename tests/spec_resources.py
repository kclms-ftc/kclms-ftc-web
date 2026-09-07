"""SPEC: the resources rework.

Today the page stacks four full-height PDF <object> embeds, one of which is a
15 MB portfolio, so reaching the branding guidelines means scrolling past two
whole documents. The rework puts a scannable card index on top and drops every
embed behind a closed <details>.

Expected card markup:

    <article class="resource-card" data-kind="pdf">
      <img class="resource-cover" src="media/portfolio-cover.png" ...>
      <h3>Engineering Portfolio</h3>
      <p class="resource-blurb">Design process, CAD and the season strategy.</p>
      <p class="resource-meta">PDF &middot; 14.3 MB &middot; updated Jul 2026</p>
      <a class="btn solid" href="media/engineering-portfolio-2025-26.pdf" download>...</a>
      <details class="resource-read"><summary>Read here</summary>
        <div class="pdf-frame"><object data="..." type="application/pdf">...</object></div>
      </details>
    </article>
"""

import glob
import os
import re
import unittest

import sitelib as S

PAGE = "resources.html"
META_RE = re.compile(
    r"^(PDF|ZIP|LINK|CAD)\s*·\s*"
    r"(?:(?:\d+(?:\.\d+)?\s*(?:KB|MB))|external)\s*·\s*"
    r"updated\s+[A-Z][a-z]{2}\s+\d{4}$"
)
SITE_PDFS = sorted(os.path.basename(p) for p in glob.glob(os.path.join(S.ROOT, "media", "*.pdf")))


def page():
    return S.Page.load(PAGE)


def cards():
    return page().find_all("article", cls="resource-card")


class SpecResourcesIndex(unittest.TestCase):
    def test_page_has_a_card_index(self):
        self.assertTrue(
            cards(), "resources.html still has no resource cards"
        )

    def test_index_comes_before_any_embed(self):
        """The whole point: you see the list of documents before you see a PDF."""
        first_card = page().find("article", cls="resource-card")
        first_embed = page().find("object")
        if first_embed is None:
            self.skipTest("no embeds on the page")
        self.assertIsNotNone(first_card, "no cards on the page")
        self.assertLess(
            first_card.line,
            first_embed.line,
            "a PDF embed appears above the resource index",
        )

    def test_every_pdf_in_the_repo_is_listed(self):
        listed = set()
        for card in cards():
            for anchor in card.find_all("a"):
                href = anchor.get("href") or ""
                if href.endswith(".pdf"):
                    listed.add(os.path.basename(href))
        for pdf in SITE_PDFS:
            with self.subTest(pdf=pdf):
                self.assertIn(pdf, listed, f"{pdf} is in the repo but not on the page")


@unittest.skipUnless(cards() if S.built(PAGE) else False, "no resource cards yet")
class SpecResourceCards(unittest.TestCase):
    def test_cards_have_a_title_and_a_blurb(self):
        for card in cards():
            with self.subTest(card=card.line):
                heading = card.find("h3")
                self.assertIsNotNone(heading, "card has no title")
                self.assertTrue(heading.stripped_text())
                blurb = card.find("p", cls="resource-blurb")
                self.assertIsNotNone(blurb, "card does not say what is inside")
                self.assertTrue(blurb.stripped_text())

    def test_cards_carry_a_metadata_line(self):
        """Type, size and last-updated is most of what makes a resource page
        feel navigable rather than a wall of documents."""
        for card in cards():
            meta = card.find("p", cls="resource-meta")
            with self.subTest(card=card.line):
                self.assertIsNotNone(meta, "card has no metadata line")
                self.assertRegex(
                    meta.stripped_text(),
                    META_RE,
                    "metadata must read 'PDF · 4.2 MB · updated Jul 2026'",
                )

    def test_declared_size_matches_the_actual_file(self):
        """Stale sizes are worse than none. Pin them to the bytes on disk."""
        for card in cards():
            meta = card.find("p", cls="resource-meta")
            download = None
            for anchor in card.find_all("a"):
                href = anchor.get("href") or ""
                if not S.is_external(href) and href.split("#")[0]:
                    download = href
                    break
            if download is None or meta is None:
                continue
            path = S.local_target(download)
            if path is None or not os.path.exists(path):
                continue
            expected = S.human_size(os.path.getsize(path))
            with self.subTest(card=card.line, file=download):
                self.assertIn(
                    expected,
                    meta.stripped_text(),
                    f"{download} is {expected} on disk but the card disagrees",
                )

    def test_cards_offer_a_download(self):
        for card in cards():
            hrefs = [a.get("href") for a in card.find_all("a")]
            with self.subTest(card=card.line):
                self.assertTrue(hrefs, "card has no link at all")
                for href in hrefs:
                    if S.is_external(href):
                        continue
                    self.assertTrue(
                        os.path.exists(S.local_target(href)),
                        f"{href} does not resolve",
                    )


@unittest.skipUnless(S.built(PAGE), f"{PAGE} not built yet")
class SpecResourcesEmbeds(unittest.TestCase):
    def test_every_embed_is_collapsed(self):
        """A closed <details> is what stops the 15 MB portfolio loading on open."""
        for obj in page().find_all("object"):
            with self.subTest(line=obj.line, data=obj.get("data")):
                self.assertTrue(
                    any(a.tag == "details" for a in obj.ancestors()),
                    f"{obj.get('data')} is embedded outside a <details>",
                )

    def test_details_are_closed_by_default(self):
        for details in page().find_all("details"):
            with self.subTest(line=details.line):
                self.assertIsNone(
                    details.get("open"), "a resource embed opens by default"
                )

    def test_details_have_a_summary(self):
        for details in page().find_all("details"):
            with self.subTest(line=details.line):
                summary = details.find("summary")
                self.assertIsNotNone(summary, "<details> with no <summary>")
                self.assertTrue(summary.stripped_text())


@unittest.skipUnless(S.built(PAGE), f"{PAGE} not built yet")
class SpecResourcesNavigation(unittest.TestCase):
    def test_resources_are_grouped_into_categories(self):
        banners = page().find_all("div", cls="section-banner")
        self.assertGreaterEqual(
            len(banners), 3, "resources are not grouped into categories"
        )

    def test_there_is_a_filter_box(self):
        search = None
        for node in page().find_all("input"):
            if node.get("id") == "resource-search":
                search = node
        self.assertIsNotNone(search, "no search/filter input over the cards")
        self.assertTrue(search.get("aria-label") or search.get("placeholder"))

    def test_offsite_resources_are_present(self):
        """Sponsors and rookie teams ask for the code and the CAD, not only the
        PDFs."""
        hrefs = " ".join(a.get("href") or "" for a in page().find_all("a"))
        self.assertIn("github.com", hrefs, "the repo is not linked from resources")

    def test_rookie_section_exists(self):
        text = page().root.stripped_text().lower()
        self.assertIn(
            "rookie", text, "no 'for rookie teams' grouping (Connect award fodder)"
        )


if __name__ == "__main__":
    unittest.main()
