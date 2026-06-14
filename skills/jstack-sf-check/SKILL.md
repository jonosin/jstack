---
name: jstack-sf-check
description: Check and apply what Jono saved in the StayFrame QA dashboard, then iterate the reel. Use when Jono says /jstack-sf-check, "check the dashboard", "check what I saved / what changed", "I made changes in the dashboard", "I left feedback", "check my feedback on <reel>", "iterate the reel", or any time he has been editing reference / still / clip directives or ticking checklist steps in the runsheet and wants the agent to act on them. Reads qa/reels/<reel>.json, reports what changed, auto-applies the feedback to the brief (re-pick/add refs, rewrite NB Pro / Veo prompts preserving craft rules), clears handled entries, then tells Jono to reload.
---

# jstack-sf-check — read the dashboard, apply, iterate

Jono directs from the QA dashboard; you maintain the brief. He never hand-edits prompts. This
skill is the "I saved something, go look" trigger: it reads the reel's saved state, **auto-applies**
the actionable feedback to the brief, clears what it handled, and reports back. The feedback entries
ARE the work queue — they persist on disk until you clear them, so there is no cursor to track.

Mode: **report + auto-apply** (Jono's choice). Apply without asking; surface only taste calls you
genuinely can't resolve from the note.

## What you're reading

Reel state lives at `~/ventures/stayframe/qa/reels/<reel_id>.json`, `reel_id = <client>__<reel>`
(e.g. `serenity-sands__sands-v3`). Shape:

```json
{
  "reel_id": "serenity-sands__sands-v3",
  "steps":    { "b1-still": true, "b1-gatea": true },     // checklist ticks (informational)
  "feedback": { "b4-still": { "action": "edit", "note": "angle too flat", "updated_at": "..." } }
}
```

- **`feedback` keys** = `b<N>-ref` | `b<N>-still` | `b<N>-clip`. `ref` action is `swap` or `add`;
  `still`/`clip` action is `edit`. **A note is required to act** — an entry with `note: ""` is a
  no-op (Jono clicked the field but typed nothing); report it as "flagged, no note" and skip.
- **`steps` keys** = `b<N>-` + `refok` | `still` | `gatea` | `clip` | `gateb` | `saved`
  (ref-approved → still → GATE A → clip → GATE B → saved). Read-only here; report progress, don't act.

## Steps

### 1. Locate the reel(s)
Scan `~/ventures/stayframe/qa/reels/*.json`. Act on every reel with at least one actionable
(non-empty-note) feedback entry. If Jono named a reel, scope to it. Map `reel_id` → brief file via
`curl -s localhost:7777/api/reels` (gives `reel_id`, `client`, `brief_file`); if the dashboard is
down, grep `clients/<client>/briefs/*-brief.md` frontmatter for the matching `client` + `reel`.

### 2. Report what changed (before touching anything)
List, per beat: the pending feedback (target · action · note) you're about to apply, plus a one-line
checklist snapshot (e.g. `Beat 1: still ✓ · GATE A ✓ · clip pending`). Keep it tight.

### 3. Apply to the brief (auto)
Per the contract in `~/ventures/stayframe/clients/AGENTS.md` § Reel production and the
`jstack-sf-new` skill (produce phase):
- **`b<N>-ref` + `swap`** → re-pick that beat's reference from `clients/<client>/catalog.json` per
  the note (a described shot like "wider sunset" or an explicit id), edit the beat heading's
  `ref \`ID\``.
- **`b<N>-ref` + `add`** → add the requested id(s) to that beat heading.
- **`b<N>-still` / `b<N>-clip` + `edit`** → rewrite that prompt block per the note, **preserving the
  craft rules**: grade + property anchors verbatim, camera contract, negative blocks, continuity
  anchors, and any prop variant already adopted. Jono describes the problem in plain language; you do
  the correct rewrite — **never raw-paste his note into the prompt.** If a beat's still is reprised
  by a later beat (e.g. an outro), sync the reprise too.

One lever at a time matches the brief's own iteration rule. If a note is genuinely ambiguous on a
taste call (which of two refs, how dramatic an angle), make the best call and flag it in the report
rather than blocking.

### 4. Clear handled entries
For each entry you applied, clear it so it doesn't re-trigger. Prefer the API when the dashboard is
up (keeps the server's view consistent):
```bash
curl -s -X POST http://localhost:7777/api/reel-feedback \
  -H 'Content-Type: application/json' \
  -d '{"reel_id":"<reel_id>","key":"b4-still","note":"","action":""}'
```
Empty note + empty action deletes the key. If the dashboard is down, edit the JSON file directly
(remove the handled key, keep the rest).

### 5. Report back + reload
Summarize: what changed, what you applied (name the new angle/ref in a line), what's left unhandled
and why. Tell Jono to **reload the dashboard** — it re-parses the brief live, so no restart is needed
for prompt/ref edits (restart `node server.js` only if `server.js` itself changed). Don't commit the
brief unless Jono asks; let him eyeball the result first.

## Notes
- Reel-agnostic: works for any `clients/*/briefs/*-brief.md` with the runsheet structure.
- This skill does not generate images or launch the dashboard — `jstack-sf-new` runs the pipeline
  (harvest → screen → catalog → creative → produce). This one is purely the read → apply → clear loop.
