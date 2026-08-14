---
name: show-me
description: Help the user understand the current topic visually. Use when the user asks to show how something works, see a flow, compare states, or make a concept easier to understand.
---

# show-me

Help the user understand the current topic of conversation visually. Skip the preamble and keep prose
brief. Pick the smallest view that makes the key point clear.

- Show logic or an algorithm as pseudocode.
- Show runtime control flow as a call tree.
- Show UI structure as a component tree. Include only the state and module boundaries that matter.
- Show file responsibility or a broad refactor as a shallow file tree.
- Show component interaction, control flow, or data flow with Mermaid.
- Show the whole relevant block when most of it is new, when omitted context hides ownership or order,
  or when the user needs a copyable target shape.
- For a visual UI, layout, state comparison, or concept too dense for Mermaid, write one focused HTML
  file: a diagram, infographic, or short slide deck. Match the product's colors, type, spacing, and
  components. Use real labels and data. Support desktop and mobile. Then open it for the user with
  `open path/to/show-me-[description].html`.

Place each visual next to the short text it supports. Keep only the calls, files, props, states, and
boundaries needed to answer the current question. Use one or more views as needed, but do not
overwhelm the user.

## Next skills

| Next | When |
|------|------|
| `asciiexplain` | The user needs a terminal-safe text diagram. |

## Gotchas

Use a visual only when it makes the current point easier to understand than brief prose.
