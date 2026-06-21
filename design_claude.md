# Kavan Vyas — Design System Specification

This document captures every design decision embedded in the Kavan Vyas portfolio codebase. It serves as an exhaustive reference for reproducing the look, feel, layout, and behavior of the portfolio.

---

## 1. Overview
The personal portfolio site for Kavan Vyas (mathematician, programmer, and builder at KCLMS) is built using a **Technical Brutalist** aesthetic. 
The system runs on vanilla HTML5, CSS3, and JavaScript (ES6+). It couples a rigid layout structure—defined by sharp borders, zero border-radius, and mathematical grids—with organic, fluid motion systems (such as a chained physical cursor, Momentum smooth scrolling, and a custom image magnifying lens).

---

## 2. Design Principles
*   **Proof. / Not / Plausibility. (Mathematical Rigour):** The visual language mirrors a researcher's notebook. Formulas are rendered literally, numbers are presented with tabular alignment, and visual decoration is derived from mathematical equations and coordinate geometry rather than aesthetic filler.
*   **Raw Structural Framing:** Layout zones are partitioned using explicit solid borders (1px to 1.5px) rather than background colors or drop shadows.
*   **Organic Micro-Interactions:** The rigid layout is balanced by soft, physics-based trailing elements (e.g., cursor dot-and-ring lerps) and spring-based scroll entries.
*   **Clipped Typographic Hierarchy:** Heavy styling is applied to case treatments: ticker items, tags, and label metrics are strictly uppercase; username headings and repository filenames are lowercase. Title Case is avoided.

---

## 3. Colour System

### Core Palette
The core colors are defined as CSS custom properties under the `:root` pseudo-class:

| Token Name (Website) | Token Name (Design System File) | Literal Value | Description |
| :--- | :--- | :--- | :--- |
| `--bg` | `--kv-bg` | `#EBEBEB` | Warm off-white (concrete matte background) |
| `--text` | `--kv-text` | `#111111` | Near-black ink (primary text and outlines) |
| `--accent` | `--kv-accent` | `#FF5C00` | Signal orange (highlights, cursor, active state) |
| `--accent-bg` | `--kv-accent-bg` | `#FFF5EF` | Soft orange wash (hover state background tint) |
| `--blue` | `--kv-blue` | `#0000CC` | Imperial Blue (monospace numeric keys & logos) |
| `--black` | `--kv-black` | `#000000` | Pure black (ticker background block) |
| `--white` | `--kv-white` | `#FFFFFF` | Pure white (contrast text on black/orange) |
| *N/A* | `--kv-snake-dark` | `#228822` | Dark green (loader background stripes) |
| *N/A* | `--kv-snake-mid` | `#33CC33` | Mid green (loader progress bar fill & border) |
| *N/A* | `--kv-snake-glow` | `#66FF66` | Bright green (loader progress bar glow) |

### Theme Variations (Side-by-Side Comparison)
The theme is toggled by cycling the `data-theme` attribute on the `<html>` root:

```css
/* Custom properties mapping per theme (defined in css/global.css) */
```

| Token | Light (Default) | Dark (`[data-theme="dark"]`) | B&W Mono (`[data-theme="bw"]`) |
| :--- | :--- | :--- | :--- |
| `--bg` | `#EBEBEB` | `#111111` | `#FFFFFF` |
| `--text` | `#111111` | `#F0F0F0` | `#000000` |
| `--accent` | `#FF5C00` | `#FF5C00` | `#000000` |
| `--accent-bg`| `#FFF5EF` | `#2D1A10` | `#F5F5F5` |
| `--blue` | `#0000CC` | `#FF5C00` (Imperial Blue → Orange) | `#0000CC` (Blue retained) |
| `--black` | `#000000` | `#000000` | `#000000` |
| `--white` | `#FFFFFF` | `#FFFFFF` | `#FFFFFF` |

### Semantic Opacity Conventions
Muted states are created using alpha transparency on the primary ink color (`--text`):
*   `--fg-1` (100% opacity): Primary body prose and prominent headings.
*   `--fg-2` (80% opacity): Secondary body paragraphs and notes (`rgba(17, 17, 17, 0.8)`).
*   `--fg-3` (60% opacity): Eyebrows, labels, and tick metrics (`rgba(17, 17, 17, 0.6)`).
*   `--fg-4` (50% opacity): Footer column headings (`rgba(17, 17, 17, 0.5)`).
*   `--fg-5` (40% opacity): Micro footers and copyright lines (`rgba(17, 17, 17, 0.4)`).

