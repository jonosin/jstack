# Inline visuals

Use this reference only when an in-conversation HTML visual materially improves understanding. This
is the small `visualize` wrapper; load the full `visualize` skill only when this reference cannot
cover the requested visual.

1. Use Mermaid for a static structure that labeled nodes and edges explain completely. Return a normal
   Mermaid fence and do not create an HTML file.
2. Use one focused HTML fragment for dynamics, spatial relationships, adjustable inputs, visual UI,
   or a concept that Mermaid cannot explain clearly.
3. Write the fragment to an explicitly writable, durable, task-owned location outside the checked-out
   repository. Use a concise lowercase-hyphenated filename.
4. Keep the fragment focused. Include only the labels, values, controls, and accessible text needed
   for the point. Use real data and support desktop and mobile widths.
5. Use semantic markup and native controls. Keep controls local to the visual. Do not fetch data or
   make network calls from the fragment.
6. In the final response, put the required visualize content reference for the absolute fragment path
   where the visual should appear: `visualize{"path":"/absolute/path/title.html"}`.
7. Keep prose brief. State only what the visual helps the user see or decide.
