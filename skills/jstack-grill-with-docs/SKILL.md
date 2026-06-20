---
name: jstack-grill-with-docs
description: A relentless interview to sharpen a plan or design, which also creates docs (ADRs and glossary) as we go.
---

# jstack-grill-with-docs

Interview the user relentlessly about every aspect of their plan until shared understanding is reached, capturing the domain model as permanent documentation along the way. Walk down each branch of the decision tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

This skill is two disciplines interleaved: the **grill** (the conversational interview loop from `jstack-grillme`) and **domain modeling** (building a glossary and recording architectural decisions the moment they crystallize). Do not batch the documentation — update it inline as terms are resolved.

## The grill loop

Ask questions one at a time. Lead with your recommended answer so the user can confirm or correct, rather than treating every question as open-ended. If a question can be answered by exploring the codebase, explore the codebase instead of asking.

Stop grilling when one of these is true: every branch of the design tree has been walked, the user says "ship it," or the remaining open questions are explicitly deferred.

## Domain modeling during the grill

As you grill, actively build and sharpen the project's domain model. This is the *active* discipline — challenging terms, inventing edge-case scenarios, and writing the glossary and decisions down the moment they crystallize. Merely reading `CONTEXT.md` for vocabulary is not this skill; this skill is for when you're changing the model.

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"

## File structure

Most repos have a single context:

```
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

If a `CONTEXT-MAP.md` exists at the root, the repo has multiple contexts. The map points to where each one lives.

Create files lazily — only when you have something to write. If no `CONTEXT.md` exists, create one when the first term is resolved. If no `docs/adr/` exists, create it when the first ADR is needed.

### Update CONTEXT.md inline

When a term is resolved during the grill, update `CONTEXT.md` right there in the same turn. Do not batch these up — capture them as they happen. Use the format defined in `references/CONTEXT-FORMAT.md`.

`CONTEXT.md` must be totally devoid of implementation details. It is a glossary of domain terminology, not a spec, a scratch pad, or a repository for implementation decisions.

### CONTEXT.md rules

- **Be opinionated.** When multiple words exist for the same concept, pick the best one and list the others under _Avoid_.
- **Keep definitions tight.** One or two sentences max. Define what it IS, not what it does.
- **Only include terms specific to this project's context.** General programming concepts (timeouts, error types, utility patterns) don't belong even if the project uses them extensively. Before adding a term, ask: is this a concept unique to this context, or a general programming concept? Only the former belongs.
- **Group terms under subheadings** when natural clusters emerge. If all terms belong to a single cohesive area, a flat list is fine.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the format in `references/ADR-FORMAT.md`.

An ADR can be a single paragraph. The value is in recording *that* a decision was made and *why* — not in filling out sections.

## After the session

When the grill concludes, summarize what was resolved: terms added to the glossary, ADRs created, decisions deferred, and branches walked. Point the user at the artifacts — `CONTEXT.md` and any new ADRs — so they can review.

## Next skills

| Next | When |
|------|------|
| `/jstack-savetobrain` | Captured domain insights worth preserving in the second brain beyond the repo |
| `/jstack-premortem` | The plan is sharp and you want to stress-test it from the failure direction |
| `/jstack-handoff` | The session produced a plan ready for another agent or session to execute |

Otherwise standalone — the artifacts live in the repo and every future AI session benefits from them.
