---
name: jstack-excalidraw
description: Author beautiful, hand-drawn-style Excalidraw diagrams and export them to PNG/SVG headlessly. Use when you need to draw a clear, designed-looking visual — a flow, architecture, system, tree, sequence, or concept — anything where a picture beats text. Routes to an auto-layout pipeline (author in Mermaid, the engine places everything) and a design methodology for diagrams that visually argue, then renders + self-validates with no browser or auth.
---

# jstack-excalidraw

You need a diagram that looks **designed**, not slapped together. This skill is a router to two bundled
capabilities plus a playbook that combines them into one pipeline. Read `references/playbook.md` first;
disclose the deeper craft doc only when you need it.

## The one decision: which authoring path?

- **Auto-layout — default, fastest, cleanest.** Write the diagram in **Mermaid** (LLMs write Mermaid
  well) and let the layout engine place every box and arrow. Zero coordinate math — this is why the old
  hand-placed diagrams looked bad and these don't. Best for flows, architectures, trees, ER, sequences,
  state. → `references/playbook.md` (Auto-layout path).
- **Hand-authored — max control / visual argument.** When the picture must *argue* visually in a way
  Mermaid grammar can't express (custom composition, evidence artifacts, multi-zoom, freeform funnels),
  author the Excalidraw JSON directly using the design methodology. → read
  `references/excalidraw-diagram/SKILL.md` (the full craft doc) + `references/excalidraw-diagram/references/color-palette.md`.

Both paths render + self-validate through the **same** headless renderer. Start with auto-layout; drop
to hand-authoring only when the diagram needs to do something Mermaid can't.

## Setup (once)

The renderer + Mermaid bridge run on Python/Playwright:
```
cd references/excalidraw-diagram/references
uv sync && uv run playwright install chromium
```
One time. (`npm install` is NOT required — the bridge loads the pinned Excalidraw + Mermaid libs from
esm.sh at render time; `package.json` is only the version-of-record.)

## The pipeline (best of both worlds)

All commands run from `references/excalidraw-diagram/references`:
```
# 1. Author in Mermaid -> auto-laid-out .excalidraw   (skip if hand-authoring JSON directly)
uv run python mermaid_to_excalidraw.py <in.mmd> -o scene.excalidraw
# 2. Render -> PNG, then eyeball it
uv run python render_excalidraw.py scene.excalidraw -o scene.png
# 3. Look at scene.png; revise the Mermaid (or JSON); re-render until it matches the brief.
```
Worked example, pattern picks, styling with `classDef`, and troubleshooting: **`references/playbook.md`**.

## Progressive disclosure map

| Need | Read |
|------|------|
| Run the pipeline · worked example · pick a path · style · troubleshoot | `references/playbook.md` |
| Design craft — "diagrams argue, not display", pattern library, multi-zoom, shape/colour meaning | `references/excalidraw-diagram/SKILL.md` |
| Brand palette — single source of truth for fills, strokes, text colours | `references/excalidraw-diagram/references/color-palette.md` |
| Element JSON schema + templates (hand-authoring only) | `references/excalidraw-diagram/references/json-schema.md`, `element-templates.md` |

## Verify

A real render is a PNG well over ~10 KB; a blank canvas is tiny. Check byte size first, then open and
eyeball against the brief. Smoke test: pipe `references/smoke.mmd` through both steps → expect a
non-trivial PNG. Needs network at render time (esm.sh CDN).

## Next skills

| Next | When |
|------|------|
| /jstack-vision | Second-opinion read of the exported PNG — does it match the brief? |

Otherwise standalone.
