---
name: jstack-skillify
description: "Use when you want to turn working, judgment-driven work into deterministic code — two modes. (1) CODIFY: invoke after a successful interactive session to save it as a NEW deterministic skill ('skillify this', 'codify this', 'save this as a skill', 'make this permanent', 'turn this into a skill'). (2) HARDEN: invoke on an EXISTING skill to push its fuzzy, judgment-driven steps into deterministic scripts ('make this skill more deterministic', 'harden this skill', 'extract the code from this skill', 'turn these steps into a script', 'codify part of this skill'). Eval-gated so behavior can't silently change. NOT for metric-driven accuracy/efficiency tuning of an existing skill — that is /jstack-skilltune."
---

# jstack-skillify

The productivity multiplier. You just did something that worked — pulled data from a page, ran a multi-step lookup, transformed some output. jstack-skillify codifies the working path into a deterministic skill so next time it runs in one shot with no re-discovery. It also **hardens an existing skill** by pushing its fuzzy, judgment-driven steps into deterministic code. Every successful prototype is a one-time cost.

**Fully harness-agnostic.** This skill does not prescribe tools, languages, or file layouts. It runs the codification workflow. You (the agent) ran the prototype — you decide the best deterministic route.

## Two modes — produce deterministic code

| Mode | Source | When |
|------|--------|------|
| **Codify** | a session that just worked | you did something repeatable and want it as a NEW skill |
| **Harden** | an existing skill's fuzzy steps | a skill works but leans on LLM judgment you want made deterministic (extract scripts) |

Both modes run the same flow (Steps 1–10); Step 1 branches on the mode.

**Routing:** a description of something / "save what we just did" → **Codify**. An existing skill name +
"make it deterministic / harden / extract code" → **Harden**. An existing skill name + "more accurate /
consistent / efficient" is **tuning, not hardening → `/jstack-skilltune`** (a metric eval loop, not a
refactor). Ambiguous → ask one line: "Harden `<x>` into code, or tune its consistency
(`/jstack-skilltune`)?"

### Routing self-check (credit: skill-creator trigger optimization)

Run this table once, whenever this skill's or jstack-skilltune's `description:` changes, to confirm the
boundary still discriminates cleanly:

| Phrasing | Routes to |
|---|---|
| "skillify this" | Codify |
| "codify this" | Codify |
| "save this as a skill" | Codify |
| "make this permanent" | Codify |
| "turn this into a skill" | Codify |
| "make this skill more deterministic" | Harden |
| "harden this skill" | Harden |
| "extract the code from this skill" | Harden |
| "turn these steps into a script" | Harden |
| "codify part of this skill" | Harden |
| "make this skill more accurate" | Tune → `/jstack-skilltune` |
| "make this skill's output more consistent/reliable" | Tune → `/jstack-skilltune` |

If any phrasing lands ambiguously across two routes, tighten the two descriptions' trigger language until
each phrasing has exactly one home.

## Iron contract

Skills are user-trust artifacts. A broken skill erodes confidence. Write to a temp dir, test there, and only move into the final path on test pass plus explicit user approval. On either failure, remove the temp dir entirely. No "almost shipped" state.

## Orchestration — Opus drives, Sonnet does the grunt work

The main session is the **orchestrator on Opus 4.8** and does the *important, non-repetitive* work itself:
deciding the deterministic route, writing the code, and every keep/ship decision — the smart model on the
high-leverage steps. Delegate only **grunt / repetitive / token-heavy** work — running tests, capturing
fixtures, scaffolding, bookkeeping — to **Sonnet 4.6 subagents** (`claude-sonnet-4-6`), spawned aggressively,
one job each, so their bulky output never enters the main context. When an *important* task must run as a
**separate** subagent (e.g. a cold checker that verifies the hardened skill reproduces the captured
behavior, to keep maker ≠ checker), use an **Opus 4.8 subagent** (`claude-opus-4-8`). Rule of thumb: smart /
creative / judgment → Opus; repetitive / mechanical / verbose → Sonnet 4.6 subagent.

---

# The codify / harden flow

## Step 1 — Provenance guard (branches by mode)

**Codify mode.** Walk back through the conversation, at most 10 agent turns, and identify the most recent successful multi-step interaction that produced a useful, repeatable output. It must be:

- Bounded: you can identify where it started, what steps ran, and what the accepted output was.
- Successful: the user accepted the result without invalidating it.
- Codifiable: the steps can be expressed deterministically.

If you cannot find one, refuse: *"No recent codifiable session found. Run the thing first, then say /skillify."* Stop. Do not synthesize from chat fragments or failed attempts. If the conversation has drifted past the candidate, ask once: *"The last codifiable session was '<what you did>' a few turns back. Skillify that?"* A "yes" continues.

**Harden mode.** The arg names an existing skill and the intent is "make it deterministic / harden." Identify the specific steps in its `SKILL.md`/references that rely on LLM judgment but **could** be deterministic code. A step that genuinely needs runtime judgment stays fuzzy — do not force it into code.

> **Eval-gate (mandatory for hardening).** Before changing anything, capture the skill's current behavior on **3+ representative inputs** as fixtures (input → current output). Hardening must reproduce that behavior; you verify against these in Step 7. Hardening that silently changes behavior is forbidden. For *measuring/improving* accuracy or efficiency against a held-out set, that is **`/jstack-skilltune`**, not here.

## Step 2 — Name

- **Codify mode:** extract a short, descriptive name — lowercase letters/digits/dashes, ≤32 chars, starts with a letter, no consecutive dashes, `jstack-` prefix. Ask the user to confirm; warn on collision.
- **Harden mode:** the name is the existing skill — you edit it in place. No rename, no new name.

## Step 3 — Decide the deterministic route

