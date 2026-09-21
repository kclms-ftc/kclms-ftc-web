# How the site works (read before editing)

Plain static HTML on GitHub Pages. No build step. All behaviour lives in
`script.js`; all styling in `styles.css`. Pushing to `main` deploys.

## Five rules

1. **`git pull` before you start, and again before you push.** More than one
   person commits here.
2. **Never edit between `<!-- XYZ:START -->` and `<!-- XYZ:END -->`.** A
   script writes that part, and your edit will be overwritten on the next run.
   Edit the source instead (see the table below).
3. **Don't remove `data-hunt="…"` from any image.** Those are the game's
   hidden stickers.
4. **Keep the `<script>` line straight after `<meta charset>` in each page's
   `<head>`, and keep `<script src="script.js">` at the end of `<body>`.**
   Without them, sections either never appear or never animate.
5. **Run `python3 tests/run.py` before pushing.** If a test fails, it prints
   the file and line.

## Generated parts

| What | Don't edit here | Edit this, then run |
| --- | --- | --- |
| Nav bar and footer (every page) | `NAV`, `FOOTER` markers | `tools/nav.html`, `tools/footer.html` → `tools/sync-nav.sh` |
| Updates page lists, homepage teaser, RSS, sitemap | `UPDATES:*` markers, `updates.xml`, `sitemap.xml` | the post files in `updates/` → `python3 tools/rebuild_updates.py` |

**Hiding a post:** add `data-status="draft"` to its `<article class="post">`,
then rebuild. The file stays, but the post goes off the site. Delete the
attribute to bring it back. Don't comment the HTML out.

## What `script.js` does, top to bottom

| Feature | How it works | Don't |
| --- | --- | --- |
| Hero slideshow | Rotates `.hero-slide` images, marking one `active` | leave a hero with no `active` slide |
| Number count-up | Counts `.stat-number` up to its `data-target` | put the number in the text. It goes in `data-target` |
| Nav highlight | Lights up the button whose file name matches the page | |
| Fade-in sections | Anything with class `reveal` fades in when it scrolls into view | **see below** |
| Live finances | Fetches the Hack Club Bank figures for the element with `data-hcb-slug` on Sponsors | rename or remove `data-hcb-*` attributes |
| Tilt toggle | Clicking a tilted photo, team card or sponsor tile straightens it | |
| Updates filter / Resources search | Hide or show cards on the page | |

### Fade-in (`reveal`): why it's built this way

Sections only hide while they wait for their fade-in once the page confirms
that JavaScript is running (it adds `.js` to `<html>`). If `script.js` doesn't
load within 3 seconds, everything is shown anyway. The old version hid content
unconditionally, and on phones pages showed only the nav bar and the hero.
Don't style `.reveal` with `opacity: 0` yourself; the rule lives under
`.js .reveal` in `styles.css`.

## The easter egg (the game)

**Fireboy**, the mascot, has four "flame moods" hidden as stickers across the
site:

| Sticker | Mood | Where |
| --- | --- | --- |
| `m1` | The Blaze | portfolio hero |
| `m2` | The Warmth | sponsors, Open Finances |
| `m3` | The Smoulder | the footer mascot, on every page |
| `m4` | The Spark | homepage, "This Season" block |

1. Click all four. Progress is saved in the browser.
2. **Erupt the volcano**, then accept the joke *cookie terms and conditions*.
   This sets the one real cookie the site uses (`volcanix_cookie`).
3. Play **The Calibration**. Winning it straightens every tilted element on
   the site.
4. That unlocks the **Volcano Arcade**: The Calibration, Provision 11 (rock,
   paper, scissors), Mood Sequence, Wonk Patrol and Stoke the Flame. Clearing
   them all unlocks the Grand Aligner.

Everything is saved in the visitor's own browser (`localStorage` keys
starting `vx-`). There's no server. **To reset while testing:** DevTools →
Application → Local Storage → delete the `vx-*` keys and the
`volcanix_cookie` cookie.

**Ways to break it by accident:**
- Removing or renaming a `data-hunt` sticker (it becomes unwinnable).
- Hand-editing the footer mascot on a page instead of `tools/footer.html`.
- Renaming the classes the tilt code targets: `.block-media img`,
  `.team-card`, `.gallery img`, `.sponsor-logos li`.
- **Renaming anything called `eruption` in `styles.css` or `script.js`.**
  `.eruption`, `.eruption-reward` and `eruption-in` are the game's volcano
  overlay, not the old "Eruptions" page name.
