---
name: jstack-challenge
description: Spawn an unbiased advisor subagent to pressure-test the user's latest position, reframe, or decision. Use when the user wants honest pushback because the main agent has been agreeing too readily, or asks for "a second opinion", "pressure test this", "challenge me", "spawn an advisor", "/jstack-challenge". The subagent is briefed cold and instructed to attack load-bearing assumptions, not validate them.
---

# jstack-challenge — Adversarial Advisor Subagent

When the user wants an unbiased pressure-test of their latest position, decision, or reframe — especially when the main agent has been pattern-matching agreement — spawn a fresh subagent briefed cold and instructed to attack the position rather than support it.

## When to invoke

Invoke when the user says any of:
- "spawn an advisor"
- "pressure-test this"
- "challenge me"
- "get a second opinion"
- "/jstack-challenge"
- "you've been agreeing too much"
- "play devil's advocate on this"
- "stress test my thinking"

Also invoke proactively when you notice yourself agreeing with the user multiple turns in a row on a high-stakes decision without surfacing real disagreement, and the cost of being wrong is meaningful (strategy pivot, money commitment, public position).

Do NOT invoke for routine questions, drafting tasks, or decisions the user has clearly already made and is just executing.

## How to spawn the advisor (auto-pick the engine)

The advisor can run on one of two engines. Pick automatically. The engine choice never changes the role, the six-section prompt, or the surfacing protocol. Everything from "How to write the prompt" onward is identical regardless of which engine runs.

**Step 1: probe for a background Codex engine.** Run this synchronously:

```bash
bash ~/.claude/skills/jstack-challenge/scripts/codex-advisor.sh probe
```

