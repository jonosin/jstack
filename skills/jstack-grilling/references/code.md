# Code grilling

Use this branch for a codebase change, architecture decision, or domain-modeling work.

## Canonical artifacts

- `CONTEXT.md` holds durable domain vocabulary only. Add a term when its meaning is specific to this
  codebase and it will improve later reasoning or naming.
- `docs/strategy/YYYY-MM-DD-<self-explanatory-decision>.md` holds local technical decisions and
  architecture/design rationale. Use `type: architecture` for a genuine architecture decision.
  Create one only when a future maintainer would otherwise ask why the code has this shape.
- For multi-session delivery, Matt's tracker spec created by `/to-spec` is the canonical destination.
  With Matt's local Markdown tracker it lives at repository-root `.scratch/`; a configured GitHub or
  other tracker may own it instead. Do not create a duplicate pointer doc. Do not turn `CONTEXT.md`
  or a decision record into a file-by-file implementation plan.

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
| One fresh context window can complete the work | `/jstack-handoff goal` for this execution scope, then ask to spawn its fresh execution task and wait for confirmation. The outcome-led handoff carries success, constraints, decisions, risks, and validation; the executor uses `/implement` and final `/code-review` as appropriate. |
| The destination is clear but implementation spans multiple fresh sessions | `/to-spec`, then `/to-tickets`. `/to-spec` persists the detailed destination in the configured tracker (repository-root `.scratch/` for Matt's local Markdown tracker). Each ticket is a vertical, independently verifiable slice. For every selected ticket, create `/jstack-handoff goal`, ask to spawn its fresh execution task, and wait for confirmation before implementation. |
| The destination itself is unclear and too large for one decision session | `/wayfinder` to resolve the decision map. Once the destination is clear, continue with `/to-spec` then `/to-tickets`. |

This is Matt's actual multi-session flow: `/to-spec` compresses the resolved grilling context into a
detailed, durable destination; `/to-tickets` describes the vertical route there; each fresh context
implements one ticket; `/code-review` checks the finished work against the original tracker spec and
the repository's standards. Where a resolved spec is executed without tickets, create one goal handoff
for that execution scope first. The handoff points at the full spec/ticket and carries only the
outcome-led execution essentials; the executor consults the full source on demand. Do not create an
external tracker record automatically.
