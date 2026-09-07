# Site checks

Plain `unittest`, Python 3 standard library only. No `npm install`, no build
step, nothing added to the deployed site.

```sh
python3 tests/run.py              # both suites
python3 tests/run.py regression   # the invariants that must stay green
python3 tests/run.py spec         # the contracts for work not yet built
```

Only the regression suite sets the exit code. A red spec suite is the expected
state before the build, so it does not make the repo look broken.

## The two suites

**`test_*.py` — regression.** Invariants the site already satisfies. These are
what protect the parts that are good right now: nav and footer stay in step
across the eight files that duplicate them, every local link and asset
resolves, every page keeps its canonical/OG/Twitter metadata, every image keeps
its `alt` and its `width`/`height`, the redirect stubs keep working, and no
class name is left styled by nothing.

**`spec_*.py` — contracts.** Written before the pages exist, so they fail now
and go green as each piece lands. Each file's docstring carries the markup
shape it expects, which doubles as the build brief.

## What is currently red, and why

Regression is green. The spec suite is red on the work still to come:

| Failing check | Plan item |
| --- | --- |
| `spec_updates.*` | `updates.html` + `updates.xml` + the first post |
| `spec_events.*` | `events.html` + the `.ics` files |
| `spec_resources.*` | card index, collapsed embeds, filter box, GitHub/CAD/rookie entries |
| `spec_index.*` | homepage latest-update and next-event teasers |
| `spec_nav.*` | the remaining half: adding Updates to `tools/nav.html` and Events to the footer. The markers and `tools/sync-nav.sh` they also check are done. |

## Checks worth knowing about

A few of these keep working after the build, as alarms rather than one-off
gates:

- `spec_events.test_upcoming_and_past_are_labelled_honestly` fails once an
  "upcoming" event's date passes. That is the prompt to move the card to
  Been There, so the page cannot quietly go stale.
- `spec_resources.test_declared_size_matches_the_actual_file` pins the
  `4.2 MB` in each card's metadata line to the actual bytes on disk. Replace a
  PDF without updating the card and this catches it.
- `spec_updates` keeps the post list, the index rows, the filter chips and the
  RSS feed in agreement. The monthly rota is students, not developers; this is
  what stops post seven silently breaking the feed.
- `test_pages.test_nav_agrees_across_pages` is the guard for the problem noted
  in `kavan/31`: every nav change costs six file edits, soon eight.

## Adding a page

1. Add it to `CONTENT_PAGES` in `sitelib.py`.
2. Add it to `NAV` and/or `FOOTER_EXPLORE` if it belongs there.
3. Run the suite; it will tell you what the new page is missing.

## Note

`tests/` sits in the repo root, so GitHub Pages will serve these files. They
contain no secrets and nothing links to them, but that is why there is nothing
sensitive in here.
