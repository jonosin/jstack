---
name: jstack-sf-learn
description: Promote what a passed StayFrame reel proved into canon, so the next resort starts ahead of this one. Use when Jono says /jstack-sf-learn, "promote to canon", "what did we learn", "save the method", "the reel passed — capture it", or right after a reel clears every GATE B and is assembled. Diffs the approved brief's actual method against playbook/, surfaces what is NOT yet canon, and on Jono's confirm writes the rule into the governing playbook + appends playbook/DECISIONS.md, and runs the lint. Method history lives in canon (DECISIONS.md) only — it does NOT copy methods to the brain. Works for still (image) methods and video methods alike. Never writes canon without a confirm.
---

# jstack-sf-learn — close the loop (reel → canon)

The pipeline ends at a finished reel. The **system** only improves when what that reel proved is
written back to canon. Without this step a working method (e.g. the single-start-frame Veo move that
beat the flat-zoom baseline) stays stranded in one brief and the next resort re-invents it. This skill
is that promotion, made **invokable** — not a thing the agent has to remember to offer.

All paths under `~/ventures/stayframe/` (abbrev `SF`).

## When to run
- Jono invokes `/jstack-sf-learn` (or "promote to canon", "what did we learn", "save the method").
- `jstack-sf-new`'s produce phase nudges it after a reel clears every GATE B and is assembled.
- Either way the trigger is the same: a reel just **passed** and may carry a method canon doesn't have.

## 1. Resolve the target reel
- If Jono names it, use that. Else pick the most recently touched `SF/qa/reels/<client>__<reel>.json`
  whose `steps` show the gates passed (gateb true across beats / `saved`).
- Load: the reel state `SF/qa/reels/<reel_id>.json`, the brief `SF/clients/<slug>/briefs/*-brief.md`
  it was produced from, and (if present) the baseline it beat (`renders/<subdir>/beat-N-baseline.mp4`)
  for the evidence line.

## 2. Diff the brief's actual method against canon
A learning can be a **still (image)** method or a **video** method — promote it to the doc that governs
that modality + engine. Read what the brief actually did, then compare against the governing canon docs:

| Brief signal | Canon to check |
|---|---|
| `still_model` / `clip_model` / `clip_type` frontmatter | `playbook/index.md §2` engine matrix — is this engine+lane a row? |
| the **still** prompt method (how the still was made/edited) | `playbook/prompts/still-prompt-system.md` (reference-over-text; NB Pro / GPT Image 2) |
| the camera method (how the move is described in the CLIP prompts) | `playbook/prompts/reel-prompt-system.md` (camera lexicon, §single-start-frame, first→end rule) + `playbook/prompts/end-frame-method.md` |
| prompt structure / block order / density (per engine) | `playbook/prompts/reel-prompt-system.md` (video) / `playbook/prompts/still-prompt-system.md` (image) — formats are per-engine |
| negatives that were **added or removed** (e.g. handheld pulled out of negatives) | the engine's prompt doc — negative-prompt floor |
| any new red-line / authenticity handling | `playbook/produce/quality-gate.md` |

A **candidate learning** = anything the passed brief did that canon does not yet say (a new engine
lane, a new camera method, a changed negative floor, a new prompt pattern), OR anything canon says
that this reel **contradicted and won** (canon is now wrong/too-narrow and should be demoted/scoped).

## 3. Surface candidates + CONFIRM (the gate)
Present each candidate terse: *what's new · which playbook doc it belongs in · the one-line rule to
write · the evidence (this reel/beat beat that baseline)*. Recommend, then **wait for Jono's yes**.
Never write canon on a bare invocation without confirmation — promotion is a real edit to the rules
every future reel follows. If nothing is new (the reel just used existing canon well), say so, write
nothing to the playbook, and skip to step 5.

## 4. On confirm — write canon (operational) + log the decision
For each confirmed learning:
1. **Edit the governing playbook doc** so the rule is now the default the next reel inherits — a new
   `index.md §2` matrix row, a new `prompts/reel-prompt-system.md` section, a scoped/demoted old rule, etc.
   Keep it terse and machine-parseable; match the doc's existing style.
2. **Append** an entry to `SF/playbook/DECISIONS.md` (append-only; never rewrite prior entries) using
   the template below.
3. **If you added or renamed a playbook file, register it in `index.md §4`** (`file · role · freshness`)
   — `index.md` is the one map; a doc that isn't listed there is invisible to every agent.
4. **Run the lint — it is the guarantee, not your memory:**
   `python3 ~/ventures/stayframe/tools/sf_lint.py`. Its **ORPHAN check globs `playbook/*.md` and fails,
   naming the file**, if any playbook isn't referenced in `index.md`; its ENGINE check fails if a brief
   names an engine not in the matrix. Add the missing §4 row (or matrix row) and re-run until exit 0.
   The same lint runs at commit (pre-commit hook), so an unregistered playbook **cannot ship** even if
   this step is skipped — registration is mechanically enforced, not memory-dependent.

### `DECISIONS.md` entry template
```
## YYYY-MM-DD — <short method name>
- **Changed:** <what canon now says that it didn't before / what was demoted>
- **Why:** <the failure or win that forced it — one or two sentences>
- **Evidence:** <reel id + beat(s)> beat <baseline/old method>; <where the renders live>
- **Canon touched:** <playbook files edited, with the section>
- **Fallback:** <when to use the old method / the exception slot, if any>
```

## 5. Canon is the home — do NOT copy methods to the brain
The rule and its why both live in the playbook doc + `DECISIONS.md`. The next session reads canon and
uses the method — that IS the propagation mechanism; a brain copy would only duplicate and drift.
**Skip brain capture for craft methods.** (The brain is for business/strategy decisions — a different
tool, plain `/jstack-savetobrain`, not this skill. A craft method is never that.)

## Guardrails / separation
- **Confirm before any canon write.** This skill proposes; Jono approves; then it writes.
- **Method (rule + why) → `playbook/` + `DECISIONS.md` only.** No brain copy — the next session reads canon and uses it; duplicating to the brain just drifts. Brain is for business/strategy, not craft.
- **Route, don't duplicate.** When you write canon, keep the plugin routing: record the StayFrame
  rule/delta and point to `video-prod-skills:<skill>` (per `index.md §3`) for the generic
  technique. Never copy the plugin's craft into the playbook — that re-creates the very divergence the
  routing model removes.
- **`DECISIONS.md` is append-only** — history, never rewritten. Supersession is a new entry that
  scopes/demotes the old, not an edit of the old.
- **Don't touch artifacts.** This skill edits canon + the decision log only; renders/briefs stay as
  the immutable record of what was produced.
- The other skills stay the source of truth for their jobs: `jstack-sf-new` runs the pipeline,
  `jstack-sf-check` applies dashboard feedback, the `playbook/` docs hold the rules this skill writes.

## Next skills

| Next | When |
|------|------|
| `/jstack-sf-new <resort>` | Canon is updated — start the next resort, now ahead of this one. |
| `/jstack-sf` | Want a read-only status of where things stand across resorts. |
