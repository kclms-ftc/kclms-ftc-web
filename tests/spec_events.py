"""SPEC: events.html.

Scoped as Events *and* Competitions so the page is populated on day one from
qualifiers, school visits and the bake sale, rather than sitting empty until an
event gets organised. Two sections: Coming Up and Been There.

Expected card markup:

    <article class="event-card" id="ukq-guildford-2025" data-when="upcoming">
      <div class="date-chip"><span class="chip-mon">Nov</span><span class="chip-day">15</span></div>
      <h3>UK Qualifier &mdash; Guildford</h3>
      <p class="event-where">Royal Grammar School, Guildford</p>
      <p class="event-when"><time datetime="2025-11-15">15 November 2025</time></p>
      <a class="btn ghost" href="media/events/ukq-guildford-2025.ics" download>...</a>
    </article>
"""

import datetime
import os
import re
import unittest

import sitelib as S

PAGE = "events.html"
MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


class SpecEventsExist(unittest.TestCase):
    def test_page_is_built(self):
        self.assertTrue(S.built(PAGE), f"{PAGE} has not been built yet")


def page():
    return S.Page.load(PAGE)


def cards():
    return page().find_all("article", cls="event-card")


def card_date(card):
    stamp = card.find("time")
    return datetime.date.fromisoformat(stamp.get("datetime"))


@unittest.skipUnless(S.built(PAGE), f"{PAGE} not built yet")
class SpecEventsPage(unittest.TestCase):
    def test_headline(self):
        self.assertIn("Events", page().find("h1").stripped_text())

    def test_populated_or_honestly_empty(self):
        """Nothing is scheduled yet, and inventing dates would be worse than
        saying so. Either there are real cards, or the empty state carries the
        page. What is not allowed is a blank column."""
        if not cards():
            self.assertIsNotNone(
                page().find(cls="event-empty"),
                "no events and no empty state: the page would just be a gap",
            )
            empty = page().find(cls="event-empty")
            self.assertTrue(
                empty.find_all("a"), "the empty state offers the reader nothing to do"
            )

    def test_says_how_to_book_the_team(self):
        """The page has to work as an inbound route for schools and sponsors,
        not only as a calendar."""
        hrefs = " ".join(a.get("href") or "" for a in page().find_all("a"))
        self.assertIn("mailto:", hrefs, "no way to get in touch about an event")

    def test_both_sections_present(self):
        headings = {
            b.stripped_text().lower()
            for b in page().find_all("div", cls="section-banner")
        }
        joined = " ".join(headings)
        self.assertIn("coming up", joined, "no Coming Up section")
        self.assertIn("been there", joined, "no Been There section")

    def test_cards_are_identified(self):
        ids = [c.get("id") for c in cards()]
        for card_id in ids:
            with self.subTest(card=card_id):
                self.assertTrue(card_id, "event card has no id to deep-link")
        self.assertEqual(len(ids), len(set(ids)), "duplicate event ids")

    def test_cards_carry_a_parseable_date(self):
        for card in cards():
            with self.subTest(card=card.get("id")):
                stamp = card.find("time")
                self.assertIsNotNone(stamp, "event has no <time>")
                datetime.date.fromisoformat(stamp.get("datetime"))

    def test_date_chip_matches_the_real_date(self):
        for card in cards():
            with self.subTest(card=card.get("id")):
                chip_mon = card.find("span", cls="chip-mon")
                chip_day = card.find("span", cls="chip-day")
                self.assertIsNotNone(chip_mon, "no month chip")
                self.assertIsNotNone(chip_day, "no day chip")
                when = card_date(card)
                self.assertEqual(
                    MONTHS[chip_mon.stripped_text()[:3].lower()],
                    when.month,
                    "date chip month disagrees with the <time>",
                )
                self.assertEqual(int(chip_day.stripped_text()), when.day)

    def test_cards_say_where(self):
        for card in cards():
            with self.subTest(card=card.get("id")):
                where = card.find("p", cls="event-where")
                self.assertIsNotNone(where, "event does not say where it is")
                self.assertTrue(where.stripped_text())

    def test_upcoming_and_past_are_labelled_honestly(self):
        """This is the staleness alarm: when an upcoming event's date passes,
        this fails until someone moves the card to Been There."""
        today = datetime.date.today()
        for card in cards():
            when = card_date(card)
            state = card.get("data-when")
            with self.subTest(card=card.get("id"), date=when):
                self.assertIn(state, {"upcoming", "past"}, "bad data-when")
                if state == "upcoming":
                    self.assertGreaterEqual(
                        when, today, "an 'upcoming' event is in the past"
                    )
                else:
                    self.assertLess(
                        when, today, "a 'past' event has not happened yet"
                    )

    def test_empty_state_exists(self):
        """With nothing upcoming the page must still sell something, not show a
        blank column."""
        self.assertIsNotNone(
            page().find(cls="event-empty"),
            "no fallback block for when nothing is scheduled",
        )

    def test_past_events_link_to_their_write_up(self):
        """Been There cards tie back to the month they were covered in."""
        for card in cards():
            if card.get("data-when") != "past":
                continue
            hrefs = [a.get("href") or "" for a in card.find_all("a")]
            with self.subTest(card=card.get("id")):
                self.assertTrue(
                    any(re.search(r"updates\.html#\d{4}-\d{2}$", h) for h in hrefs),
                    "past event does not link its update post",
                )


