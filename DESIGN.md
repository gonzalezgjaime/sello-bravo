---
name: Sello Bravo
description: Letterpress-dark brand system — copper ink and bone paper for a Mexican POD merch brand
colors:
  cobre: "#C0492C"
  tinta: "#1B1714"
  tinta-profunda: "#10100E"
  fondo-hondo: "#0A0A09"
  hueso: "#F3EADB"
  nopal: "#2F5D50"
  ambar: "#E2A53C"
  ambar-oscuro: "#9A6A10"
  rosa: "#D2326B"
typography:
  display:
    fontFamily: "'Bebas Neue', Impact, 'Arial Narrow', sans-serif"
    fontSize: "clamp(56px, 8vw, 108px)"
    fontWeight: 400
    lineHeight: 0.87
    letterSpacing: "0.02em"
  headline:
    fontFamily: "'Bebas Neue', Impact, 'Arial Narrow', sans-serif"
    fontSize: "clamp(36px, 6vw, 68px)"
    fontWeight: 400
    lineHeight: 0.88
    letterSpacing: "0.04em"
  title:
    fontFamily: "'Bebas Neue', Impact, 'Arial Narrow', sans-serif"
    fontSize: "24px"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0.06em"
  body:
    fontFamily: "'Bitter', Georgia, serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.7
  label:
    fontFamily: "'Special Elite', Courier, monospace"
    fontSize: "11px"
    fontWeight: 400
    letterSpacing: "0.14em"
rounded:
  sharp: "0px"
  chip: "2px"
  dot: "50%"
spacing:
  chip: "3px 8px"
  cta: "6px 14px"
  badge: "10px 18px"
  link: "16px 32px"
  card: "28px 26px 22px"
  gutter: "40px"
  section: "64px"
components:
  button-cta:
    backgroundColor: "transparent"
    textColor: "{colors.cobre}"
    rounded: "{rounded.sharp}"
    padding: "{spacing.cta}"
  button-cta-hover:
    backgroundColor: "{colors.cobre}"
    textColor: "{colors.tinta-profunda}"
  store-link:
    backgroundColor: "transparent"
    textColor: "{colors.hueso}"
    rounded: "{rounded.sharp}"
    padding: "{spacing.link}"
  store-link-hover:
    textColor: "{colors.cobre}"
  card-product:
    backgroundColor: "{colors.hueso}"
    textColor: "{colors.tinta-profunda}"
    rounded: "{rounded.sharp}"
    padding: "{spacing.card}"
  tag-evergreen:
    backgroundColor: "#2F5D501F"
    textColor: "{colors.nopal}"
    rounded: "{rounded.chip}"
    padding: "{spacing.chip}"
  tag-seasonal:
    backgroundColor: "#E2A53C1F"
    textColor: "{colors.ambar-oscuro}"
    rounded: "{rounded.chip}"
    padding: "{spacing.chip}"
---

# Design System: Sello Bravo

## 1. Overview

**Creative North Star: "La Imprenta de Noche"**

A letterpress workshop after dark. Copper ink under a work lamp, bone paper on
the bench, ledger lines ruled across the ground, film grain in the air. Every
surface behaves like a print artifact: the seal comes down, the ink bites, the
edge stays sharp. The shipping site (sellobravo.com) is the workshop at night —
near-black ground (`#10100E`), copper (`#C0492C`) doing all the talking, bone
(`#F3EADB`) as both paper and voice. The products that leave the workshop are
the daylight side: bold ink on bone or white garments.

