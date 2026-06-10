# Brainwork Final Report

One to four short lines. No preamble, no postamble.

## Required fields

Include in this order:

1. **Chosen route** — one of: ingest, batch ingest, maintenance, dry run, no-op.
2. **Raw source(s) processed** — file path(s); or, if none, a one-clause reason (no pending raw / dry run / user asked maintenance).
3. **Wiki pages or support files changed** — short list of titles or paths; say `none` if no writes occurred.
4. **`tools/sb.py check` result** — `clean` or specific failure.
5. **Remaining pending work** — only if relevant; mention the count or next suggested action.

## Examples

Single ingest:

```
Route: ingest (raw/drops/2026-06-03-pricing-thoughts.md)
Created: wiki/personal/ventures/pricing-thoughts.md; updated: wiki/personal/me.md, wiki/index.md, wiki/log.md
sb check: clean
Remaining pending: 0
```

Maintenance with one fix:

```
Route: maintenance (user asked for lint)
Fixed: 1 index drift entry via sb index --write
sb check: clean
```

Dry run:

```
Route: dry run (user asked to inspect only)
Next action would be: ingest raw/drops/2026-06-03-foo.md (Personal Ingest)
No writes performed.
```

No-op:

```
Route: no-op (no pending raw; lint clean; graph healthy)
No writes performed.
```

## Style

Concise. No emojis. No "Successfully completed..." wrappers. The report is a status payload, not a celebration.
