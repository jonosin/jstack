---
name: jstack-asciiexplain
description: Explain any concept with a visual ASCII diagram plus a short labelled legend. Use when Jono says /jstack-asciiexplain, "explain this with ascii", "draw/diagram/visualize X", "show me how X works", "give me a visual of X", or wants a terminal-safe picture of a process, system, architecture, relationship, or idea. Composes the ascii-art skill for the rendering craft; this skill owns topic resolution + the explain-with-a-picture intent. Generic and domain-agnostic — code, systems, processes, math, anything.
---

# jstack-asciiexplain — explain a concept with ASCII

A thin orchestration layer: **resolve a topic → pick the right `ascii-art` tool → emit a diagram + a
terse legend that makes the concept legible.** This skill does NOT render art itself — it routes the
craft to `/ascii-art` and owns the *explain-with-a-picture* intent. Generic; works for any subject.

## Flow

1. **Resolve the topic.**
   - **Arg present** → topic = the arg. Proceed.
   - **No arg** → infer-or-ask. If the session has an obvious recent subject, propose it in one line
     ("Explain `<X>`? Or tell me what.") and proceed on confirm. If nothing obvious, ask one line:
     "What should I explain?" Then proceed.
2. **Pick the art form** via the `/ascii-art` **Decision Flow** (load that skill for the palette +
   tool details — never copy its tool list here):
   - **concept / flow / process / architecture / relationship** → custom Unicode box-drawing diagram
     (ascii-art Tool 9 palette: box-drawing + block + geometric glyphs). This is the default and the
     most common path for explaining how something works.
   - **a title / banner header** for the explanation → pyfiglet (Tool 1), or asciified API if not installed.
   - **a framed callout** (wrap a definition/summary in a border) → boxes (Tool 4).
   - **user supplied an image** to explain → image-to-ascii (Tool 6).
3. **Emit diagram + legend.** Output the art, then **1-3 lines of labels/legend** that name the parts
   and the flow. The picture carries the structure; the legend makes it readable. Never dump raw art
   with no explanation — this is an *explanation* skill. **If the topic won't fit one ≤25-line scene,
   split it into multiple labeled panels** (each a diagram + legend) rather than truncating or
   overflowing — see the Output contract.

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

## Tiny illustration

`/jstack-asciiexplain TCP handshake` →

```
   Client                         Server
     │                               │
     │ ───────  SYN  ───────────────▶│   1. open: client proposes
     │                               │
     │◀────── SYN-ACK ───────────────│   2. server acks + proposes
     │                               │
     │ ─────── ACK  ────────────────▶│   3. client acks → connected
     │                               │
     ▼                               ▼
```

Legend: vertical lines = each side's timeline; arrows = packets in order; after step 3 the connection
is established (both sides synced sequence numbers).

## Next skills

| Next | When |
|------|------|
| `/ascii-art` | Want raw art (a banner, a specific object, an image-to-ascii) without the explain-it wrapper. |
| `/jstack-focus` | The legend ran long — tighten the explanation to its essentials. |
