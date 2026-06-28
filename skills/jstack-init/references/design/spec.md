# DESIGN.md Format Specification

Source of truth: `google-labs-code/design.md` (Apache-2.0), CLI v0.3.0.

## What it is

DESIGN.md is a single file that combines YAML frontmatter (machine-readable design tokens) with Markdown body (human-readable rationale). Coding agents read it to produce on-brand UI without you restating the palette.

The CLI (`npx @google/design.md`) lints structure and WCAG contrast, diffs versions for regressions, and exports tokens to Tailwind or W3C DTCG JSON.

## Token types

| Type | Format | Example |
|------|--------|---------|
| Color | Any valid CSS color, hex preferred | `"#1A1C1E"`, `"oklch(62% 0.18 250)"` |
| Dimension | number + unit (`px`, `em`, `rem`) | `48px`, `"-0.02em"` |
| Token reference | `{path.to.token}` | `{colors.primary}` |
| Typography | object with `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, `letterSpacing`, `fontFeature`, `fontVariation` | see template |

Component property whitelist: `backgroundColor`, `textColor`, `typography`, `rounded`, `padding`, `size`, `height`, `width`.

Variants (hover, active, pressed) are **separate component entries** with related key names (`button-primary-hover`), never nested.

## Canonical section order

Sections use `##` headings and present ones MUST appear in this order. Duplicate headings reject the file. Unknown sections are preserved, not errored.

1. Overview (alias: Brand & Style)
2. Colors
3. Typography
4. Layout (alias: Layout & Spacing)
5. Elevation & Depth (alias: Elevation)
6. Shapes
7. Components
8. Do's and Don'ts