@unittest.skipUnless(S.built(PAGE), f"{PAGE} not built yet")
class SpecEventsSchema(unittest.TestCase):
    def events_in_schema(self):
        found = []
        for block in page().json_ld():
            for entry in block.get("@graph", [block]):
                if entry.get("@type") == "Event":
                    found.append(entry)
        return found

    def test_one_schema_event_per_card(self):
        self.assertEqual(
            len(self.events_in_schema()),
            len(cards()),
            "every event card needs a schema.org Event so search can surface it",
        )

    def test_schema_events_are_complete(self):
        for entry in self.events_in_schema():
            with self.subTest(event=entry.get("name")):
                self.assertTrue(entry.get("name"))
                self.assertTrue(entry.get("startDate"))
                datetime.date.fromisoformat(entry["startDate"][:10])
                location = entry.get("location") or {}
                self.assertTrue(location.get("name"), "event has no location name")
                self.assertTrue(entry.get("organizer"), "event has no organizer")

    def test_schema_dates_match_the_cards(self):
        card_dates = {c.find("time").get("datetime") for c in cards()}
        for entry in self.events_in_schema():
            with self.subTest(event=entry.get("name")):
                self.assertIn(
                    entry["startDate"][:10],
                    card_dates,
                    "schema startDate matches no card on the page",
                )


@unittest.skipUnless(S.built(PAGE), f"{PAGE} not built yet")
class SpecEventsCalendar(unittest.TestCase):
    def ics_refs(self):
        return [
            a.get("href")
            for a in page().find_all("a")
            if (a.get("href") or "").endswith(".ics")
        ]

    def test_upcoming_events_offer_a_calendar_file(self):
        upcoming = [c for c in cards() if c.get("data-when") == "upcoming"]
        for card in upcoming:
            hrefs = [a.get("href") or "" for a in card.find_all("a")]
            with self.subTest(card=card.get("id")):
                self.assertTrue(
                    any(h.endswith(".ics") for h in hrefs),
                    "upcoming event has no add-to-calendar file",
                )

    def test_ics_files_exist_and_are_valid(self):
        for href in self.ics_refs():
            path = S.local_target(href)
            with self.subTest(ics=href):
                self.assertTrue(os.path.exists(path), f"{href} is missing")
                with open(path, encoding="utf-8") as handle:
                    body = handle.read()
                self.assertTrue(body.startswith("BEGIN:VCALENDAR"))
                self.assertIn("END:VCALENDAR", body)
                for field in ("UID:", "DTSTART", "SUMMARY:"):
                    self.assertIn(field, body, f"{href} has no {field}")

    def test_ics_dates_match_the_page(self):
        for card in cards():
            ics = [
                a.get("href")
                for a in card.find_all("a")
                if (a.get("href") or "").endswith(".ics")
            ]
            if not ics:
                continue
            with open(S.local_target(ics[0]), encoding="utf-8") as handle:
                body = handle.read()
            match = re.search(r"DTSTART[^:]*:(\d{8})", body)
            with self.subTest(card=card.get("id")):
                self.assertIsNotNone(match, "no DTSTART date in the ics")
                self.assertEqual(
                    match.group(1),
                    card_date(card).strftime("%Y%m%d"),
                    "the calendar file disagrees with the page",
                )


if __name__ == "__main__":
    unittest.main()
