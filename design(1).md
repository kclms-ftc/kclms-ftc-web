# Site Design Analysis — 14906.tulsaroboticscenter.org

## What kind of site this is
A single-page, scroll-driven promotional site for a competitive robotics team (built on WordPress + Elementor). It functions like a digital poster or event programme more than a conventional "corporate" website: one tall page, a fixed header that stays on screen throughout, and a small set of sub-pages (About, Team, CAD) reached through that same persistent header rather than a multi-level menu structure.

## Overall aesthetic
The design reads as **varsity/motorsport-poster energy filtered through a flat, sticker-based digital layout** — bold italicised display lettering, sharp angular button shapes, and hard-edged "stamped" drop shadows rather than soft, realistic elevation. It leans graphic and poster-like rather than minimal or corporate; nothing is subtle, everything is oversized, tilted, or outlined for impact.

## Layout & structure
- Single continuous vertical scroll, no sidebars, no multi-column dashboard layout.
- Content is built almost entirely from stacked flexbox containers (row and column), not a traditional grid system — rows wrap onto new lines on narrow screens rather than reflowing into a grid.
- A generous, consistent spacing scale is used throughout (roughly 7px up to 80px in fixed steps), which keeps vertical rhythm predictable between blocks even though the page is visually loud.
- Main content area is capped at a fixed maximum width and centred, while some elements are deliberately allowed to break out full-width (hero, header bar) — a common "contained content, full-bleed backgrounds" pattern.
- The hero section occupies a large share of the viewport (roughly 70–85% of viewport height depending on screen size), so the very first thing seen is a nearly full-screen banner rather than a compact strip.

## Header / navigation
- The header is fixed/pinned to the top and stays visible while scrolling, layered above the rest of the content.
- It is a horizontal strip containing a logo mark sized to a fixed height (so it scales down proportionally rather than stretching), followed by a row of nav items spaced evenly across the remaining width.
- A soft radial vignette sits behind the fixed header, darkening toward one edge — this keeps the logo/nav legible over whatever busy image or block sits directly beneath it, without needing a solid opaque bar.
- Navigation items are rendered as **buttons, not plain text links** — each one is a slanted parallelogram (achieved via a skew transform, not a rotation), giving the whole nav row a dynamic, "leaning forward" feel rather than sitting flat.
- These nav buttons have sharp square corners (no rounding at all here, in contrast to the site's general button style elsewhere), bold condensed all-caps labels, and swap their fill/label emphasis on hover — i.e. hovering visibly inverts which part of the button is emphasised, giving clear tactile feedback.

## Typography
- Two distinct type voices are used, and they're kept deliberately far apart in character:
  - A heavy, condensed, italicised, all-caps display face for headings, the hero title, and every button label. Letter-spacing is pulled slightly tight/negative at large sizes, and headline text carries a thin outline stroke plus a soft blurred glow behind it — giving headings a raised, sticker/decal quality rather than sitting flat on the page.
  - A lighter, italic serif-leaning accent face for the short descriptive tagline text sitting beside the hero, contrasted against a plain, humanist sans-serif used for regular running body copy elsewhere on the page.
- Headings scale fluidly with viewport width (using CSS clamp), so the jump between a heading on mobile and the same heading on a wide desktop screen is smooth rather than snapping between fixed sizes at breakpoints.
- All-caps treatment and wide letter tracking is reserved for headings and buttons only — body paragraphs are set in mixed case at a more relaxed line-height, so the "shouting" display type is used sparingly as punctuation rather than for continuous reading.

## Shape language & component style
- Two competing corner treatments coexist by design: general buttons elsewhere on the site use a small, soft rounded corner, while the nav buttons and the hero call-to-action buttons are fully square-cornered and skewed — signalling "primary navigation/action" versus "secondary/general" through shape alone.
- Buttons generally carry a thick border that's invisible until interaction, plus a hard-edged, offset drop shadow (a solid duplicate silhouette pushed a few pixels down and to the right, with little to no blur) — closer to a screen-printed sticker or a stamp than a soft, realistic shadow. Deeper "elevated" variants of this same offset-shadow idea exist in the design system (some with much larger offsets, some with a thin outline plus a solid block shadow) — the family of options all favour hard graphic shadows over soft blurred ones.
- A large standalone sticker/mascot-style image breaks out of the normal content flow entirely — placed as its own graphic element rather than boxed into a card, reinforcing the "poster" feel.
- Sponsor/partner logos are displayed as a horizontally auto-scrolling, looping strip (the logo list is duplicated back-to-back so the scroll never visibly resets), with every logo vertically centred and scaled to fit a shared row height regardless of its native proportions — turning a mismatched set of external logos into one visually even row.
- A wave-shaped divider sits along the bottom edge of the hero, separating it from the section beneath with a curved rather than straight edge; this shape is scaled wider than the viewport itself and grows proportionally wider still on smaller screens, so the curve's steepness stays roughly consistent rather than looking stretched.

## Motion & interaction
- Content sections animate in on scroll using directional entrance effects — fading in, fading in from above, sliding in from the side, and zooming in — rather than appearing statically. This gives the page a "reveal as you go" pacing typical of landing pages/pitch decks.
- Interactive elements (buttons, links) use short, snappy transitions (a couple of tenths of a second) on hover/focus rather than instant or sluggish state changes.
- The header's background vignette and the top accent bar's diagonal gradient are both static (not animated), so movement is reserved for content entering the viewport, not for decorative chrome.

## Imagery treatment
- Photography/logo imagery is treated as flat, contained blocks (object-fit "contain/scale-down" behaviour) rather than being cropped edge-to-edge — logos in particular are never stretched or cropped, only scaled down to fit their row.
- The hero itself uses a full-bleed background image/slideshow behind the heading, with the wave divider cutting it off cleanly at the bottom rather than letting it fade out.

## Responsiveness
- Two clear breakpoints govern layout changes (roughly tablet-width and phone-width). Below these:
  - The hero shrinks in height and its bottom wave divider is scaled up proportionally more aggressively so the curve doesn't flatten out.
  - Side padding around text blocks increases substantially (moving from viewport-width-based single digits up to double digits) so text doesn't run edge-to-edge on small screens.
  - Row-based nav/content blocks that sit side-by-side on desktop switch to wrapping/stacking, and elements that had a fixed partial width expand to fill the full row.

## In summary
This is a bold, high-contrast, poster-style single-page site built around skewed sticker-shaped buttons, heavy italic condensed display type with outline/glow treatment on headings, hard offset "stamp" shadows rather than soft elevation, a looping logo marquee, and scroll-triggered directional entrance animation — all assembled from stacked flexbox blocks rather than a rigid grid, with a fixed header riding above the entire scroll.
