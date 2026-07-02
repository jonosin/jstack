# jstack-excalidraw — pipeline playbook

The best-of-both-worlds way to make a diagram that looks designed: **author the structure in Mermaid,
let the layout engine place it, render, then eyeball and iterate.** Drop to hand-authored JSON only when
the picture must argue in a way Mermaid can't.

All commands run from the skill's script dir:
```
cd references/excalidraw-diagram/references
```

---

## Path A — Auto-layout (default)

Use for: flows, pipelines, architectures, trees/hierarchies, ER diagrams, sequences, state machines —
anything with nodes and edges. The layout engine (Mermaid's dagre) does all coordinate math, so nothing
overlaps and spacing is even. This is the fix for "hand-placed boxes look bad."

**1. Write Mermaid.** LLMs are strong at this. Keep one idea per diagram; big labels; few nodes.

```
flowchart LR
  T[tools]:::src --> M{{one memory}}
  I[inbox]:::src --> M
  H[in your head]:::src --> M
  M --> O[done for you, ongoing]
  classDef src fill:#d0e8ff,stroke:#1e1e1e;
```

**2. Convert → auto-laid-out `.excalidraw`:**
```
uv run python mermaid_to_excalidraw.py scene.mmd -o scene.excalidraw   # --font-size 20 (default)
# or pipe:  echo "flowchart TD; A-->B" | uv run python mermaid_to_excalidraw.py - -o scene.excalidraw
```

**3. Render → PNG and look at it:**
```
uv run python render_excalidraw.py scene.excalidraw -o scene.png   # -s scale(2), -w maxwidth(1920)
```

**4. Iterate.** Read `scene.png`. Adjust the Mermaid (direction `TD`/`LR`, node text, grouping,
`classDef` colours) and re-run. The `.excalidraw` is fully editable afterward in the Excalidraw app or by
hand if you need one nudge.

### Styling in Mermaid
- Direction: `flowchart TD` (top-down) vs `LR` (left-right) — pick what makes the argument read.
- Colour by role with `classDef` + `:::name` (see the `src` class above). Pull real hex values from
  `references/excalidraw-diagram/references/color-palette.md` so diagrams stay on-brand.
- Node shapes carry meaning: `[]` process, `{{}}` hexagon/hub, `()` rounded, `[( )]` database, `{}` decision.
- Diagram types supported: `flowchart`, `sequenceDiagram`, `classDiagram`, `erDiagram`, `stateDiagram-v2`,
  `mindmap`, C4. If a type errors, it's usually unsupported syntax — simplify.

### Limits of Path A
Mermaid gives **correct layout, plain styling**. It won't do freeform composition, hand-annotated
callouts, evidence artifacts, or multi-zoom framing. When you need those, use Path B (you can also convert
with Path A first, then hand-edit the emitted JSON for the last 10%).

---

## Path B — Hand-authored (visual argument / max control)

Use when the diagram must *argue*, not just display: custom spatial composition, real code/data samples
shown as artifacts, one-to-many fans, multi-zoom levels, deliberate whitespace as meaning.

Read the craft doc before authoring — it is the methodology, not optional:
- `references/excalidraw-diagram/SKILL.md` — "diagrams argue, not display", the pattern library
  (fan-out, convergence, tree, cycle, assembly line, comparison), shape/colour meaning, multi-zoom.
- `references/excalidraw-diagram/references/color-palette.md` — the single colour source of truth.
- `references/excalidraw-diagram/references/json-schema.md` + `element-templates.md` — the exact element
  JSON: required fields, text-in-container, arrow binding, gotchas.

Then render + self-validate with the **same** renderer:
```
uv run python render_excalidraw.py scene.excalidraw -o scene.png
```
Loop: author JSON → render → read the PNG → fix overlaps/alignment → re-render until it matches the brief.

---

## The self-validation loop (both paths) — MANDATORY, not optional

The whole point of the renderer is that the agent *sees* its own output and corrects it before delivering.
This loop is a hard gate: **a diagram that has not passed the checklist below is not a finished diagram —
do not present it as final, and do not tell the user it's ready.**

```
brief → author (Mermaid or JSON) → render → READ the PNG against the checklist → revise → re-render →
until the checklist passes OR the iteration cap is hit
```

### Output-quality checklist (run against the actual rendered PNG, every time)

- [ ] **No overlapping elements** — no box/arrow/label sits on top of another; nothing is clipped at
      the canvas edge.
- [ ] **Labels are readable at 100% zoom** — text is not truncated, doesn't overrun its container, and
      is legible at the PNG's native size (not just "would be fine if I zoomed in").
- [ ] **Visual hierarchy matches the argument** — the thing that matters most is visually dominant
      (size/position/colour), not just first in the source order; grouping and flow direction reflect
      the actual relationships in the brief.
- [ ] **Non-trivial layout** — the diagram is not a single row/column of uniform boxes when the brief's
      structure calls for more (branching, grouping, hierarchy, zoom). A flat row is a red flag that the
      structure was under-modeled, not a valid "simple" diagram.
- [ ] **Isomorphism test** — strip the text and the structure alone still communicates the concept.

### Iteration cap

Iterate up to **3 render/read/revise cycles**. If the checklist still fails after 3 iterations, stop,
show the best version to the user, and say explicitly which checklist item(s) still fail and why
(e.g. "labels overflow their containers at this node count — needs a wider canvas or fewer nodes") —
do not silently ship a diagram that fails its own checklist, and do not loop indefinitely.

Never deliver a diagram you haven't rendered, read, and checked against this list.

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `modules failed to load from esm.sh` / timeout | Network needed at render time. Retry (esm.sh cold-builds the bundle on first hit); confirm connectivity. |
| Mermaid `parse failed` | Unsupported/invalid Mermaid syntax. Simplify; test the snippet at mermaid.live. |
| Tiny PNG (<10 KB) | Empty/blank canvas — the scene had no visible elements. Check the `.excalidraw` `elements` array. |
| `Chromium not installed` | Run setup once: `uv sync && uv run playwright install chromium`. |
| Want a local (offline) lib pin | `npm install` in this dir installs the exact versions in `package.json`; the scripts still default to esm.sh. |

## Quick reference

```
# one-shot: mermaid file -> png
uv run python mermaid_to_excalidraw.py in.mmd -o s.excalidraw && \
uv run python render_excalidraw.py s.excalidraw -o s.png
```
