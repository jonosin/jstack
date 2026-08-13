# ASCII drawing routes

Use one shape. Keep the labels that answer the current question.

| Need | Shape |
|---|---|
| Ordered steps or transformation | Flow: `[input] → [step] → [result]` |
| Two or more actors exchange messages | Sequence: vertical lanes with horizontal arrows |
| Components and their links | Architecture: labelled boxes and arrows |
| Parent-child ownership | Tree: `├──` and `└──` branches |
| State changes | State machine: `[state] → [state]`, with transition labels |
| Comparison | Two aligned columns; use the same rows on both sides |
| Cycle | A compact loop with each stage labelled |

Use Unicode box drawing where it improves reading: `┌ ┐ └ ┘ │ ─ ├ ┤ ┬ ┴ ┼` and arrows such as `→` and
`↓`. Start with the diagram. Follow it with one to three lines that name the parts or the direction of
flow. Split a dense topic into labelled panels instead of shrinking labels or exceeding one scene.