---

## 4. Typography

### Font Families
*   **Serif Display:** `'Playfair Display', Georgia, serif`. Linked from Google Fonts. Used for serif display headers (`h1`, `h2`), portal headings, and mathematical formulas (e.g. sigma equations).
*   **Monospace UI + Body:** `'Consolas', 'Inconsolata', 'Monaco', monospace`. Google Font `Inconsolata` is loaded as the cross-platform rendering fallback. Used for body text, tickers, navigation, numeric tags, and key-value metrics.
*   **Pixel Display:** `'Press Start 2P', monospace`. Loaded from Google Fonts. Used exclusively for the pixelated loading percentage display (`NN%`).

### Type Scale & Hierarchy

| Token | CSS Variable | Font Size (Value) | Line Height | Letter Spacing | Intended Casing / Usage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Hero Name** | `--fz-hero` | `clamp(3rem, 10vw, 9rem)` | `0.85` | `0.02em` | lowercase (monospace) |
| **Portal Number** | `--fz-display` | `clamp(3rem, 7vw, 8rem)` | `0.9` | `0.08em` | lowercase (serif display) |
| **Headline H1** | `--fz-h1` | `clamp(3rem, 6vw, 7rem)` | `0.9` | `0.08em` | Sentence case (serif display) |
| **Headline H2** | `--fz-h2` | `clamp(2rem, 4vw, 4rem)` | `1.0` | `0.08em` | Sentence case / uppercase |
| **Stat Value** | `--fz-stat` | `2.8rem` | `1.0` | `-0.02em` | Tabular numbers (monospace) |
| **Body text** | `--fz-body` | `16px` | `1.4` | `normal` | Sentence case (monospace) |
| **Body Prose** | `--fz-para` | `13px` | `1.8` | `normal` | Paragraphs (monospace) |
| **Timeline Item** | `--fz-small` | `12px` | `1.6` | `normal` | Sub-labels, timelines |
| **UI labels** | `--fz-label` | `11px` | `1.0` | `0.18em` | UPPERCASE (nav, tags) |
| **Micro-labels** | `--fz-micro` | `10px` | `1.6` | `0.20em` | UPPERCASE (footers, keys) |
| **Nano-labels** | `--fz-nano` | `9px` | `1.6` | `0.12em` | UPPERCASE (metric subscripts) |

---

## 5. Spacing & Sizing

### Spacing Scale
The spacing system uses a relative rem-scale anchored to a `0.5rem` (8px) base spacing unit:

| Token Name | Rem Value | Pixel Value | Intended Usage |
| :--- | :--- | :--- | :--- |
| `--space-1` | `0.5rem` | 8px | Internal element padding (pills, badges) |
| `--space-2` | `1rem` | 16px | Intermediate margins, plot paddings |
| `--space-3` | `1.5rem` | 24px | Small column gaps, text segment offsets |
| `--space-4` | `2rem` | 32px | Nav bar side padding, small section gaps |
| `--space-6` | `3rem` | 48px | Timeline grid margins, controls row spacing |
| `--space-8` | `4rem` | 64px | Outer boundaries, table padding, grid gutters |
| `--space-12` | `6rem` | 96px | Section vertical heights, timeline spacers |
| `--space-16` | `8rem` | 128px | Outer page top-paddings, major gaps |

### Sizing and Container Constraints
*   **Sticky Ticker Height:** `36px` (`sticky` positioning at top of viewport).
*   **Navigation Header Height:** `60px` (`sticky` positioning below ticker).
*   **Paragraph Max-Width:** `.paragraph` has a hard limit of `500px` to maintain readability.
*   **Hero Graph SVG Container:** `width: min(480px, 40vw); height: min(480px, 40vw)` to maintain a square aspect ratio.
*   **Mag Glass Lens Diameter:** `180px` (when hover lens is active).

---

