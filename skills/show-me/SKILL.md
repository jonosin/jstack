---
name: show-me
description: Help the user understand the current topic visually. Use when the user asks to show how something works, see a flow, compare states, or make a concept easier to understand.
---

# show-me

Help the user understand the current topic of conversation visually. Skip the preamble and keep prose
brief. Pick the smallest view that makes the key point clear.

- Show component interaction, control flow, or data flow with Mermaid.
- Use a diff when the point is what changes and the surrounding shape already exists. Match the diff
  shape to the topic.

  ```diff
   src/
   ├── commands/
  +│   └── show-me.ts       # expands the slash command
   ├── sessions/
  -└── transport.ts
  +└── transport/
  - ├── client.ts
  - └── stream.ts
  ```
- For a visual UI, layout, state comparison, or concept too dense for Mermaid, write one focused HTML
  file: a diagram, infographic, or short slide deck. Match the product's colors, type, spacing, and
  components; use real labels and data; support desktop and mobile. Then open it for the user with
  `open path/to/show-me-[description].html`.
- Place each visual next to the short text it supports. Keep only the calls, files, props, states, and
  boundaries needed to answer the current question.

## Next skills

| Next | When |
|------|------|
| `asciiexplain` | The user needs a terminal-safe text diagram. |

## Gotchas

Use a visual only when it makes the current point easier to understand than brief prose.