You ran the prototype (or you can read the existing skill's fuzzy steps). Decide the simplest deterministic path that reproduces the behavior.

The only constraint: the codified path must run deterministically without human judgment — no interactive prompts, no "figure it out" steps, no re-discovery. A future agent (or cron job) should invoke it and get the same shape of output. Beyond that, you decide everything: a shell pipeline, a Python script, a sequence of API calls. Use whatever matches what actually worked. For hardening, the route is the script(s) that replace the identified fuzzy steps.

**Repeated-work signal** (credit: anthropics skill-creator). Determinism follows observed repetition, not
vague preference: if the same helper logic was written or re-derived in **≥2** of the session's runs or
fixtures, that logic MUST be bundled as a `scripts/` file rather than left as inline, re-typed-each-time
reasoning. Seeing it once is a judgment call; seeing it twice is a mandate.

## Step 4 — Capture a fixture

Save a snapshot of the input data the code operates on; Step 5's test replays against this snapshot so the parse/transform logic is verified independently of live calls. For hardening, the behavioral fixtures captured by Step 1's eval-gate serve here.

## Step 5 — Write the test

A minimal test that exercises the codified path against the fixture. It must assert something meaningful about the output — shape, key fields, presence of expected data — not just that the script didn't crash. For hardening, the test asserts the new code **reproduces the captured behavior** (no regression). Match the test format to the skill format (shell test for a shell skill, pytest for Python, etc.).

## Step 6 — Author the skill files (delegate to skill-creator)

**Load the `skill-creator` skill** and follow its conventions for file structure and SKILL.md format.

- **New skill:** use `init_skill.py` to scaffold a staging dir under `/tmp/jstack-skillify-<name>/`. Place the codified script in `scripts/`, the fixture in `references/` or alongside the test.
- **Hardening:** copy the existing skill into the sandbox, add the new script(s) under `scripts/`, and rewrite the fuzzy step in `SKILL.md` to call the script. Keep everything else intact.
- Frontmatter spec: only `name` and `description` in YAML; the description must say what the skill does and when to use it (the triggering mechanism). Keep the SKILL.md body lean.

skill-creator owns the authoring conventions. jstack-skillify owns the codification logic. Use both.

## Step 7 — Run the test against staging

Run the test inside the staging/sandbox dir. For hardening, also confirm **no behavioral regression** vs the Step 1 fixtures. If it fails and the failure is a fixable logic bug, fix it and retry — at most twice; show the diff before each retry. If still failing after two retries, or the failure is environmental, remove the sandbox and report the failure. No on-disk artifact.

**Blind-comparison check (harden mode only, credit: skill-creator comparator).** Alongside the fixture-match
check above, judge the old-skill output vs the hardened-script output **blind** on the same fixture — strip
which-is-which labels before judging. The hardened output must be judged equal-or-better to pass. A fixture
that technically matches but reads worse blind is still a hardening regression; fix before proceeding to
Step 8.

## Step 8 — Approval gate

Tests passed. Ask the user:

- **Commit it.** New skill → moves into `~/jstack/skills/<name>/` + symlinks across harnesses. Hardening → updates the existing canonical skill in place.
- **Show me first.** Print the SKILL.md and the main script (for hardening, the diff), then re-ask (without the show option).
- **Discard.** Remove the sandbox. Nothing changes on disk.

## Step 9 — Commit or discard

**Description=when rule (both modes, credit: obra/superpowers writing-skills).** Before committing, check
the skill's `description:` field: it must state WHEN to invoke the skill, never a summary of its internal
workflow steps. Documented failure mode: an agent reads a workflow-summary description, believes it already
knows what to do, and skips reading the body — so the description's only job is triggering, not explaining.
Rewrite it if it drifted into a summary.

**Lint gate (both modes, mandatory).** Run `bash skills/jstack/scripts/skill-lint.sh <target-skill-dir>`
against the staged/sandboxed skill and require `LINT-PASS` before moving on to the commit actions below. A
`LINT-FAIL` blocks commit exactly like a failed test in Step 7 — fix the listed violations (frontmatter,
trigger-style description, `## Next skills` table, no absolute paths, size budget) and re-run before
proceeding. This does not replace the eval-gate; it is a structural check on top of it.

- **New skill:** move the staging dir into `~/jstack/skills/<name>/`, then symlink it into `.agents`, `.claude`, `.codex`, and `.hermes/skills/jstack/` per the jstack convention.
- **Hardening (in place):** back up the canonical skill, `rsync` the sandbox over it, then re-run the test against canonical to confirm identical-green — roll back the backup if not.
- **Reject:** `rm -rf` the sandbox. Report: "Discarded. No change was written to disk."

## Step 10 — Verify + Final Report

Run the committed/updated skill once against the live source to confirm it still produces the expected output. If it diverges, surface the discrepancy. Do not silently roll back.

Then output a **plain-English final summary** — no jargon, no technical terms. Structure:

1. **What this skill does** — one sentence on the skill's purpose in plain English.
2. **What was codified / hardened** — plain description of what changed ("before, an AI had to figure out X each time; now a script handles it automatically").
3. **Why it's better now** — how this makes the skill more consistent or reliable in plain English.
4. **What to expect** — 2–3 sentences on what will be noticeably different or better when using the skill going forward.
5. **Verification** — one line: which test passed and what it confirmed.

**Forbidden words in this report:** `eval`, `fixture`, `scaffold`, `deterministic`, `regression`, `fuzzy`, `harden`, `codify`. Write behavior, not implementation. Translate everything into what the user will *experience*.

End with: "Skill '<name>' is ready." (hardening: same — no need to distinguish modes in user-facing output.)

---

## Limits (be honest)

- **You are reconstructing from memory.** For a session source, the transcript is your only record. If the prototype had nuance you can't recover, say so.
- **JavaScript-rendered pages.** If the prototype used a real browser to render a SPA and your deterministic route uses static HTTP, the output may differ. Flag this before committing.
- **Fixture staleness.** The test passes against a frozen snapshot. When the source changes, the test becomes a no-op.
- **Single-task only.** One codified workflow per skill. Multi-phase pipelines with branching logic are out of scope.

## What this skill does NOT do

- Codify failed or partial attempts.
- Codify flows that fundamentally require human judgment at runtime (a genuinely fuzzy step stays fuzzy).
- **Silently change an existing skill's behavior when hardening** — the Step 1 eval-gate forbids it.
- **Metric-driven accuracy/efficiency tuning** of an existing skill — that is **`/jstack-skilltune`**.
- Remove or tombstone skills.

## Next skills

| Next | When |
|------|------|
| `skill-creator` | Step 6 — author (new) or edit (harden) the skill files. Load before writing a SKILL.md. |
| `/jstack-skilltune` | After hardening (or instead of it) to **measure + tune** accuracy/efficiency against a held-out eval set — the metric loop, not a refactor. |
| `/jstack-savetobrain` | The codified/hardened skill is durable knowledge worth ingesting into the second brain. |

Otherwise standalone — the committed (or hardened) skill is the deliverable.