## 6. Layout & Grid
*   **Viewport Edge Offsets:** The chrome header, footers, and page main wrappers have horizontal padding set to `2rem` (32px), `3rem` (48px), or `4rem` (64px) depending on the context.
*   **Asymmetrical Columns:** Two-column page structures use asymmetrical layouts (e.g. `.about-section` is `1.2fr 0.8fr`; maths `.anim-body` is `1.6fr 1fr`; `.maths-section` is `1.5fr 1fr`).
*   **Border-Defined Grids:** Grids use explicit border styling rather than flex-gap sizing, splitting panels with solid lines (e.g. `border-right: 1.5px solid var(--text)`).
*   **Responsive Breakpoints:**
    *   `860px` (Tablet/Mid Screen): Collapses 3-column project cards to 1 column, collapses capabilities columns, merges 2-column animations to vertical stacks, and stacks the side-by-side pendulum.
    *   `720px` (Mobile): Collapses index Euler asymmetric columns (`minmax(240px, 340px) 1fr`) to a single column, centering the plot graphic.

---

## 7. Borders, Radii & Dividers
*   **Border Width Scale:**
    *   `--border`: `1.5px solid var(--text)` (nav boundaries, portal grids, active boundaries)
    *   `--border-hair`: `1px solid var(--text)` (internal cards, timeline items, metric boxes)
    *   `--border-dashed`: `1.5px dashed var(--text)` (used exclusively on the About lens zone)
*   **Brutalist Zero Radius:** `--radius: 0` (and `--kv-radius: 0`). The border-radius property is explicitly zeroed out across all buttons, portal cells, timelines, and tags.
*   **Dividers:** Drawn as borders directly on layout containers rather than `<hr>` markup (e.g., `border-top: var(--border)`).

---

## 8. Elevation & Shadows
The brutalist aesthetic avoids standard drop shadows and ambient lighting. Depth is depicted via flat, hard offsets:

*   **No Drop Shadows:** Standard card surfaces are completely flat with no box-shadow blur.
*   **Brutalist Hard Shadows:** Offset shadow parameters are defined in `colors_and_type.css`:
    *   `--kv-shadow-sm` (`3px 3px 0 0 var(--text)`): Assigned to `.timeline-item`, `.brut-btn`, `.brut-slider`.
    *   `--kv-shadow-md` (`5px 5px 0 0 var(--text)`): Assigned to hovered button states (`.brut-btn:hover`).
    *   `--kv-shadow-press` (`1px 1px 0 0 var(--text)`): Assigned to active button clicks (`.brut-btn:active` / `.pill-tag:active`).
*   **Glow Shadows (Loader Only):** The progress bar container features a green glow (glow radius `8px` at `rgba(51, 204, 51, 0.25)` or `#66ff66`).

---

## 9. Iconography
*   **Typographic Symbols (Unicode):** The visual system uses typographic punctuation to replace icon symbols:
    *   `◆` (U+25C6): Ticker line content divider.
    *   `→` (U+2192): Portal card arrows and primary actions.
    *   `·` (U+00B7): Keyword / Tag separators.
    *   `↑` (U+2191): Scroll-to-top button symbol.
    *   `Σ` (U+03A3): Mathematical summation accent.
*   **Lucide Glyphs (Exception):** Standard icons are omitted. If required (e.g. social footers), the design system suggests loading Lucide SVG elements at a stroke-width of `1.5` and color set to `currentColor` (though none exist in the core templates).

---

## 10. Imagery & Illustration
*   **Cinematographic Treatments:** Imagery consists of architectural/landscape photography of London (Canary Wharf, Big Ben, Westminster bridge). The colors are processed with warm, gold-orange tones, matched with fine film grain.
*   **Image Framing:** Images never bleed to the edge; they are housed within a border frame (e.g., `.lens-zone` uses `border-dashed`).
*   **Liquid Glass Lens Zone:**
    *   Images in the zone default to a blurred state via `backdrop-filter: blur(12px) saturate(1.6)`.
    *   Hovering morphs the cursor ring into a `180px` circle, applying a background-image that matches the coordinate overlay, rendering a sharp image focal point.
*   **Illustration Style:** Vector graphics are strictly functional SVG plots (curves, grid vectors, coordinate nodes) styled dynamically with theme variables.

---

## 11. Motion & Animation
All motion transitions are implemented via CSS and requestAnimationFrame (RAF).

