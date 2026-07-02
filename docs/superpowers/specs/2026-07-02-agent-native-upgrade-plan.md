# Agent-Native Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every skill in the jstack suite agent-native — deterministic where cheap, trigger-sharp, progressively disclosed — driven by an empirical audit of real session friction (clusters referenced by name below) and a landscape review of skill-authoring tooling.

**Architecture:** Four phases in strict order: (1) upgrade the skill-authoring tooling (jstack-skillify, jstack-skilltune) first so later work benefits from it; (2) fix the specific skills named by audit cluster verdicts; (3) package the one adopted external skill (jstack-git-guardrails, adapted from mattpocock/skills); (4) sweep every remaining skill against the conventions. All work happens on the audit branch; each phase commits with explicit paths.

**Tech Stack:** AgentSkills SKILL.md format (YAML frontmatter), bash scripts under `scripts/`, markdown references under `references/`.

## Global Constraints

- NEVER modify `skills/jstack-myvoice/` — not its SKILL.md, not its references.
- Never `git add -A`; commit explicit paths only.
- Nothing committed may contain personal identity, absolute `/Users/...` paths, or session-transcript quotes. Audit evidence stays out of the repo; clusters are referenced by name only.
- Every changed or new SKILL.md keeps/gains YAML frontmatter (`name`, `description`) and ends with a `## Next skills` table.
- New skill dirs are created ONLY by `bash skills/jstack/scripts/new-jstack-skill.sh <name> --desc "…"` (run from the repo root) — never by hand.
- Config resolution in any skill: env var → `~/.jstack/config.env` → built-in default. No hardcoded personal values.
- Do not bypass or weaken the eval gates in jstack-skillify / jstack-skilltune; behavior changes follow the skills' own eval procedure.
- Any workflow step that reaches "generate a video/clip" routes through `/jstack-vidgen`.
- `bash tools/secrets-gate.sh` must show no new hits on touched files before any push.

---

## Phase 1 — Skill-authoring tooling upgrades (jstack-skillify, jstack-skilltune)

Implements the landscape-research recommendations. Sources credited inline where a pattern is borrowed: anthropics/skills `skill-creator`, `FishSerrie/skill-evolver`, `TheStack-ai/pulser`, `obra/superpowers` writing-skills.

### Task 1: Shared deterministic skill lint (used by both skills)

**Files:**
- Create: `skills/jstack/scripts/skill-lint.sh`
- Modify: `skills/jstack/SKILL.md` (add one line documenting the linter under "Before pushing")

**Interfaces:**
- Produces: `skill-lint.sh <skill-dir>` — exits 0 with `LINT-PASS <name>`, exits 1 listing violations. Later tasks call it as the pre-commit hygiene gate in skillify Step 9 and skilltune S6.

- [ ] **Step 1: Write the linter** (pattern credit: TheStack-ai/pulser — deterministic, zero-LLM-call checks)

```bash
#!/bin/bash
# skill-lint.sh <skill-dir> — deterministic hygiene gate for jstack skills.
# Checks are structural only; behavior/quality is the eval gate's job.
set -euo pipefail
d="${1:?usage: skill-lint.sh <skill-dir>}"
f="$d/SKILL.md"
fails=()
[ -f "$f" ] || { echo "LINT-FAIL: no SKILL.md in $d"; exit 1; }
# 1. Frontmatter: opening ---, name:, description:
head -1 "$f" | grep -qx -- '---' || fails+=("missing frontmatter opening ---")
awk '/^---$/{n++} n==1 && /^name:/{found=1} END{exit !found}' "$f" || fails+=("frontmatter missing name:")
awk '/^---$/{n++} n==1 && /^description:/{found=1} END{exit !found}' "$f" || fails+=("frontmatter missing description:")
# 2. Description states WHEN to trigger (must contain a trigger cue)
grep -qiE '^description:.*(use when|invoke|trigger|when the user|when you)' "$f" || fails+=("description lacks a 'use when' trigger cue")
# 3. Next skills table present
grep -q '## Next skills' "$f" || fails+=("missing ## Next skills table")
# 4. No absolute personal paths
grep -qE '/Users/[a-z]' "$f" && fails+=("absolute /Users/ path in SKILL.md")
# 5. SKILL.md size budget (progressive disclosure)
[ "$(wc -l < "$f")" -le 500 ] || fails+=("SKILL.md over 500 lines — push detail into references/")
if [ "${#fails[@]}" -gt 0 ]; then
  printf 'LINT-FAIL %s\n' "$(basename "$d")"; printf ' - %s\n' "${fails[@]}"; exit 1
fi
echo "LINT-PASS $(basename "$d")"
```

