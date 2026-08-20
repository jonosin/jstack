---
name: to-spec
description: "Create a durable, outcome-led execution spec from settled context. Use when an agreed change or delivery needs one authoritative contract for a fresh task or multi-session work."
---

# to-spec

Turn the settled conversation and relevant artifacts into one durable execution spec. Synthesize; do
not restart the interview or reopen settled decisions. The spec is the execution source of truth.

Use the project's established planning location. If it has none, create the spec at an explicit,
durable path in the current project. Link to decision records and sources instead of copying them.

Write this structure:

```markdown
# <action-oriented title>

## Contract

### Outcome

### Acceptance

### Scope

### Constraints

### Stop / escalation

### Settled decisions

### Sources

### Closeout review

## Milestones

- [ ] <short name> — <observable ideal state>

## Progress

Status: <not started | active | blocked | done>
Updated: <YYYY-MM-DD>
Current milestone: <short name>

### Completed

### Next

### Blockers

## Contract changes
```

Make the Contract specific enough for an agent to decide done from the Acceptance evidence. State the
condition that requires the executor to stop and ask, such as missing authority, an irreversible
action, a required credential, or an unresolved decision that changes the Contract. Keep the Contract
stable during execution. After material work, update Progress with compact state and evidence. When a
durable decision changes the contract, record its reason and authority under Contract changes, then
revise the affected Contract text.

Write the smallest useful milestone set. Each milestone describes the observable ideal state at a
meaningful transition and leaves the method to the executor. Use milestones for orientation and
Progress tracking; use Acceptance to decide completion.

Every spec requires a closeout review after the work and acceptance checks. Dispatch a fresh,
read-only independent reviewer with the Contract, changed artifacts, and verification evidence. The
reviewer checks the delivered work against every relevant Contract clause: Outcome, Acceptance,
Scope, Constraints, Stop / escalation, and Settled decisions when applicable. The reviewer maps
every Acceptance clause to evidence, runs safe required tests, and returns `ship`, `fix-first`, or
`rethink`. For `fix-first`, dispatch a bounded quick-fix subagent with the exact gap, owned files,
and done condition; rerun the affected checks, then request a fresh review. For
`rethink`, or when a fix changes the Contract or needs new authority, stop at the escalation boundary.
The main session owns final acceptance.

The spec is ready when its outcome, acceptance evidence, scope, constraints, stop / escalation
boundary, settled decisions, milestones, and closeout review are clear, and Progress names the
current milestone and exact next action or blocker.

## Next skills

| Next | When |
|------|------|
| `/handoff` | The spec or its active progress must move to another session or agent. |
