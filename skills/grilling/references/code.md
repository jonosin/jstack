# Code grilling

Use this branch for a codebase change, architecture decision, or domain-modeling work.

## Canonical artifacts

- `CONTEXT.md` holds durable domain vocabulary only. If it is absent, create it with `# Context`
  before adding the first term. Add a term when its meaning is specific to this codebase and it will
  improve later reasoning or naming.
- `docs/strategy/YYYY-MM-DD-<self-explanatory-decision>.md` holds local technical decisions and
  architecture/design rationale. Use `type: architecture` for a genuine architecture decision.
  Create one only when a future maintainer would otherwise ask why the code has this shape.
- For multi-session delivery, `/to-spec` creates the canonical execution destination. Do not
  create a duplicate pointer doc. Do not turn `CONTEXT.md` or a decision record into a file-by-file
  implementation plan.

## Frontier rounds

1. Read `CONTEXT.md`, relevant ADRs, and the code before asking any question the repository can answer.
2. Build the decision tree. Invoke the host's structured user-input tool with every independent
   frontier question in one round, leading with the recommended answer. Do not render the questions
   as an inline numbered chat list.
3. After the structured response, update terms and qualifying strategy artifacts immediately. Recompute the frontier.
4. Stop when no decision remains, the user says to ship, or remaining questions are explicitly deferred.

## Closeout

State the resulting outcome, `CONTEXT.md` terms, strategy artifacts, and unresolved decisions. Regenerate
and lint `docs/index.md` before handoff. For multi-session work, hand off to an outcome-led spec or
ticket; do not prescribe file-by-file implementation steps.

## Route the resolved work

Do not automatically invoke a downstream Matt skill or create tracker issues. State the recommended
next move and wait for the user's go-ahead; those operations may create external work records.

| Situation after grilling | Recommended next move |
|---|---|
| A question needs a runnable answer | `/prototype`, then return to this grilling artifact to record the decision. |
| One fresh context window can complete the work | `/to-spec`, then `/handoff goal` to package the spec as a paste-ready fresh-task prompt. The executor uses `/implement` and final `/code-review` as appropriate. |
| The destination is clear but implementation spans multiple fresh sessions | `/to-spec`, then `/to-tickets` when separate execution slices are useful. Each ticket is a vertical, independently verifiable slice. For every selected ticket, use `/handoff goal` to package its governing spec as a fresh-task prompt. |
| The destination itself is unclear and too large for one decision session | `/wayfinder` to resolve the decision map. Once the destination is clear, continue with `/to-spec` then `/to-tickets` when needed. |

This is the multi-session flow: `/to-spec` compresses the resolved grilling context into a
detailed, durable destination; `/to-tickets` describes the vertical route there; each fresh context
implements one ticket; `/code-review` checks the finished work against the original tracker spec and
the repository's standards. Where a resolved spec is executed without tickets, create one goal handoff
for that execution scope first. The generated prompt points at the full spec/ticket; the executor
consults the full source on demand. Do not create an external tracker record automatically.