**This is a two-track system, by explicit decision.** Track one is the **web
system** (this file's frontmatter): Bebas Neue display + Special Elite labels +
Bitter body on the dark ground — what ships at sellobravo.com. Track two is the
**print system** for product art (playeras, tazas, prints): Anton display +
Oswald labels, Tinta ink `#1B1714` on Hueso/white, specified in
`brand/brand-guide.md` and `brand/designs/catalog.md`. The two tracks share the
palette, the seal devices, and the voice; they never swap typefaces. A web page
set in Anton or a shirt set in Bebas Neue is a system violation, not a variant.

The system explicitly rejects (from PRODUCT.md): touristy-kitsch and the
flag-cliché, green-white-red as a palette shortcut, corporate filler, sad-beige
minimalism, and generic AI landing-page grammar. Warmth is carried by copper,
paper texture, and Spanish-first copy — never by defaulting to cream
backgrounds or folkloric costume.

**Key Characteristics:**
- Dark letterpress ground; copper is the single loud voice (Committed strategy)
- Everything sharp-cornered; the only radii are 2px chips and round dots
- Material depth (grain, paper noise, copper hairlines), not shadow depth
- Typewriter metadata voice (Special Elite) against condensed display shouting (Bebas Neue)
- The press-die lockup and 8-leaf maguey star recur as nav icon, watermark, and footer mark
- Two tracks, one brand: web (Bebas/Special Elite) and print (Anton/Oswald), never mixed

## 2. Colors

A committed copper-on-dark palette: two inks, one paper, three controlled accents.

### Primary
- **Cobre** (`#C0492C`): the brand's voice. Logo marks, accent heading lines,
  section labels, CTA text and hover fills, and every hairline border via
  `rgba(192,73,44, α)` — α 0.04 for ledger lines, 0.10–0.18 for hairlines,
  0.28 for the hero glow, 0.4 for CTA outlines. The only hex identical across
  every surface in the repo. Never gradiated, never shadowed.

### Secondary
- **Tinta** (`#1B1714`): print ink. Type and line art on product designs;
  ink-on-paper text on light cards via `rgba(27,23,20, α)`. Print-track only
  as a surface color.
- **Tinta Profunda** (`#10100E`): the web dark ground and logo dark-tile fill.
  The page background of the shipping site.
- **Fondo Hondo** (`#0A0A09`): deepest dark — fixed nav (`rgba(10,10,9,0.9)`
  with blur), alternate sections, drawers, toasts.

### Tertiary
- **Nopal** (`#2F5D50`): evergreen tag text on its own 12% tint; secondary art
  balance in print designs.
- **Ámbar** (`#E2A53C`): fills and graphics only — seasonal tag tint
  backgrounds (12–15%), fiesta warmth in print art. Not for text.
- **Ámbar Oscuro** (`#9A6A10`): the accessible text partner for Ámbar — all
  seasonal/amber text on tinted or light backgrounds uses this, never raw
  Ámbar and never the deprecated `#B07D20`.
- **Rosa Mexicano** (`#D2326B`): print-side pop (quinceañera and mamá lines,
  "Personalizable" badges), ≤10% of any design. Currently absent from the web
  track by design; introducing it there is a deliberate decision, not a default.

### Neutral
- **Hueso** (`#F3EADB`): paper. Primary text on dark grounds, product-card and
  mockup backgrounds, the light-garment canvas. Muted text is always a
  transparency of Hueso, never a gray: `rgba(243,234,219, α)`.

### Named Rules
**The Two Inks Rule.** Tinta `#1B1714` is print ink; Tinta Profunda `#10100E`
is the web ground. They are different tokens with different jobs. Never swap
them, never invent a third near-black (`#12100E` is dead; `--bone` and `--mid`
are dead tokens — delete on sight).

**The Copper Hairline Rule.** Structure on the dark ground is drawn with 1px
copper transparencies (`rgba(192,73,44, 0.10–0.18)`), not gray borders, not
box shadows.

**The Legible Alpha Rule.** On `#10100E`, Hueso alphas below **0.55** fail AA
for body-size text (0.42 computes to ~3.6:1, 0.2 to ~1.7:1). Text that must be
read uses α ≥ 0.58; alphas 0.14–0.45 are reserved for decorative/duplicated
content only. Same discipline for ink-on-paper: `rgba(27,23,20, α)` text
uses α ≥ 0.62.

## 3. Typography

**Display Font (web):** Bebas Neue (with Impact, 'Arial Narrow' fallbacks)
**Label Font (web):** Special Elite (with Courier fallback)
**Body Font (both tracks):** Bitter (with Georgia fallback) — 400/600 + italic
**Display Font (print):** Anton · **Label Font (print):** Oswald

**Character:** a condensed shout against a typewriter whisper, mediated by a
warm slab serif. Bebas Neue compresses to line-heights below 0.9 like stacked
wood type; Special Elite carries the workshop's metadata voice — uppercase,
wide-tracked, small; Bitter is the only font allowed to speak in sentences.

### Hierarchy
- **Display** (400, `clamp(56px, 8vw, 108px)`, 0.87): hero headline only. The
  second line takes Cobre.
- **Headline** (400, `clamp(36px, 6vw, 68px)`, 0.88): section headings, store
  CTA headings, card art text (`clamp(32px, 4.5vw, 48px)` at 0.86).
- **Title** (400, 20–24px, letter-spacing 0.04–0.06em): wordmark (20px nav /
  24px footer), store links, swatch names.
- **Body** (400, 16.5–17px, 1.7–1.75): Bitter prose; max width ~44rem (~70ch).
- **Label** (400, 11px canonical, tracking 0.14em; eyebrows 0.28em): Special
  Elite, uppercase. Tags may compress to 10px; nothing text-bearing below that.

### Named Rules
**The Two Voices Rule.** Bebas Neue shouts on the web; Anton shouts on
garments. Special Elite labels the web; Oswald labels the seal and print art.
Bitter is the only shared voice. Mixing tracks on one surface is forbidden.

**The Outlined Type Rule.** No live `<text>` in distributed SVG. Every logo or
design SVG that leaves the repo has its type converted to paths (web marks
from Bebas Neue, print art from Anton). Impact appearing in a rendered asset
means this rule was broken.

**The Thumbnail Rule.** Every composition must survive shrinking to a
marketplace thumbnail: one dominant element, line-heights tight, hierarchy
readable at 120px wide.

## 4. Elevation

Ink, not air. Surfaces are flat at rest; depth is **material**, conveyed by
film grain (fixed `feTurbulence` overlay at 0.045 opacity, `mix-blend-mode:
screen`), paper noise on cards (0.03), ledger lines (1px copper at 0.04 every
56px), and copper hairline borders. Shadows exist only as a **response to
state**, never at rest.

### Shadow Vocabulary
- **Card lift** (`box-shadow: 0 12px 32px -12px rgba(0,0,0,0.5)` +
  `translateY(-3px)`): product card hover only.
- **Copper glow** (`filter: drop-shadow(0 0 50px rgba(192,73,44,0.28))`): the
  hero press-die mark only — lamplight on metal, not UI elevation.

### Named Rules
**The Ink, Not Air Rule.** If a surface needs to feel distinct at rest, give
it texture, a hairline, or a different ground color — never a resting shadow.

## 5. Components

Stamped and confident: sharp corners, hairline outlines that invert to solid
copper on interaction, typewriter labels. Every interactive element needs a
designed `:focus-visible` state (2px Cobre outline, 3px offset) — the shipped
pages predate this rule and owe it.

### Buttons
- **Shape:** sharp (0px radius), always.
- **CTA (nav):** transparent, Cobre text, 1px `rgba(192,73,44,0.4)` border,
  6px 14px, Special Elite 11px uppercase 0.14em.
- **Hover:** inverts — solid Cobre fill, Tinta Profunda text. The press comes down.
- **Store link (large):** Bebas Neue 22px, 16px 32px, 1.5px
  `rgba(243,234,219,0.14)` border, pulsing 8px copper dot; border and text turn
  Cobre on hover.

### Chips
- **Style:** Special Elite 9–10px uppercase, 0.1–0.2em tracking, 3px 8px,
  2px radius — the only rounded corners in the system.
- **Variants:** evergreen (Nopal text on `#2F5D501F`), seasonal (Ámbar Oscuro
  text on `#E2A53C1F`).

### Cards / Containers
- **Corner Style:** sharp (0px).
- **Background:** Hueso paper on the dark ground, with fractal paper noise at
  0.03 opacity; text in Tinta Profunda / `rgba(27,23,20, α)`.
- **Shadow Strategy:** flat at rest; hover lift per Elevation.
- **Border:** internal hairlines `rgba(27,23,20,0.08)`; the card foot carries a
  28px maguey watermark at 0.15 opacity.
- **Internal Padding:** 28px 26px 22px.

### Navigation
- **Style:** fixed 58px bar, `rgba(10,10,9,0.9)` + 12px blur, copper hairline
  bottom border. Wordmark (Bebas 20px) + maguey star left; Special Elite 11px
  uppercase links right, muted (`rgba(243,234,219,0.42)` — decorative-tier;
  bump to ≥0.58 when links carry sole navigation). Non-CTA links hide under 600px.

### Section Header (signature)
Copper Special Elite label (10.5px, 0.28em tracking) beside a 1px copper rule
(max 120px), then the Bebas headline. This is the system's one deliberate
kicker device — it replaces, and forbids, generic eyebrows on every block.

### The Press-Die Lockup & Maguey Star (signature)
The primary web mark: double cut-corner border (6px + 1.8px strokes) with
corner registration ticks, SELLO/BRAVO lettering, diamond-and-rule dividers,
optionally distorted by the `#ink-press` SVG filter (feTurbulence 0.03 +
feDisplacementMap scale 5). The 8-leaf maguey star (center-dot opacity 0.45)
recurs as nav icon, card watermark, and footer mark. The circular seal
(`logo/sello-bravo-seal.svg`) is the print-track rubber stamp for product art
and packaging.

## 6. Do's and Don'ts

### Do:
- **Do** carry all structure on the dark ground with copper hairlines
  (`rgba(192,73,44, 0.10–0.18)`) and material texture — grain, paper noise,
  ledger lines.
- **Do** keep text-bearing Hueso alphas ≥ 0.58 on `#10100E` (The Legible Alpha
  Rule) and use Ámbar Oscuro `#9A6A10` for any amber text.
- **Do** ship a `prefers-reduced-motion: reduce` alternative for every
  animation (pulse dots, press-in entrances, drawer slides, smooth scroll) —
  and a designed `:focus-visible` state on every interactive element. The
  existing pages owe this debt; new work never adds to it.
- **Do** outline all SVG type to paths before an asset leaves the repo (web
  marks in Bebas Neue, print art in Anton).
- **Do** keep the two tracks pure: Bebas Neue + Special Elite on web surfaces;
  Anton + Oswald on product art; Bitter for prose everywhere.
- **Do** write copy Spanish-first, short and witty, and alt text in brand
  voice, in Spanish.

### Don't:
- **Don't** reach for touristy-kitsch or the flag-cliché — no sombreros, no
  serape gradients, no green-white-red palette shortcuts, no "auténtico
  mexicano™" tropes (PRODUCT.md anti-references, verbatim).
- **Don't** drift into sad-beige minimalism: warmth comes from copper, paper
  texture, and voice — never from a cream body background or gray-on-gray
  restraint.
- **Don't** use generic AI landing-page grammar: uniform icon-card grids, a
  tracked uppercase eyebrow above every section (the section-header device is
  the one licensed kicker), gradient text, hero-metric blocks, or side-stripe
  borders.
- **Don't** invent near-blacks or resurrect dead tokens: `#12100E`, `--bone`,
  `--mid`, and `#B07D20` are retired; the only darks are Tinta `#1B1714`
  (print), Tinta Profunda `#10100E` (web), and Fondo Hondo `#0A0A09`.
- **Don't** round corners beyond the 2px chip radius, add resting shadows, or
  gradiate/shadow the Cobre marks (brand guide: seal is one-color by design).
- **Don't** ship a web surface in Anton/Oswald or product art in Bebas
  Neue/Special Elite — if the store page goes live, it is retrofitted to the
  web track first (Bebas Neue display, Special Elite labels, 58px nav).
- **Don't** put live `<text>` in distributed SVGs — Impact leaking into
  rendered assets is the tell that type wasn't outlined.
