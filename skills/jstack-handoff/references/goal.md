# Handoff — goal mode (fresh execution task)

Use when work should continue in a fresh task without carrying this conversation's context. Create an
outcome-led execution contract, then emit a completed `/goal` prompt. For tracker-backed work, the
spec or ticket remains the detailed plan; this handoff is the concise execution contract and pointer,
not a duplicate.

`/goal` is the execution engine. The new session has no memory of the planning session, so it must be
able to act safely from the handoff plus the referenced authoritative artifact.

## Distill the contract

Give the work one measurable stop condition. Define done with observable behavior and an exact command
plus expected output wherever possible; never use subjective acceptance. Do not add file-by-file steps,
milestones, or an implementation sequence when the tracker spec/ticket already owns that detail.

Do not silently invent load-bearing values. Either state how the executor discovers the value, or record
the chosen assumption explicitly under risks and unknowns.

## Write the durable handoff

Save to `~/.jstack/handoffs/session-YYYY-MM-DD-<slug>-goal.md` (append `-2`, `-3` if needed). Apply
the shared rules in `SKILL.md`: state the repo and working directory first, reference artifacts rather
than duplicating them, and redact secrets.

Use this exact primary structure:

```markdown
# <action-oriented title>

> Execution contract. Keep Progress / Surprises & Discoveries / Decision Log / Outcomes current so a
> new context can resume from this file.

Run from `<repo-path>`; all relative paths resolve against it.

## Outcome
Single verifiable stop condition, including command and expected output.

## Why this matters
What becomes possible and for whom.

## Success / acceptance
Observable behavior, acceptance criteria, and scope boundary.

## Constraints and non-goals
Standing rules, anti-patterns, and what not to change.

## Decisions already made
Settled choices and rationale. Do not reopen without material new evidence.

## Risks and unknowns
Assumptions, dependencies, and how to resolve any unknown load-bearing value.

## Validation
Exact commands/proofs, expected output, and any rollback note. Safe to rerun.

## Supporting docs and context
Start with the authoritative tracker spec/ticket URL or path. Then list only relevant docs, code paths,
and vocabulary. State: “Read the full spec/ticket on demand; it owns detailed implementation scope.”

## Execution safeguards
Re-read this contract and repo `AGENTS.md` before changing work. Resolve reversible ambiguity and log
it. Use an independent checker for consequential or ambiguous validation. Never echo secrets or widen
scope. Stop only for missing authority, an irreversible unapproved action, an interactive credential or
login, or a decision that cannot safely be resolved. State the smallest unblock and exact resume point.

## Suggested skills

## Progress
<!-- executor: timestamped completed/remaining items -->

## Surprises & Discoveries
<!-- executor: observation + evidence -->

## Decision Log
<!-- executor: decision + rationale + date -->

## Outcomes & Retrospective
<!-- executor: result versus Outcome -->
```

The handoff must carry the outcome, constraints, decisions, risks, and validation inline. The executor
loads the linked spec/ticket on demand rather than duplicating its detailed implementation plan.

## Emit the launch prompt

First give a recap under 200 words: outcome, acceptance, authoritative spec/ticket if any, and explicit
assumptions. Then fill `references/goal-mode-template.md`, count it with `wc -c`, and keep it under
1500 characters.

For a spec/ticket execution goal, always ask: `Spawn a fresh execution task for <spec-or-ticket title>
now?` Wait for the user's confirmation before creating it. For another goal, likewise require explicit
immediate-start authorization; if it is absent, return the completed paste-ready prompt.