### Easing Curves
*   **Spring entrance ease:** `var(--ease-organic): cubic-bezier(0.34, 1.56, 0.64, 1)`. Adds a minor bounce to entrance animations.
*   **Custom cursor ring ease:** `var(--ease-ring): cubic-bezier(0.23, 1, 0.32, 1)`. Creates an elastic lag behind the dot.
*   **Standard linear fade:** `var(--transition): 0.3s ease`. Used for theme color switching.

### Scroll-driven Animations
*   **Intersection Observer Reveal:** Elements with `.reveal` or `.reveal-group > *` are bound to an observer with a `0.15` threshold. On viewport entry, they fade in and slide up:
    ```css
    .reveal {
        opacity: 0; transform: translateY(40px) scale(0.98); filter: blur(5px);
        transition: opacity 1.2s var(--ease-organic), transform 1.2s var(--ease-organic), filter 1.2s var(--ease-organic);
    }
    .reveal.in-view { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
    ```
*   **Staggered Entrance:** Child items inside `.reveal-group` use CSS transition delays incrementing by `0.1s` per child (`nth-child(1)` has `0.1s` delay, up to `0.6s`).
*   **Scroll-driven Hero SVG Plot:** In `js/heroplot.js`, scrolling triggers a redraw of the SVG path. The curve retracts (modifying `strokeDashoffset` from `0` to `1` relative to scroll progress) and the nodes fade out progressively.

### Keyframe Animations
*   **Ticker Infinite Scroll (`ticker`):** Translates text blocks horizontally.
    ```css
    @keyframes ticker { 0% { transform: translate3d(0, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); } }
    ```
    *   Normal Ticker: 28s duration.
    *   Reverse Ticker: 32s duration.

---

## 12. Components

### Navigation Bar
*   **Structure:** `nav` element containing a `.nav-logo-link` wrapping a logo, and `.nav-links` wrapping text links.
*   **States:**
    *   *Default:* Monospace uppercase links with color `var(--text)`.
    *   *Hover:* Underlying border expands from `width: 0` to `width: 100%` in `0.25s` with color `var(--accent)` (`#FF5C00`).
*   **Sizing:** Height `60px`, padding `0.8rem 2rem`.

### Ticker
*   **Structure:** `.ticker-wrap` wrapper with `.ticker` containing duplicate text lines.
*   **States:** Passive infinite scrolling.
*   **Variants:** Standard (left-scrolling, black background) and `.ticker-wrap-reverse` (right-scrolling, blue star highlights).

### Logotype (Ket-notation logo)
*   **Structure:** `.ket` class. Serif letters "k" and "v" separated by custom CSS border stripes (`.pipe` and `.angle`).
*   **Variants:**
    *   Nav Logo (`.nav-ket`): `font-size: 22px`. Pipe width `3px`, angle border thickness `3px` (heavy variant uses `3.5px`).
    *   Hero Display (`.s-80`): `font-size: 80px`. Pipe width `6px`, angle thickness `6px` (heavy variant uses `7px`/`8px`).
    *   Footer Mark (`.footer-ket`): `font-size: 14px`. Pipe/angle thickness `1.5px`.
    *   *Theme Colors:* Blue angle collapses to orange in dark theme; orange collapses to black in black-and-white theme.

### Custom Cursor
*   **Structure:** `#cursor-dot` (12px solid circle) and `#cursor-ring` (40px hollow ring). Position is fixed.
*   **Physics:** Dot lerps to mouse position (`factor: 0.35`). Ring lerps to dot position (`factor: 0.18`).
*   **States:**
    *   *Hover on `a, button`:* Dot shrinks to 6px; ring expands to 60px.
    *   *Hover on tiles (`.portal-tile`, `.project-card`):* Ring expands to 60px with border-width `2px`.
    *   *Hover on `.lens-zone`:* Dot opacity goes to 0; ring expands to 180px with 3px border and handles magnifying image backgrounds.

### Theme Switcher
*   **Structure:** `.theme-switcher` button, fixed at bottom-right corner.
*   **States:** Clicks trigger attribute toggling on HTML root.

### Portal Tile
*   **Structure:** `.portal-tile` link. Housed in a 3-column `.portal-grid`.
*   **States:**
    *   *Default:* Border `1.5px solid var(--text)`, flat background, hard shadow offset `4px 4px` (or `3px 3px`).
    *   *Hover:* Background turns to `--accent-bg` (soft orange wash), tiles translate up-left by `-4px, -4px` (or `-2px, -2px`), shadow offset increases to `8px 8px`.
    *   *Active Press:* Tiles translate down-right by `3px 3px`, shadow offset collapses to `1px 1px`.

