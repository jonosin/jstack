---
name: asciiexplain
description: Explain a topic with a terminal-safe ASCII diagram and short legend. Use for “explain this with ASCII” or when the user requests a text diagram of a process, system, architecture, relationship, or idea.
---

# asciiexplain — explain a concept with ASCII

Resolve the topic. If it is clear from the request or recent conversation, proceed. Otherwise ask:
“What should I explain?”

Choose the smallest diagram shape from [drawing routes](references/drawing-routes.md). Then draw the
explanation directly and add a short legend. This skill does not load a general ASCII-art skill.

## Output contract (terminal-safe)

- **Always draw.** Every answer contains an actual rendered diagram built from lines / boxes / shapes
  (box-drawing / block / geometric Unicode). Never prose-only, never plain text bullets — if there is a
  topic, there is a drawing, then its legend.
- Monospace only; box-drawing / block / geometric Unicode palette.
- **≤ ~72 chars wide.** Banners ≤ 15 lines; **each scene ≤ 25 lines** — the cap bounds one *picture*,
  NOT the whole answer.
- **Decompose, don't truncate.** A topic too dense for one 25-line scene splits into multiple labeled
  panels (`Part 1 / Part 2`, or grouped stages), each its own ≤25-line diagram + legend. Never crush
  detail to fit; never overflow a single scene past the cap.
- Diagram first, then a short legend. Label nodes/edges so each glyph maps to a named idea.
- Keep it generic — no hardcoded domain assumptions; adapt the shape to the topic.

## Next skills

| Next | When |
|------|------|
| `/focus` | The legend ran long — tighten the explanation to its essentials. |

## Gotchas

Keep each scene small enough to read without horizontal scrolling. Use labelled panels for dense topics.
