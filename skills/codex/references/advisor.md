# advisor — adversarial pressure-test (the old jstack-challenge)

Spawn an unbiased advisor to pressure-test the user's latest position, reframe, or
decision. The advisor is briefed cold and instructed to attack load-bearing
assumptions, not validate them. Single-shot: each invocation is a fresh advisor with a
freshly written prompt; the skill does not stay active across turns.

Also invoke proactively when you notice yourself agreeing with the user multiple turns
in a row on a high-stakes decision without surfacing real disagreement, and the cost of
being wrong is meaningful (strategy pivot, money commitment, public position).

Do NOT invoke for routine questions, drafting tasks, or decisions the user has clearly
already made and is just executing.

## Mechanics

1. Write the six-section prompt (below) to a temp file with the Write tool.
2. `bash ~/.jstack/bin/codex-run.sh run <prompt-file> --isolated --effort high --timeout 600`
   via Bash with `run_in_background: true` — ALWAYS background, every invocation. The
   advisor takes 30–600s; never block the user staring at a loading bar. `--isolated`
   gives it an empty working dir + read-only sandbox + no web: it must attack from the
   briefing alone.
3. On failure/timeout/CODEX_UNAVAILABLE: spawn the Claude advisor instead — Agent tool,
   `subagent_type: general-purpose`, `model: 'sonnet'`, `run_in_background: true`, the
   exact same prompt. Never drop the pressure-test because the codex path failed.

## How to write the prompt

The advisor has zero conversation context. Brief it like a smart colleague who just
walked into the room. The prompt MUST contain six sections in this order:

### 1. Role declaration
Open with one sentence that anchors the advisor's stance:

> "You are an unbiased strategic advisor. The founder you are advising has been
> brainstorming with another AI partner. That partner has been criticized for agreeing
> too readily. Your job is to pressure-test the founder's most recent reframe with the
> discipline of someone who has zero investment in being liked. Be the skeptic in the
> room. Cite specifics. Do not pad."

### 2. Founder / project context
Two to four short paragraphs covering: who the user is, what they're building, who
their warm relationships are, what's at stake. No conversation transcript — just the
durable facts a stranger would need.

### 3. What has already been killed or settled
Bullet list of hypotheses already retired with one-line reasons. This prevents the
advisor from re-litigating closed questions and forces it to engage with the live
frame. If you don't have killed-hypotheses to list, include current confidence-graded
assumptions instead.

### 4. The reframe to pressure-test
Quote or paraphrase the user's most recent position in their own framing. Be faithful —
do not soften, do not strawman. The advisor must attack the actual claim, not a version
you find easier to defend.

### 5. Required interrogation dimensions
Enumerate 5–10 specific load-bearing assumptions, hidden anchors, or analogies you want
the advisor to attack. Be concrete. Example:

> "Is 'warm trust from X' actually a moat, or a one-shot relationship asset that
> doesn't compound? How many degrees out does a single warm intro propagate before
> strangers say no?"

Cover at minimum:
- The strongest hidden assumption
- The closest historical analog that failed and why this is different
- The specific testable experiment that would falsify the reframe in 30 days
- The "is this actually X-shape vs Y-shape business?" framing question

### 6. Output format and hard constraints
Force structure on the response so the advisor cannot drift into mush:

> Required sections: Verdict (one sentence), Where the reframe is genuinely strong
> (1–3 items), Where it's fooling itself (load-bearing failures), Numbered responses to
> each interrogation question, Honest recommendation for the next 7 days.

> Hard constraints: under 1,200 words, skeptic not cheerleader, cite specifics from the
> founder's own evidence, do NOT propose new wedges or alternatives, be willing to say
> "this doesn't survive" if the evidence points there.

## Anti-pattern: prompts that produce sycophantic critique

These framings cause the advisor to soften into mush. Avoid:

- "Critique this plan." → reads as "find some polish points" → returns sandwich-feedback
- "What do you think?" → reads as opinion question → returns balanced overview
- "What could go wrong?" → reads as risk register → returns generic risk list

Use instead:
- "Pressure-test this. Attack the load-bearing assumptions. You have no incentive to be liked."
- "Be the skeptic in the room. If the reframe doesn't survive, say so."
- "Force the founder to answer X clearly. Do not let them dodge."

## Surfacing the result

When the advisor completes:
1. Open with the verdict in one sentence. Don't bury it.
2. Pull out the 2–3 most cutting findings, in the advisor's own words where possible.
   Quote directly when the phrasing is sharper than yours would be.
3. State whether you (the main agent) agree, partially agree, or disagree with the
   advisor — and why. The user invoked this because the main agent was being too
   agreeable; don't now flip to agreeing with the advisor reflexively. Take a real
   position.
4. End with one concrete next action the advisor's critique implies. Not three options.
   One.

Do NOT just dump the advisor's full response and walk away.

## What this mode is NOT

- Not a research agent. Don't ask the advisor to look things up or run tools.
- Not a brainstorming partner. Don't ask it to propose alternatives or generate options.
- Not a tie-breaker. The advisor has one job: attack the current position. The user
  decides what to do with the attack.
- Not for routine questions ("should I use TypeScript or JavaScript" gets no advisor).

## Next steps

| Next | When |
|------|------|
| `/premortem` | The attack exposed real failure modes in a plan or commitment — map them structurally before deciding. |
| advisor again | The position changed materially after the attack — fresh advisor, freshly written prompt. |