### Project Card
*   **Structure:** `.project-card` link containing name, tags, description, and an orange prompt arrow.
*   **States:**
    *   *Hover:* Background transitions to `--accent-bg`, prompt arrow slides right (`transform: translateX(4px)`), and project details fade in.
*   **Variants:** Featured cards display an interactive ASCII fractal mockup.

### Pill Tag
*   **Structure:** `.pill-tag` borders.
*   **Variants:** Standard, `.orange` (filled orange background), and `.blue` (filled blue background).
*   **States:** Shifts slightly on hover/active click.

### Section Headers
*   **Structure:** `.sec-header` containing a monospace label `.sec-num` (e.g. `M.1`) and title `.sec-title` separated from content by a 1px border.

### Timeline Strip
*   **Structure:** `.timeline-strip` wrapper containing `.timeline-item` divs.
*   **States:** Hover moves items up-left by `2px`. `.current` adds orange borders and shadows.

### Capabilities Row
*   **Structure:** `.cap-row` grids.
*   **States:** Hover slides text left (`padding-left: 0.8rem`) and applies `--accent-bg` background.

### Math Anim Controls (Buttons & Sliders)
*   **Button (`.brut-btn`):** Brutalist button with offset shadow `3px 3px`. Hover translates up-left by `-2px, -2px` with a `5px 5px` shadow. Active/Pressed (`.active`) shifts down-right by `2px` and turns orange background.
*   **Slider (`.brut-slider`):** Native range inputs styled with custom parameters:
    *   Track: `height: 2px; background: var(--text)`
    *   Thumb: `width: 12px; height: 20px; background: var(--accent); border: 1.5px solid var(--text); border-radius: 0`

### Key-Value Readout Grid
*   **Structure:** `.kv-grid` container holding `.kv` elements (composed of `.k` label and `.v` value). Uses tabular numerals (`font-variant-numeric: tabular-nums`).

### Formula Box
*   **Structure:** `.anim-formula`. Formatted as LaTeX equations:
    *   Fraction (`.frac`): Displays numerator (`.num`) above denominator (`.den`) with horizontal line (`border-bottom: 1.2px solid`).
    *   Matrix (`.matrix`): Displays linear transform cells wrapped inside bracket ticks (drawn using CSS borders and gradient ticks).

### Lens Zone
*   **Structure:** `.lens-zone` wrapper holding `.lens-overlay`, `.glass-highlight`, and `.label`.
*   **States:** Hover triggers the magnifying glass lens morphing. Click cycles through 3 loaded images.

---

## 13. States & Interaction Patterns
*   **Hover Affordance:** Standard elements transition background to `--accent-bg` (soft orange wash) or underline text in orange.
*   **Active Presses:** Brutalist elements shift by 2px (down-right), collapsing shadows to `1px 1px`.
*   **Text Selection:** Background color matches `--accent` (`#FF5C00`), and text turns white.
*   **Dynamic Loading State:**
    *   The browser locks scrolling (`overflow: hidden`) during loading.
    *   The logo text flickers through 15+ font families and bright colors.
    *   The progress bar fills to 100% with a pixelated green snake pattern.
    *   Once loaded, the logo morphs from centered position to its layout placement via a FLIP animation.

---

## 14. Accessibility
*   **Contrast Levels:** High-contrast text conforms to standards (dark charcoal text `#111111` on light gray `#EBEBEB`). Accent colors (blue `#0000CC` and orange `#FF5C00`) do not conform to AA contrast on body paragraphs, but they are limited to display numbers and border accents.
*   **Custom Cursor Impact:** Keyboard/Screen-reader focus outlines are not defined in the CSS since `cursor: none !important` is applied globally. Visual indicators depend on hover transitions.
*   **Screen Reader Control:** SVG graphs are excluded from screen readers (`aria-hidden="true"`).

---

## 15. Design Tokens Reference

