# GTM 40 Checks Audit

Audit the actual current motion, not an aspirational strategy or a generic best-practice list.

## Workflow

1. **Resolve the business and motion.** Identify the offer, ICP, channel, campaign window, conversion event, and current constraint. Read the most current grounded GTM artifacts: operating context, strategy/ADR, campaign exports, CRM or outcome data, copy, sequence, and sending configuration. Prefer observed results over plans. When sources conflict, use the newest evidence and state the conflict.
2. **Set the evidence boundary.** State the motion, period, and materials audited. Use `Pass`, `No`, `Unknown`, or `N/A` for every check. `No` requires evidence it fails; `Unknown` means evidence is missing; `N/A` means the channel makes a check structurally inapplicable. Missing evidence is never a pass.
3. **Score every check below.** Apply email-deliverability checks only to email. For LinkedIn, calls, events, or another channel, mark genuinely email-only checks `N/A` and name the closest channel control when one exists.
4. **Count leaks fairly.** Report `No / applicable checks` by stage and report unknowns separately. Do not rank a stage by raw failures when most of its checks are N/A.
5. **Diagnose one priority.** Name a biggest leak only when the evidence supports it; otherwise label it a leading hypothesis. Do not prescribe copy changes for a list, delivery, targeting, or measurement failure.
6. **Recommend one next test.** Give the smallest reversible action that can fix or falsify the priority leak, with owner, success metric, decision threshold, and re-audit point. Do not turn every failure into a work plan.

## Required output

```markdown
# GTM 40 Checks Audit — <business / motion>

## Scope and evidence
- Motion / period:
- Materials reviewed:
- Evidence limits:

## Stage scorecard
| Stage | No / applicable | Unknown | Verdict |
|---|---:|---:|---|
| List quality | | | |
| Deliverability | | | |
| Targeting and signal | | | |
| Messaging | | | |
| Follow-up and measurement | | | |

## Check findings
For every check: `# | Pass / No / Unknown / N/A | evidence | implication`.

## Biggest leak
<one evidence-backed stage, or clearly labelled leading hypothesis>

## Fix-first plan
1. <action, owner, deadline>
   - Success metric and threshold:
   - What would change the diagnosis:

## Do not change yet
<tests or strategy elements not supported by the evidence>
```

## Rubric

### 1. List quality

1. Are email addresses verified in the hours before sending?
2. Are catch-all and role addresses removed?
3. Are sends released in controlled batches rather than indiscriminate blasts?
4. Is campaign bounce rate below roughly 2–3%?
5. Do bounce and reply outcomes feed the next list build?
6. Is every contact confirmed at the correct current company?
7. Does enrichment capture live signals, not only firmographics?
8. Is the true addressable market known and ranked rather than guessed?
9. Is the list deduplicated across campaigns and sending identities, with recent-contact suppression?
10. Is the list refreshed from prior outcomes instead of rebuilt from zero?

### 2. Deliverability

11. Are multiple sending domains used so one domain is not a single point of failure?
12. Are SPF, DKIM, and DMARC configured and verified on every sending domain?
13. Is each inbox capped at roughly 30–50 emails per day?
14. Was each domain warmed for at least 30 days before campaign volume?
15. Is spam-complaint rate below 0.1%?
16. Are senders distributed across ESPs where volume warrants it?
17. Do sending identities have real names, credible profiles, and clean signatures?
18. Is inbox placement monitored with seed tests, not inferred from open rates?

### 3. Targeting and signal

19. Does every account have at least one reason to reach out now?
20. Is the signal recent, normally within the last 90 days?
21. Is the ICP divided into segments with materially different buying behavior?
22. Are segments defined before messaging is written?
23. Do highest-signal accounts receive a higher-touch treatment?
24. Is contract value or economic potential known by segment?
25. Is fit scored before enrichment spend or outreach?
26. Does the contacted person own the problem being solved?

### 4. Messaging

27. Does the first message offer something useful without requiring a call?
28. Can the recipient verify one concrete proof point in the message?
29. Is there exactly one clear ask?
30. Is the ask proportionate to the trust level of a cold relationship?
31. Is personalization based on substantive account research?
32. Is experimentation focused on offer and ask rather than treating subject lines as the main lever?
33. Does the first message earn the follow-up, with follow-ups normally 3–5 days apart?
34. Is recognition built before the cold touch where that is practical?

### 5. Follow-up and measurement

35. Is the sequence four touches, normally spaced 3–5 days apart?
36. Does every follow-up add a distinct angle, proof point, or value?
37. Is conversion from booked meeting to opportunity measured within 45 days?
38. Does a human own confirmation and pre-meeting context in the final minute before the meeting lands?
39. Are loss reasons captured and fed back into targeting?
40. Does every campaign seed the next campaign with its outcomes?

## Guardrails

- Treat strategy as a hypothesis; campaigns, replies, meetings, opportunities, revenue, and loss reasons are stronger evidence.
- A positive reply, click, meeting, or open is not revenue validation. Trace evidence to the next commercial stage available.
- Preserve causality: a weak offer and poor targeting can coexist. Prioritize the evidence-backed constraint rather than averaging explanations.
- State the source for every material conclusion. Do not invent metrics, signals, list hygiene, or outcomes.