(In non-Claude installs, the helper is this skill's own `scripts/codex-advisor.sh`.) It prints `CODEX_OK` (exit 0) when the OpenAI Codex CLI is installed AND authed (`CODEX_API_KEY` or `OPENAI_API_KEY` set, or `~/.codex/auth.json` exists), or `CODEX_UNAVAILABLE` (exit 1) otherwise.

**Step 2: if `CODEX_OK`, run the advisor as a background Codex agent.**
1. Write the full six-section prompt (see below) to a temp file, e.g. `mktemp /tmp/jstack-advisor-XXXXXX.md`. Use the Write tool so escaping is not a concern.
2. Run the helper with `run_in_background: true` so the user is not blocked:
   ```bash
   bash ~/.claude/skills/jstack-challenge/scripts/codex-advisor.sh run /tmp/jstack-advisor-XXXXXX.md
   ```
   The helper runs `codex exec -s read-only` with no web search and no write access, in an isolated empty directory, so the advisor reasons purely from the briefing and cannot research or touch files. It parses the JSONL event stream and prints only the advisor's final message to stdout.
3. When it finishes, surface stdout using the surfacing protocol below.
4. Fallback: if the helper exits non-zero or stdout is empty (timeout, auth error, or the marker `__CODEX_UNAVAILABLE__` on stderr), spawn the Claude advisor instead with the exact same prompt. Never drop the pressure-test because the Codex path failed.

**Step 3: else (`CODEX_UNAVAILABLE`), spawn the Claude advisor.** Use the `Agent` tool with:
- `subagent_type`: `general-purpose`
- `model`: `sonnet` (override; Sonnet 4.6 gives the right balance of skepticism and structure for this task)
- `run_in_background`: `true` (the user shouldn't wait staring at a loading bar; surface the result when it completes)

Why auto-pick: a background Codex agent is a genuinely independent second model, which is exactly what an adversarial pressure-test wants. When Codex is absent or unauthed, the Claude advisor is the proven fallback and behaves exactly as it did before this path existed.

## How to write the prompt

The subagent has zero conversation context. Brief it like a smart colleague who just walked into the room. The prompt MUST contain six sections in this order:

### 1. Role declaration
Open with one sentence that anchors the subagent's stance:

> "You are an unbiased strategic advisor. The founder you are advising has been brainstorming with another AI partner. That partner has been criticized for agreeing too readily. Your job is to pressure-test the founder's most recent reframe with the discipline of someone who has zero investment in being liked. Be the skeptic in the room. Cite specifics. Do not pad."

### 2. Founder / project context
Two to four short paragraphs covering: who the user is, what they're building, who their warm relationships are, what's at stake. No conversation transcript — just the durable facts a stranger would need.

### 3. What has already been killed or settled
Bullet list of hypotheses already retired with one-line reasons. This prevents the advisor from re-litigating closed questions and forces it to engage with the live frame. If you don't have killed-hypotheses to list, include current confidence-graded assumptions instead.

### 4. The reframe to pressure-test
Quote or paraphrase the user's most recent position in their own framing. Be faithful — do not soften, do not strawman. The subagent must attack the actual claim, not a version you find easier to defend.

### 5. Required interrogation dimensions
Enumerate 5–10 specific load-bearing assumptions, hidden anchors, or analogies you want the advisor to attack. Be concrete. Example:

> "Is 'warm trust from X' actually a moat, or a one-shot relationship asset that doesn't compound? How many degrees out does a single warm intro propagate before strangers say no?"

Cover at minimum:
- The strongest hidden assumption
- The closest historical analog that failed and why this is different
- The specific testable experiment that would falsify the reframe in 30 days
- The "is this actually X-shape vs Y-shape business?" framing question

### 6. Output format and hard constraints
Force structure on the response so the advisor cannot drift into mush:

> Required sections: Verdict (one sentence), Where the reframe is genuinely strong (1–3 items), Where it's fooling itself (load-bearing failures), Numbered responses to each interrogation question, Honest recommendation for the next 7 days.

> Hard constraints: under 1,200 words, skeptic not cheerleader, cite specifics from the founder's own evidence, do NOT propose new wedges or alternatives, be willing to say "this doesn't survive" if the evidence points there.

## Anti-pattern: prompts that produce sycophantic critique

These framings cause the subagent to soften into mush. Avoid:

- "Critique this plan." → reads as "find some polish points" → returns sandwich-feedback
- "What do you think?" → reads as opinion question → returns balanced overview
- "What could go wrong?" → reads as risk register → returns generic risk list

Use instead:
- "Pressure-test this. Attack the load-bearing assumptions. You have no incentive to be liked."
- "Be the skeptic in the room. If the reframe doesn't survive, say so."
- "Force the founder to answer X clearly. Do not let them dodge."

## Surfacing the result

When the subagent completes:
1. Open with the verdict in one sentence. Don't bury it.
2. Pull out the 2–3 most cutting findings, in the advisor's own words where possible. Quote directly when the phrasing is sharper than yours would be.
3. State whether you (the main agent) agree, partially agree, or disagree with the advisor — and why. The user invoked this skill because the main agent was being too agreeable; don't now flip to agreeing with the advisor reflexively. Take a real position.
4. End with one concrete next action the advisor's critique implies. Not three options. One.

Do NOT just dump the advisor's full response and walk away. The user invoked this skill so the main agent could think harder, not so they could read another wall of text.

## What this skill is NOT

- Not a research agent. Don't ask the advisor to look things up or run tools.
- Not a brainstorming partner. Don't ask the advisor to propose alternatives or generate options.
- Not a tie-breaker. The advisor has one job: attack the current position. The user decides what to do with the attack.
- Not for routine questions. If the user asks "should I use TypeScript or JavaScript", do not spawn an advisor.

## Persistence

This is a single-shot skill. Each invocation spawns a fresh advisor with the latest position. The skill itself does not stay active across turns. If the user wants another pressure-test on a revised position later, invoke the skill again with a freshly-written prompt.

## Next skills

| Next | When |
|------|------|
| `/jstack-premortem` | The advisor's attack exposed real failure modes in a plan or commitment — run a structured premortem to map them before deciding. |
| `/jstack-challenge` | The position changed materially after the attack — re-run on the revised position (single-shot; each run is a fresh advisor). |

Otherwise standalone — the user decides what to do with the pushback; no required next step.
