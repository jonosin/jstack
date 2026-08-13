---
name: premortem
description: "Run a premortem on any plan, launch, product, hire, strategy, or decision. Assumes it already failed 6 months from now and works backward to find every reason why. Produces a revised plan with blind spots exposed. MANDATORY TRIGGERS: 'premortem this', 'premortem my', 'run a premortem', 'what could kill this', 'future-proof this', 'stress test this plan', 'what am i missing here', 'find the blind spots'. STRONG TRIGGERS: 'what could go wrong', 'am i missing anything', 'poke holes in this', 'where will this break', 'devil's advocate this'. Do NOT trigger on simple feedback requests, factual questions, or LLM Council requests. DO trigger when someone has a plan or commitment where the cost of being wrong is high."
---

# premortem

A premortem assumes the plan has already failed 6 months from now and works backward to explain why. Use it to break agreeable, optimistic analysis and expose concrete failure modes before the user commits.

## Context threshold

Before running the premortem, scan available context first: current conversation, referenced files, project notes, memory folders, and workspace context files. Do not ask questions if the minimum bar is already met.

Proceed only when you know three things: what the plan is, who it is for or affects, and what success means. If one is missing, ask the single most important missing question and continue after the answer.

## Frame

State the frame explicitly before analysis: it is 6 months from now, the plan has failed, and we are looking backward to understand what killed it.

## Raw premortem

Generate every genuine reason the plan could have died. Do not use preset categories. Each reason must be specific to the actual plan, grounded in the given context, and a real threat rather than a generic inconvenience. Use the number of failure reasons that is real for the plan.

## Deep dives

Spawn one subagent per failure reason where possible, in parallel. If the environment limits concurrency, batch them with no cross-contamination. Give each subagent the full plan context, the premortem frame, and exactly one assigned failure reason.

Subagent output must include the failure story, the underlying assumption, and one or two early warning signs. Keep it under 300 words.

## Synthesis

Produce a premortem report with the most likely failure, the most dangerous failure, the hidden assumption, the revised plan, and a pre-launch checklist. The revised plan must be concrete and mapped to the failure modes.

## Artifacts

Save two files in the user's current workspace:

```text
premortem-report-[timestamp].html
premortem-transcript-[timestamp].md
```

The HTML report must be self-contained with inline CSS, dark background, prominent synthesis at the top, one visual card per failure reason, likelihood/severity indicators, and a grid showing the agents/findings.

After generating the report, return the file paths and attach or link the HTML if the platform supports it. If the user explicitly asks to open the report, or the source premortem workflow says to open the HTML after generation, use the appropriate local GUI command such as `open <report.html>` on macOS. Do not treat explicit "open this" requests as forbidden GUI automation.

## Chat output

Hard rule: the chat reply is exactly three sentences, one each and in this order: (1) the single most likely failure, (2) the hidden assumption, (3) the single most important revision. Never write a fourth sentence, a preamble, a sign-off, or extra caveats. Everything else belongs in the report, not the chat.

## Next skills

| Next | When |
|------|------|
| `/jstack-challenge` | After the premortem, the user wants a fresh advisor to attack the *revised* plan's load-bearing assumptions head-on. |

Otherwise standalone — the revised plan is the deliverable; no required next step.
