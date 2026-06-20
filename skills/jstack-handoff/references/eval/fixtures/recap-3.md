# Session transcript — design token migration

User: We're moving our CSS from hardcoded hex values to design tokens. Help me migrate.

Assistant: Surveyed the styles. Components live under `src/components/**/*.module.css`. There are 47 distinct hex colors across 31 files. The token source of truth should be `src/styles/tokens.css` (currently empty placeholder).

User: Group the colors first.

Assistant: Clustered the 47 hexes into 12 semantic tokens: `--color-bg`, `--color-bg-subtle`, `--color-fg`, `--color-fg-muted`, `--color-accent`, `--color-accent-hover`, `--color-border`, `--color-danger`, `--color-success`, `--color-warning`, `--color-overlay`, `--color-focus-ring`. Wrote the mapping table to `docs/token-migration.md` (hex → token, with which files use each).

Assistant: Populated `src/styles/tokens.css` with the 12 tokens under `:root`, plus a `[data-theme="dark"]` block (dark values still PLACEHOLDER — need design review).

User: Start replacing.

Assistant: Migrated 8 of 31 files so far (`Button`, `Card`, `Input`, `Modal`, `Badge`, `Tooltip`, `Alert`, `Tabs`) — replaced raw hex with `var(--color-*)`. STILL TODO: 23 remaining files (list in `docs/token-migration.md`), fill in dark-theme values, then delete the now-unused hex constants in `src/styles/legacy-colors.css`. Visual regression not yet run.

User: Out of time, let's continue next session.
