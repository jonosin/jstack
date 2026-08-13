# Lint rules & CLI reference

CLI: `npx @google/design.md` (Node, v0.3.0). All commands accept `-` for stdin. `lint` exits 1 on errors.

## Commands

```bash
# Validate structure + token references + WCAG contrast
npx -y @google/design.md lint DESIGN.md

# Compare two versions, fail on regression (exit 1 = regression)
npx -y @google/design.md diff DESIGN.md DESIGN-v2.md

# Export to Tailwind v3 theme JSON
npx -y @google/design.md export --format tailwind DESIGN.md > tailwind.theme.json

# Export to Tailwind v4 CSS custom properties (@theme block)
npx -y @google/design.md export --format css-tailwind DESIGN.md > tailwind.css

# Export to W3C DTCG (Design Tokens Format Module) JSON
npx -y @google/design.md export --format dtcg DESIGN.md > tokens.json

# Print the spec rules as JSON — useful for injecting into an agent prompt
npx -y @google/design.md spec --rules-only --format json
```

## 9 active lint rules

| Rule | Severity | What it checks |
|------|----------|----------------|
| `broken-ref` | Error | Broken/circular token references and unknown component sub-tokens |
| `missing-primary` | Warning | Colors defined but no `primary` token (agents will auto-generate) |
| `contrast-ratio` | Warning | Component `backgroundColor`/`textColor` below WCAG AA 4.5:1 |
| `orphaned-tokens` | Warning | Color tokens defined but never referenced by any component |
| `missing-typography` | Warning | Colors defined but no typography tokens (agents use defaults) |
| `section-order` | Warning | Sections out of canonical order |
| `unknown-key` | Warning | Top-level YAML keys that look like typos (e.g. `colours:` → `colors:`) |
| `token-summary` | Info | Count of tokens per section |
| `missing-sections` | Info | Optional sections absent when related tokens exist |

Accessibility is the most load-bearing reason to lint — `contrast-ratio` catches buttons and text that real users can't read.
