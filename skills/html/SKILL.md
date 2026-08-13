---
name: html
description: Fast deterministic single-file HTML docs and optional Chrome PDF/PNG rendering for agent reports, one-pagers, dashboards, client deliverables, briefs, comparison tables, and visual information artifacts. Use when an agent needs a repeatable on-brand HTML document quickly, not a creative frontend exploration or full web app.
---

# html

Use this skill when the deliverable is a polished static document: a one-pager, report, client brief, comparison, dashboard snapshot, invoice-like summary, or internal decision artifact.

Do not use it for exploratory UI design, interactive apps, React builds, or novelty visuals. Use `frontend-design` for creative web work and `ui-ux-pro-max` for broad design exploration.

## Operating rule

Determinism beats originality. Same input should produce the same layout, spacing, colors, and export shape. Fill the JSON schema, render it, verify the file exists, then give Jono the artifact path.

## Fast path

Create a JSON file in the working project, usually `doc.json`, using this shape:

```json
{
  "title": "Decision Brief",
  "eyebrow": "Facet Creatives",
  "dek": "One sentence that explains why this document exists.",
  "meta": ["client-ready", "2026-06-23"],
  "density": "normal",
  "sections": [
    {"type": "text", "title": "Recommendation", "lead": "Say the answer first.", "items": ["Point one", "Point two"]},
    {"type": "cards", "title": "Options", "cards": [{"title": "A", "metric": "01", "metric_label": "rank", "text": "Why it matters."}]},
    {"type": "table", "title": "Comparison", "rows": [{"Option": "A", "Fit": "High"}]},
    {"type": "callout", "title": "Risk", "text": "What can go wrong."}
  ]
}
```

Render HTML:

```bash
python3 <skill-dir>/scripts/fast_html.py doc.json --out out.html
```

Render PDF or PNG when the user needs a sendable artifact:

```bash
python3 <skill-dir>/scripts/fast_html.py doc.json --format pdf --out out.pdf
python3 <skill-dir>/scripts/fast_html.py doc.json --format png --out out.png --window-size 1200,1600
```

`fast_html.py` uses only Python stdlib plus local Chrome/Chromium/Brave/Edge for PDF/PNG. HTML output has no runtime dependencies because CSS is inlined.

## Section types

`text` supports `kicker`, `title`, `lead`, `text`, `items`, and `ordered`.

`cards` supports `cards`, where each card may include `kicker`, `title`, `metric`, `metric_label`, `text`, and `items`. Three cards automatically use thirds.

`table` accepts `rows` as an array of objects. Keys become columns in first-row order.

`quote` accepts `text` and renders it as a pull quote.

`callout` accepts `text`; set `tone: "danger"` for red-left-border warnings.

Inline formatting is intentionally tiny: `**bold**` and `` `code` `` only. If you need rich Markdown, generate the HTML yourself inside a `text` section or use a heavier document pipeline.

## Style contract

The bundled style is editorial, restrained, and on-brand for Jono's fast deliverables: warm canvas, serif headline, mono labels, brass accent, soft cards, print-safe CSS. Do not re-theme per task unless the user asks. If you must vary, change JSON content first, CSS second.

The source pattern comes from:

- `~/ventures/stayframe/clients/serenity-sands/athar-onepager-site/`
- `~/jstack-sf/tools/invoice.py`
- `~/jstack-sf/skills/jstack-sf-caption/`

For prior-art notes, read `references/research-shortlist.md`.

## Verification

After rendering, run at least one of these:

```bash
python3 <skill-dir>/scripts/test_fast_html.py
python3 <skill-dir>/scripts/fast_html.py <json> --out /tmp/check.html
```

For PDF/PNG, verify the file exists and is non-empty. If Chrome rendering fails, still deliver the HTML and state the Chrome blocker directly.

## Local preview

Never open the rendered HTML via a `file://` URL — it is blocked in the sandbox. Serve it deterministically instead:

```bash
PORT="${JSTACK_PREVIEW_PORT:-8931}"   # resolution: env var → ~/.jstack/config.env → 8931 default
python3 -m http.server "$PORT" --directory "$(dirname out.html)" >/tmp/preview.log 2>&1 &
SERVER_PID=$!
# navigate to http://localhost:$PORT/$(basename out.html) and capture the screenshot
kill "$SERVER_PID"
```

Screenshots go to the session's scratch directory (always allowed inside the sandbox), then get moved to the deliverable path if the task needs them there. Kill the server every time — do not leave it running past the capture.

## Next skills

| Next | When |
|------|------|
| `frontend-design` | The user wants a distinctive creative page, app, React component, or interactive UI instead of a deterministic doc. |
| `pdf` | The HTML/PDF artifact needs further PDF manipulation, merging, OCR, or document-specific processing. |
| `skillify` | A repeated doc subtype emerges and should be hardened into a narrower deterministic script. |

Otherwise standalone — render the file and ship it.
