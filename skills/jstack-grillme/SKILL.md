---
name: jstack-grillme
description: "Interview the user relentlessly about a plan, design, or decision until shared understanding is reached, walking down every branch of the decision tree and resolving dependencies one by one. MANDATORY TRIGGERS: 'grill me', '/grill-me', 'grill this', 'grill my plan', 'interview me on this', 'walk me through every branch', '/jstack-grillme'. STRONG TRIGGERS: 'stress-test my thinking interactively', 'let's go deep on this design', 'I want to think this through out loud'. Do NOT trigger on simple Q&A, factual questions, or when the user just wants a quick answer."
---

# jstack-grillme — Interactive Decision Tree Grilling

A grilling session walks down every branch of a plan or design, resolving dependencies between decisions one by one. The agent asks one question at a time, provides a recommended answer, and does not stop until the tree is exhausted. The deliverable is shared understanding, not a document.

## Context threshold

Before starting the grill, scan available context: current conversation, referenced files, project notes, workspace context files. Know the shape of the plan and who it affects. Do not pre-grill yourself silently. If you genuinely cannot infer what the user wants grilled, ask: "What's the plan you want grilled?" — exactly that, nothing more.

Proceed when you can identify: the plan, the decision-maker (usually the user), and at least one decision branch that needs resolution.

## Method

Open by stating what you understand the plan to be in two sentences max. If the user corrects you, accept the correction and restate. Once confirmed, begin the tree.

For every question:
1. Ask one question at a time. Never ask two.
2. Provide your recommended answer and the reasoning behind it. Be opinionated — do not present a menu of options without a recommendation.
3. If the answer can be found by exploring the codebase, explore it instead of asking. Report what you found and move on.
4. When the user answers, resolve that branch fully before moving laterally. A branch is resolved when no follow-up questions remain.
5. When a branch is resolved, pick the next highest-impact unresolved branch and repeat.

The tree is structured like this: strategic decisions before tactical ones, dependencies before dependents, external-facing choices before internal ones.

## Anti-patterns

Do not ask these kinds of questions:
- "What do you think about X?" — you should have already formed a recommendation.
- "Option A or Option B?" — without explaining why those are the only two and which you recommend.
- "Are you sure?" — unpack the specific concern instead.
- Questions the codebase can answer — go look.
- Questions designed to validate the user rather than pressure-test the plan.

## Surfacing

When the tree is exhausted, summarize in four sentences max: what was grilled, how many branches were resolved, the single most important decision made, and what remains unresolved (if anything). Offer to save the resolution map to the second brain but do not push.

## Next skills

| Next | When |
|------|------|
| `/jstack-premortem` | The grilling surfaced real failure modes — run a premortem on the resolved plan. |
| `/jstack-savetobrain` | The resolved decisions are worth preserving as durable context. |
| `/jstack-challenge` | The user wants a fresh adversarial eye on the positions they settled on during the grill. |

Otherwise standalone — shared understanding is the deliverable.
