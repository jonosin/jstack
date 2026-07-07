---
name: jstack-codex
description: Router for using GPT-5.5 via the OpenAI Codex CLI as a subagent. Four modes — advisor (adversarial pressure-test of the user's position; replaces jstack-challenge), review (independent code/plan review), implement (clear-spec bulk implementation), investigate (research/diagnosis/data analysis). Use when the user says "/jstack-codex", "/jstack-challenge", "challenge me", "pressure test this", "second opinion", "spawn an advisor", "stress test my thinking", "play devil's advocate", "have codex review/implement/investigate X", "send this to codex", or "run this on gpt-5.5". Global CLAUDE.md decides WHEN to route work to codex; this skill is HOW to brief it.
---

# jstack-codex — GPT-5.5 subagent router

Global CLAUDE.md §"Picking the right models" owns the routing policy (when codex gets
work, thresholds, the roster). This skill owns the playbooks: how to brief GPT-5.5 for
each use case. Do not restate policy here; do not improvise prompts when a playbook fits.

## Modes

| Mode | Use case | Reference | Effort | Sandbox |
|------|----------|-----------|--------|---------|
| advisor | adversarial pressure-test of the user's latest position/decision (the old jstack-challenge) | references/advisor.md | high | read-only, --isolated (empty dir, no web) |
| review | independent review of a diff/branch/plan | references/review.md | high (xhigh for ship-gates) | read-only |
| implement | clear-spec bulk implementation, migrations, mechanical sweeps | references/implement.md | medium | --write, worktree when parallel |
| investigate | diagnosis, research, data analysis | references/investigate.md | medium (high for deep investigations) | read-only, --search when the question is about the current world |

Pick the mode from the user's intent. "Challenge/pressure-test/second opinion on a
position" → advisor. "Review this diff/plan" → review. "Implement/migrate/crunch this"
→ implement. Anything question-shaped → investigate. Apply this mode choice to every
codex dispatch in the session, not just the first one.

## Mechanics (all modes)

1. Read the mode's reference file and `references/gpt55-prompting.md` (prompt style).
2. Write the prompt to a temp file with the Write tool (Markdown, outcome-first —
   never GPT-5.4 XML blocks).
3. Run `bash ~/.jstack/bin/codex-run.sh run <prompt-file> <mode flags from the table>`
   via Bash with `run_in_background: true` — every mode, every invocation. Never block
   the user on a foreground codex run.
4. Surface the result per the mode's reference. For review/advisor output: findings
   ordered by severity, verdict first.

Fallback: if `codex-run.sh probe` says CODEX_UNAVAILABLE or a run fails/times out,
advisor mode falls back to a Claude subagent (general-purpose, `model: 'sonnet'`,
`run_in_background: true`) with the exact same prompt; other modes report the failure
and ask — never silently substitute a Claude-side answer for a failed codex run.

## Result handling (all modes)

- Present findings ordered by severity; keep the verdict/summary structure.
- NEVER auto-apply review or advisor findings — stop and ask which to act on.
- Preserve evidence boundaries: fact vs inference vs open question, as codex labeled them.
- If codex made edits (implement mode), say so and list touched files.
- If the run produced nothing, report that plainly; do not fill the gap with your own
  guess presented as codex's output.