- [ ] **Step 2: Make executable, verify against a known-good skill**

Run: `chmod +x skills/jstack/scripts/skill-lint.sh && bash skills/jstack/scripts/skill-lint.sh skills/jstack-premortem`
Expected: `LINT-PASS jstack-premortem` (if it fails, the failure lines name exactly what the sweep in Phase 4 must fix — do not weaken the linter).

- [ ] **Step 3: Document in the authoring convention**

In `skills/jstack/SKILL.md`, "Before pushing" section, add: `Run scripts/skill-lint.sh <skill-dir> on any skill you changed — it enforces frontmatter, trigger-style description, the Next-skills table, no absolute paths, and the SKILL.md size budget.`

### Task 2: jstack-skilltune — resume protocol + persistent artifacts

**Files:**
- Modify: `skills/jstack-skilltune/SKILL.md`
- Modify: `skills/jstack-skilltune/references/tune-mode.md`

Addresses clusters: "jstack-skilltune UX gaps". Changes (all additive; the eval-gate mechanics are untouched):

- [ ] **Step 1: resume.json checkpoint** (credit: skill-evolver's commit-before-verify workspace). In `tune-mode.md`, add a rule: at the end of every S-stage transition, write `<sandbox>/resume.json` with `{"stage": "<S-id>", "sandbox": "<path>", "evals_hash": "<sha of approved evals.json>", "best_version": "<id>", "baseline_score": <n>, "last_composite": <n>}`. Add a "Resuming an interrupted run" subsection: a fresh session reads resume.json and continues from `stage` — no hand-written re-brief needed.
- [ ] **Step 2: static dashboard snapshot** (credit: skill-creator `--static` viewer). In `tune-mode.md` S6 (promote/teardown), before sandbox deletion: copy the final dashboard/report with all data inlined to the target skill's `references/eval/` alongside the existing score JSONs, so the result view survives teardown.
- [ ] **Step 3: metric-explainer.md**. In `tune-mode.md` S1: when the composite metric is first constructed, also write `<sandbox>/metric-explainer.md` — a plain-English explanation of each metric component, the held-out split, and the KEEP/REVERT rule; on promote, copy it to `references/eval/`. Any later "explain the metric" ask is answered by reading this file.
- [ ] **Step 4: Verify**

Run: `grep -c 'resume.json\|metric-explainer\|references/eval' skills/jstack-skilltune/references/tune-mode.md`
Expected: ≥ 4 matches.

### Task 3: jstack-skilltune — eval rigor upgrades

**Files:**
- Modify: `skills/jstack-skilltune/references/tune-mode.md`
- Modify: `skills/jstack-skilltune/SKILL.md` (only if stage names referenced there change wording)

Addresses clusters: "jstack-skilltune UX gaps" (over-rigid assertions arm). All changes preserve the existing approval gate; they add structure, not bypasses:

- [ ] **Step 1: Typed assertion taxonomy** (credit: skill-evolver). Where evals are authored, require each assertion to declare a type: program-checkable (`contains`, `regex`, `file-exists`, `script-check`, `line-count`, `structure`) or judge-scored (`semantic`, `style`). Rule: a stylistic preference MUST be a judge-scored type, never a hard program assertion.
- [ ] **Step 2: Pre-lock intent sanity pass** (credit: skill-creator grading feedback). At the Show-eval approval gate, add one required check line per assertion: "does this assertion test something the target skill's own SKILL.md claims or implies?" Assertions that constrain unclaimed implementation details are rewritten or downgraded to judge-scored before lock.
- [ ] **Step 3: L1 quick gate** (credit: skill-evolver 3-tier fail-fast). Before each full train+held-out grading run: run `skills/jstack/scripts/skill-lint.sh` on the mutated sandbox skill plus a non-crash dry parse of any changed scripts (`bash -n` / `python3 -m py_compile`). On failure: revert the mutation immediately without spending a grading pass.
- [ ] **Step 4: AND-gate keep rule** (credit: skill-evolver 5-way gate). Extend the KEEP rule: keep a mutation only if (a) composite improves past the existing threshold AND (b) no previously-passing held-out case regresses AND (c) efficiency does not degrade beyond the documented tolerance. Otherwise REVERT.
- [ ] **Step 5: Layered mutation order** (credit: skill-evolver). Order mutation attempts: description/trigger wording → body structure → references → scripts; move to the next layer only when the current one plateaus (2 consecutive REVERTs).
- [ ] **Step 6: Verify**

Run: `grep -c 'quick gate\|AND-gate\|judge-scored\|layer' skills/jstack-skilltune/references/tune-mode.md` (case-insensitive variants acceptable — adjust grep -i)
Expected: ≥ 4 matches.

### Task 4: jstack-skillify — deterministic-by-evidence + hardening quality check

**Files:**
- Modify: `skills/jstack-skillify/SKILL.md`

- [ ] **Step 1: Repeated-work signal** (credit: anthropics skill-creator). In the codify flow's "decide the deterministic route" step, add the rule: if the same helper logic was written/re-derived in ≥2 of the session's runs or fixtures, that logic MUST be bundled as a `scripts/` file — determinism follows observed repetition, not vague preference.
- [ ] **Step 2: Blind-comparison check for harden mode** (credit: skill-creator comparator). In harden mode's verification step, alongside the existing fixture-match check, add: judge old-skill output vs hardened-script output blind (labels stripped) on the same fixture; the hardened version must be judged equal-or-better to pass.
- [ ] **Step 3: Mode routing trigger-eval** (credit: skill-creator trigger optimization). Add a short "Routing self-check" reference block: ~12 canonical phrasings mapped to codify / harden / tune (tune → route to jstack-skilltune), used once when either skill's description changes to confirm the boundary discriminates. Include the mapping table inline in the SKILL.md (it is small).
- [ ] **Step 4: Description=when rule + lint gate on commit** (credit: obra/superpowers writing-skills). In the final commit step of both modes: run `bash skills/jstack/scripts/skill-lint.sh <target-skill-dir>` and require LINT-PASS; add the rule that any authored/tuned `description:` states WHEN to invoke, never a summary of internal workflow steps (documented failure mode: agents follow the summary and skip the body).
- [ ] **Step 5: Verify**

Run: `grep -ci 'skill-lint\|blind\|repeated' skills/jstack-skillify/SKILL.md`
Expected: ≥ 3 matches.

### Task 5: Phase 1 commit

- [ ] **Step 1: Lint both changed skills**

Run: `bash skills/jstack/scripts/skill-lint.sh skills/jstack-skillify && bash skills/jstack/scripts/skill-lint.sh skills/jstack-skilltune && bash skills/jstack/scripts/skill-lint.sh skills/jstack`
Expected: three `LINT-PASS` lines.

- [ ] **Step 2: Commit with explicit paths**

```bash
git add skills/jstack-skillify skills/jstack-skilltune skills/jstack
git commit -m "feat(skillify,skilltune): resume protocol, typed assertions, quick gate, AND-gate keep rule, blind-compare hardening, shared skill-lint"
```

---

## Phase 2 — Cluster-verdict fixes (named clusters → named skills)

One task per target skill. Every task ends with `skill-lint.sh` on the touched skill. Clusters with verdict `nothing` require no task: "Edit/Write tool-use guard friction", "Harness rejection/malformed tool-call friction", "jstack-myvoice/msgdraft tone churn" (skill is off-limits), "Bare /model re-invocation" (personal-preference config — deferred), "Brave-CDP relaunch bugs" (skill lives outside this repo — deferred), "LinkedIn Sales Navigator rate-limiting" (one-off).

### Task 6: jstack-handoff — goal-mode template, repo/cwd block, close-out pairing, completeness

Clusters: "jstack-handoff completeness and goal-mode boilerplate gaps", "Cross-repo CWD / repo-routing confusion", "Session close-out requires manual savetobrain + handoff pairing".

**Files:**
- Modify: `skills/jstack-handoff/SKILL.md`
- Create: `skills/jstack-handoff/references/goal-mode-template.md`

- [ ] **Step 1: goal-mode-template.md** — a fill-in-the-blanks template for the autonomous /goal prompt, so the recurring hand-typed preamble is generated, not retyped. Content skeleton (complete file):

```markdown
# Goal-mode prompt template

Fill the {SLOTS}; everything else ships verbatim with the handoff.

---
/goal {ONE-SENTENCE GOAL with a single verifiable stop condition: command + expected output}
You have NO memory of the planning session — read {HANDOFF-FILE-PATH} first; it is the
self-contained state file. Run from {REPO-PATH}; all relative paths resolve against it.
Execute autonomously, milestone by milestone: spawn subagents for each milestone's heavy
work, each returning a short summary; then a SEPARATE checker subagent verifies the
milestone's done-condition by running its stated command and matching the stated output
(maker ≠ checker). Keep the main context lean: orchestrate and review; never do heavy work
inline. Re-read the plan's constraints at the start of every milestone. After each
milestone update the plan's Progress/Decision Log so you can recover from compaction.
Resolve ambiguities yourself and log them. Commit only as the plan directs. Never stop to
ask. Stop only when: {STOP CONDITION}.
---

Every goal handoff document MUST open with:
- Repo + working directory block: "Run from `{REPO}`; paths relative to it."
- The stop-condition command and its exact expected output.
```

- [ ] **Step 2: SKILL.md edits** — (a) goal mode instructs: generate the prompt from `references/goal-mode-template.md`; (b) ALL modes: the handoff document MUST open with an explicit repo + working-directory block ("Run from `<repo>`; all paths relative to it") — cross-repo continuations break without it; (c) add a completeness checklist before saving: every decision agreed this session, every in-flight artifact path, every unresolved question — re-scan the conversation for "we decided/agreed" statements; (d) close-out pairing: before writing the handoff, check whether the session produced durable knowledge not yet captured — if so, prompt the `/jstack-savetobrain` hop first; (e) ensure the `## Next skills` table includes `/jstack-savetobrain` (durable knowledge produced) alongside existing hops.
- [ ] **Step 3: Verify**

Run: `grep -c 'goal-mode-template\|working-directory\|savetobrain' skills/jstack-handoff/SKILL.md && bash skills/jstack/scripts/skill-lint.sh skills/jstack-handoff`
Expected: ≥ 3 matches; `LINT-PASS jstack-handoff`.

### Task 7: jstack-cdesign — deterministic finalize_plan fix + handoff completeness

Clusters: "DesignSync finalize_plan rejects missing deletes field", "jstack-cdesign context and handoff-agency gaps", "Playwright MCP sandbox friction" (preview arm).

**Files:**
- Modify: `skills/jstack-cdesign/SKILL.md` (and its references if the DesignSync call sequence lives there)

- [ ] **Step 1:** Wherever the skill instructs calling DesignSync `finalize_plan`, add the hard rule: ALWAYS pass a `deletes` array — empty (`"deletes": []`) when nothing is deleted. This is a known recurring validation rejection.
- [ ] **Step 2:** Handoff-package completeness checklist: the package pushed to Claude Design MUST include the full spec, all verbatim decisions from the working session, and any prior-round feedback already given — enumerate these as required sections, and instruct the agent to push via the DesignSync connector itself rather than asking the user to relay.
- [ ] **Step 3:** Local preview rule (shared with Task 8): when visually verifying any local HTML artifact, never use `file://` URLs (blocked); serve with `python3 -m http.server <port>` from the artifact's directory and navigate to `http://localhost:<port>/…`; write screenshots only inside the session's allowed scratch directory.
- [ ] **Step 4: Verify**

Run: `grep -ci 'deletes\|http.server' skills/jstack-cdesign/SKILL.md && bash skills/jstack/scripts/skill-lint.sh skills/jstack-cdesign`
Expected: ≥ 2 matches; `LINT-PASS jstack-cdesign`.

### Task 8: jstack-html — local preview automation

Cluster: "Playwright MCP sandbox friction (file:// blocked, screenshots outside allowed roots)".

**Files:**
- Modify: `skills/jstack-html/SKILL.md`

- [ ] **Step 1:** In the render/verify flow, add the deterministic preview rule: serve the output dir with `python3 -m http.server` on a fixed default port (config: `JSTACK_PREVIEW_PORT` → `~/.jstack/config.env` → `8931`), navigate to `http://localhost:<port>/<file>.html`, and kill the server after capture. Never `file://`. Screenshots go to the session scratch directory (always allowed), then are moved if needed.
- [ ] **Step 2: Verify**

Run: `grep -c 'http.server' skills/jstack-html/SKILL.md && bash skills/jstack/scripts/skill-lint.sh skills/jstack-html`
Expected: ≥ 1 match; `LINT-PASS jstack-html`.

### Task 9: jstack-focus — proactive verbosity calibration

Cluster: "jstack-focus reactive-invocation / verbosity miscalibration".

**Files:**
- Modify: `skills/jstack-focus/SKILL.md`

- [ ] **Step 1:** Add: (a) a "stay on" rule — once invoked in a session, compression persists until explicitly turned off (the recurring pattern is re-invocation because the effect decayed); (b) a floor guard — never compress away direct answers to questions the user asked and not-yet-actioned decisions (over-compression was reported); (c) description keeps its trigger list intact.
- [ ] **Step 2: Verify**

Run: `bash skills/jstack/scripts/skill-lint.sh skills/jstack-focus`
Expected: `LINT-PASS jstack-focus`.

### Task 10: jstack-vision — capability discoverability

Cluster: "jstack-vision capability discoverability".

**Files:**
- Modify: `skills/jstack-vision/SKILL.md`

- [ ] **Step 1:** The frontmatter `description:` and the opening line must state the full media coverage explicitly — images, audio, VIDEO, and PDFs — so "does it do video?" is answered by the picker line without invocation. Add a short "What it handles" table (media type → supported → notes) near the top.
- [ ] **Step 2: Verify**

Run: `grep -ci 'video' skills/jstack-vision/SKILL.md && bash skills/jstack/scripts/skill-lint.sh skills/jstack-vision`
Expected: ≥ 2 matches; `LINT-PASS jstack-vision`.

### Task 11: jstack-adscan — reliability hardening

Cluster: "jstack-adscan reliability gaps".

**Files:**
- Modify: `skills/jstack-adscan/SKILL.md` (+ its scripts if present)

- [ ] **Step 1:** Add a verification pass: after counting active ads, re-query once and compare; on mismatch, report both counts with a low-confidence flag instead of a single unverified number. Add friendly error mapping: no raw tracebacks — each failure mode (no target resolved, auth missing, empty result) gets a one-line actionable message. Config values resolve env → `~/.jstack/config.env` → default.
- [ ] **Step 2: Verify**

Run: `bash skills/jstack/scripts/skill-lint.sh skills/jstack-adscan`
Expected: `LINT-PASS jstack-adscan`.

### Task 12: jstack-vidgen — argument validation + prompt-guide enforcement

Cluster: "jstack-vidgen reliability and prompt-quality gaps".

**Files:**
- Modify: `skills/jstack-vidgen/SKILL.md` (+ `references/` as needed)

- [ ] **Step 1:** (a) Pre-flight validation: before any backend call, validate duration/resolution/model against a per-backend capability table (add/extend one in `references/`) and fail fast with the allowed values — no raw argparse errors; (b) prompt-quality gate: the crafted prompt MUST follow the matching prompt guide in `references/prompt-guides/` — the skill checks the guide's minimum structure (shot, motion, camera, duration) before submitting; (c) keep the existing ask-duration+resolution and show-exact-prompt rules prominent.
- [ ] **Step 2: Verify**

Run: `grep -ci 'capabilit\|prompt-guide' skills/jstack-vidgen/SKILL.md && bash skills/jstack/scripts/skill-lint.sh skills/jstack-vidgen`
Expected: ≥ 2 matches; `LINT-PASS jstack-vidgen`.

### Task 13: jstack-savetobrain + jstack-brainwork — synthesis capture, supersede, lint-at-ingest

Cluster: "Second-brain capture/lint/supersede model gaps".

**Files:**
- Modify: `skills/jstack-savetobrain/SKILL.md`
- Modify: `skills/jstack-brainwork/SKILL.md`

- [ ] **Step 1 (savetobrain):** (a) capture-source rule: a conversation-content save records the agent's synthesized understanding (conclusions, decisions, the WHY), not only the user's verbatim words — add an explicit "what to write" spec; (b) supersede mechanism: when a save updates/contradicts an earlier saved decision, mark the relationship explicitly (a `supersedes:` line naming the older item) so stale facts are discoverable; (c) ingest-time structure check: the raw drop must match the brain's card structure before write (prevents the lint backlog from growing).
- [ ] **Step 2 (brainwork):** align its lint step with the same card-structure rules and have it surface `supersedes:` chains during processing.
- [ ] **Step 3: Verify**

Run: `grep -c 'supersede' skills/jstack-savetobrain/SKILL.md skills/jstack-brainwork/SKILL.md && bash skills/jstack/scripts/skill-lint.sh skills/jstack-savetobrain && bash skills/jstack/scripts/skill-lint.sh skills/jstack-brainwork`
Expected: ≥ 1 match per file; two `LINT-PASS` lines.

### Task 14: jstack-excalidraw — output-quality gate

Cluster: "jstack-excalidraw output-quality churn".

**Files:**
- Modify: `skills/jstack-excalidraw/SKILL.md` (+ `references/playbook.md` if that is where the review loop lives)

- [ ] **Step 1:** Make the visual self-review loop mandatory, not optional: after render, the agent inspects the exported PNG against a concrete checklist (no overlapping elements, readable labels at 100%, visual hierarchy matches the argument, non-trivial layout — not a single row of boxes) and iterates up to the documented cap before presenting. Diagrams failing the checklist are not shown as final.
- [ ] **Step 2: Verify**

Run: `bash skills/jstack/scripts/skill-lint.sh skills/jstack-excalidraw`
Expected: `LINT-PASS jstack-excalidraw`.

### Task 15: Phase 2 commit

- [ ] **Step 1: Confirm myvoice untouched**

Run: `git diff --name-only audit-baseline..HEAD -- skills/jstack-myvoice | wc -l` and `git status --porcelain -- skills/jstack-myvoice | wc -l`
Expected: `0` and `0`.

- [ ] **Step 2: Commit with explicit paths**

```bash
git add skills/jstack-handoff skills/jstack-cdesign skills/jstack-html skills/jstack-focus \
        skills/jstack-vision skills/jstack-adscan skills/jstack-vidgen \
        skills/jstack-savetobrain skills/jstack-brainwork skills/jstack-excalidraw
git commit -m "fix(skills): cluster-verdict fixes — handoff goal template + repo block, cdesign deletes rule, html/cdesign http.server preview, focus persistence, vision video visibility, adscan verification pass, vidgen pre-flight validation, savetobrain supersede + synthesis capture, excalidraw quality gate"
```

---

## Phase 3 — Package jstack-git-guardrails (adapted from mattpocock/skills)

### Task 16: Scaffold and author jstack-git-guardrails

**Files:**
- Create (via scaffolder): `skills/jstack-git-guardrails/SKILL.md`
- Create: `skills/jstack-git-guardrails/scripts/git-guardrails-hook.sh`

**Interfaces:**
- Produces: a one-time-setup skill that installs a Claude Code `PreToolUse` hook blocking destructive git commands.

- [ ] **Step 1: Scaffold (never hand-create)**

Run: `bash skills/jstack/scripts/new-jstack-skill.sh jstack-git-guardrails --desc "Install a PreToolUse hook that mechanically blocks destructive git commands (push, reset --hard, clean -f, branch -D, checkout .) before they execute. Use when setting up git safety guardrails, 'protect my repo from destructive git', or after any near-miss with a destructive git command."`
Expected: canonical dir created + harness symlinks; starter SKILL.md present.

- [ ] **Step 2: Write the hook script** (adapt, do not copy verbatim; credit mattpocock/skills in the SKILL.md)

```bash
#!/bin/bash
# git-guardrails-hook.sh — Claude Code PreToolUse hook (matcher: Bash).
# Reads the tool call JSON on stdin; blocks destructive git commands.
# Adapted from mattpocock/skills git-guardrails. Exit 2 = block with message.
set -euo pipefail
cmd=$(jq -r '.tool_input.command // empty' 2>/dev/null || true)
[ -z "$cmd" ] && exit 0
block() { echo "git-guardrails: blocked destructive command ($1). Run it manually if truly intended." >&2; exit 2; }
echo "$cmd" | grep -qE 'git (push --force|push -f)( |$)'        && block "force push"
echo "$cmd" | grep -qE 'git reset --hard'                        && block "reset --hard"
echo "$cmd" | grep -qE 'git clean -[a-z]*f'                      && block "clean -f"
echo "$cmd" | grep -qE 'git branch -D'                           && block "branch -D"
echo "$cmd" | grep -qE 'git (checkout|restore) \.'               && block "checkout/restore ."
exit 0
```

- [ ] **Step 3: Author the SKILL.md body.** Sections: what the hook does (table: pattern → why blocked); install procedure — copy the script to `~/.jstack/hooks/` and register it in the harness settings as a `PreToolUse` hook with a `Bash` matcher (show the exact settings JSON snippet); how to verify (attempt `git reset --hard` in a scratch repo → expect the block message); how to uninstall; credit line: "Adapted from mattpocock/skills (git-guardrails)". Plain `git push` is intentionally NOT blocked by the hook — pushing is a normal, user-directed operation in this suite; only force-push variants are blocked. End with `## Next skills` table (row: standalone — one-time setup; companion `/jstack-setup`).
- [ ] **Step 4: Verify**

Run: `bash -n skills/jstack-git-guardrails/scripts/git-guardrails-hook.sh && bash skills/jstack/scripts/skill-lint.sh skills/jstack-git-guardrails`
Expected: no syntax errors; `LINT-PASS jstack-git-guardrails`.

- [ ] **Step 5: Commit**

```bash
git add skills/jstack-git-guardrails
git commit -m "feat(jstack-git-guardrails): package git-safety PreToolUse hook, adapted from mattpocock/skills"
```

---

## Phase 4 — All-skill optimization sweep

Every skill dir under `skills/` EXCEPT `jstack-myvoice`. Skills already handled above are re-checked only by the linter, not re-edited. Sweep in batches; a separate checker verifies each batch (maker ≠ checker).

**Audit criteria per skill (apply, or record "no change needed: <reason>"):**
1. AgentSkills spec: frontmatter valid; `description:` is trigger-rich and states WHEN (invalid frontmatter has silently broken skill loading before — treat as highest-severity).
2. jstack conventions: `## Next skills` table present and lists real hops; video-gen hops route via `/jstack-vidgen`; config via env → `~/.jstack/config.env` → default; no hardcoded personal values or absolute paths.
3. Progressive disclosure: SKILL.md lean (≤500 lines); details → `references/`; deterministic mechanics → `scripts/`.
4. `skills/jstack/scripts/skill-lint.sh <dir>` passes.

**Batches (5 per batch, alphabetical; batch 8 short):**
- Batch 1: `jstack`, `jstack-adscan`, `jstack-asciiexplain`, `jstack-autoresearch`, `jstack-brainwork`
- Batch 2: `jstack-cdesign`, `jstack-challenge`, `jstack-claude-find`, `jstack-coldmsg`, `jstack-excalidraw`
- Batch 3: `jstack-focus`, `jstack-ggdesign-init`, `jstack-grill-with-docs`, `jstack-grillme`, `jstack-gtm`
- Batch 4: `jstack-handoff`, `jstack-handoff-from-claude`, `jstack-html`, `jstack-imgen`, `jstack-init`
- Batch 5: `jstack-last30days`, `jstack-linkedin`, `jstack-linkedin-leads`, `jstack-linkedin-salesnav`, `jstack-linkedin-send`
- Batch 6: `jstack-opencli`, `jstack-otagallery`, `jstack-premortem`, `jstack-research-router`, `jstack-savetobrain`
- Batch 7: `jstack-savetobrain-from-claude`, `jstack-schedule-claude`, `jstack-setup`, `jstack-skillify`, `jstack-skilltune`
- Batch 8: `jstack-teach`, `jstack-vercel-debug`, `jstack-vidgen`, `jstack-vision`, `jstack-git-guardrails`

### Task 17 (repeat per batch): sweep batch N

- [ ] **Step 1:** For each skill in the batch: read its SKILL.md (and skim references/scripts), apply the four criteria, either edit minimally or record "no change needed: <reason>". Record every outcome (improved: why+how / unchanged: reason) in the audit workbench outcomes file as you go.
- [ ] **Step 2:** Run `bash skills/jstack/scripts/skill-lint.sh skills/<name>` for each — all must print `LINT-PASS`.
- [ ] **Step 3:** Checker subagent re-runs the linter over the batch and spot-reads one diff.
- [ ] **Step 4:** Commit the batch with explicit paths:

```bash
git add skills/<name-1> skills/<name-2> skills/<name-3> skills/<name-4> skills/<name-5>
git commit -m "chore(sweep): agent-native audit batch N — <one-line summary>"
```

**Full skilltune eval loops are NOT run during the sweep** (cost discipline); only cluster-verdict work above plus lint/structure fixes. Skills whose only viable improvement would require an eval-gated behavior change get that noted as a follow-up instead.

---

## Completion checks (run after all phases)

- [ ] `git diff --name-only audit-baseline..HEAD -- skills/jstack-myvoice | wc -l` → `0`
- [ ] Every changed SKILL.md contains `## Next skills`: `for f in $(git diff --name-only audit-baseline..HEAD | grep 'SKILL.md$'); do grep -L '## Next skills' "$f"; done` → no output
- [ ] `bash tools/secrets-gate.sh` → no new hits on files changed since `audit-baseline`
- [ ] README catalog updated with `jstack-git-guardrails` and committed
