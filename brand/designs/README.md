# Sello Bravo — design assets

- **`catalog.md`** — the launch design batch: 8 concepts with sales-ready ES copy,
  visual direction, production order, and POD specs. *(The source of truth.)*
- **`*.svg`** — **concept drafts** auto-generated per design. Each was flagged
  `revise` by the art-director pass: SVG `<text>` clips when the exact font isn't
  installed on the renderer. Treat them as layout/emblem starting points. For
  **final print art**: outline or embed the **Anton** font (or force-fit each line
  with `textLength` + `lengthAdjust="spacingAndGlyphs"`) at the spec size, then
  export a **transparent PNG @ 300 DPI** per `../brand-guide.md` → POD specs.
- **`../sello-bravo-brand.html`** — the **brand showcase** (open in a browser):
  logo, palette, typography, and all 8 designs rendered cleanly with the real
  fonts. This is the intended look.

Validate niche priority with the analyzer (`market-report.md`) before mass-producing.