| Category | Token Variable Name | Literal Value | Code Mapping |
| :--- | :--- | :--- | :--- |
| **Color** | `--bg` | `#EBEBEB` | Warm matte off-white |
| **Color** | `--text` | `#111111` | Near-black ink outline |
| **Color** | `--accent` | `#FF5C00` | Signal orange highlight |
| **Color** | `--accent-bg` | `#FFF5EF` | Soft orange card wash |
| **Color** | `--blue` | `#0000CC` | Imperial Blue |
| **Color** | `--black` | `#000000` | Pure black |
| **Color** | `--white` | `#FFFFFF` | Pure white |
| **Font** | `--serif` | `'Playfair Display', Georgia, serif` | Serif display font |
| **Font** | `--mono` | `'Consolas', 'Inconsolata', monospace` | UI/Prose Monospace |
| **Font** | `--pixel` | `'Press Start 2P', monospace` | Pixel display font |
| **Shadow** | `--kv-shadow-sm` | `3px 3px 0 0 var(--text)` | Small flat offset |
| **Shadow** | `--kv-shadow-md` | `5px 5px 0 0 var(--text)` | Hover flat offset |
| **Shadow** | `--kv-shadow-press`| `1px 1px 0 0 var(--text)` | Click flat offset |
| **Ease** | `--ease-organic` | `cubic-bezier(0.34, 1.56, 0.64, 1)`| Spring entrance |
| **Ease** | `--ease-ring` | `cubic-bezier(0.23, 1, 0.32, 1)` | Cursor lagging |
| **Duration**| `--transition` | `0.3s` | Fade switch speed |
| **Duration**| `--dur-quick` | `0.25s` | Underline transition |
| **Duration**| `--dur-reveal` | `1.2s` | Scroll reveal entry |
| **Border** | `--border` | `1.5px solid var(--text)` | Primary outlines |
| **Border** | `--border-hair` | `1px solid var(--text)` | Secondary lines |
| **Border** | `--border-dashed`| `1.5px dashed var(--text)` | Lens placeholder |
| **Radius** | `--radius` | `0` | Zero border-radius |

---

## 16. Conventions & Conflicts

### Visual and Variable Naming Inconsistencies
*   **Variable Prefix Discrepancy:** The design system configuration files (`colors_and_type.css`) use `--kv-` prefixes for tokens (e.g. `--kv-bg`). However, the actual site stylesheets (`global.css`) declare variables without the prefix (e.g. `--bg`).
*   **Hardcoded Shadow Values:** Box shadow rules in `index.css` (e.g., `box-shadow: 4px 4px 0 0 var(--text)` on `.portal-tile`) bypass the tokens specified in `colors_and_type.css` (`3px 3px` and `5px 5px`).
*   **Font Size Discrepancy:** The stat number component uses a hardcoded font size of `36px` in `index.css` but `--fz-stat: 2.8rem` (equivalent to 44.8px) in the variables root.

### Duplicate Selectors (Redundant Definitions)
*   **`index.css` (Stats):** `.hero-stats` is declared twice. Lines 36–54 and lines 96–114 contain identical properties.
*   **`index.css` (Portal):** `.portal-grid` is defined twice. The first declaration (lines 60–89) has zero grid gaps, but the second block (lines 118–156) uses `gap: 3rem` and overrides the layout.
*   **`work.css` (Capabilities):** `.capabilities` is declared twice (lines 22–29 and lines 77–82).
*   **`work.css` (Card Details):** `.project-tag`, `.project-name`, `.project-desc`, and `.project-arrow` are duplicated exactly between lines 15–19 and lines 32–36.

### Syntax and Rule Bugs
*   **Stray Brackets:**
    *   `main/css/work.css` has an extra closing brace `}` at line 30 with no matching selector.
    *   `main/css/heroplot.css` has a stray closing brace `}` at line 81.
*   **Broken Selector in `global.css`:** Lines 228–234 contain styling properties (`position: relative; top: auto; background: var(--bg)...`) but are missing their selector prefix:
    ```css
    /* Defined in css/global.css (Lines 227-235) */
    .paragraph { font-size: var(--fz-para); line-height: var(--lh-prose); opacity: 0.8; max-width: 500px; }
        position: relative;
        top: auto;
        background: var(--bg);
        color: var(--text);
        border-top: var(--border);
        border-bottom: var(--border);
    }
    ```
    This causes the properties to render incorrectly in the stylesheet and fail compilation.
*   **Unstyled Back-to-Top Button:** The `.scroll-top` button (linked to `js/scrolltop.js`) is present on every page markup file, but there are no CSS properties styling it in the codebase.
