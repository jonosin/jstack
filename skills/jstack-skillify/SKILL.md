---
name: jstack-skillify
description: "Codify a successful interactive session into a permanent, deterministic skill. Walks back through the conversation, extracts the working path, and codifies it — the agent decides the implementation. Triggered by: 'skillify this', 'codify this', 'save this as a skill', 'make this permanent', 'turn this into a skill.'"
---

# jstack-skillify

The productivity multiplier. You just did something that worked — pulled data from a page, ran a multi-step lookup, transformed some output. jstack-skillify codifies the working path into a deterministic skill so next time it runs in one shot with no re-discovery. Every successful prototype is a one-time cost.

**Fully harness-agnostic.** This skill does not prescribe tools, languages, or file layouts. It runs the codification workflow. You (the agent) ran the prototype — you decide the best deterministic route.

## Iron contract

Skills are user-trust artifacts. A broken skill erodes confidence. Write to a temp dir, test there, and only move into the final path on test pass plus explicit user approval. On either failure, remove the temp dir entirely. No "almost shipped" state.

---

## Step 1 — Provenance guard

Walk back through the conversation, at most 10 agent turns, and identify the most recent successful multi-step interaction that produced a useful, repeatable output. It must be:

- Bounded: you can identify where it started, what steps ran, and what the accepted output was.
- Successful: the user accepted the result without invalidating it.
- Codifiable: the steps can be expressed deterministically.

If you cannot find one, refuse:

> "No recent codifiable session found. Run the thing first, then say /skillify."

Stop. Do not synthesize from chat fragments or failed attempts.

If the conversation has drifted past the candidate, ask once:

> "The last codifiable session was '<what you did>' a few turns back. Skillify that?"

A "yes" continues. Anything else: refuse.

## Step 2 — Propose name

Extract a short, descriptive skill name: lowercase letters/digits/dashes, ≤32 chars, starts with a letter, no consecutive dashes. Follow jstack convention: prefix with `jstack-`.

Ask the user to confirm the name. Warn if it collides with an existing skill.

## Step 3 — Decide the deterministic route

You ran the prototype. You know what worked. Now decide the simplest deterministic path that reproduces it.

This is the only constraint: the codified skill must run deterministically without human judgment. No interactive prompts, no "figure it out" steps, no re-discovery. A future agent (or cron job) should be able to invoke it and get the same shape of output.

Beyond that, you decide everything. A shell pipeline. A Python script. A sequence of API calls. Whatever matches what actually worked. Use whatever tools, languages, and libraries make sense. The prototype proved the approach — codify exactly that approach.

## Step 4 — Capture a fixture

Save a snapshot of the input data the prototype operated on. The test in step 6 will replay against this snapshot so the parse/transform logic is verified independently of live network calls.

If the prototype fetched from a URL, save the response body. If it transformed local files, save a copy of those files. Whatever the input was, freeze it.

## Step 5 — Write the test

A minimal test that exercises the codified skill against the fixture. It must assert something meaningful about the output — shape, key fields, presence of expected data — not just that the script didn't crash.

Keep it simple. If the skill is a shell script, the test can be a shell script that runs it and checks the output. If it's Python, use plain assert or pytest. Match the test format to the skill format.

## Step 6 — Author the skill files (delegate to skill-creator)

You have the deterministic route, the fixture, and the test. Now turn them into a proper skill. **Load the `skill-creator` skill** and follow its conventions for file structure and SKILL.md format. Specifically:

- Use `init_skill.py` from skill-creator to scaffold the staging directory under `/tmp/jstack-skillify-<name>/`.
- Follow skill-creator's frontmatter spec: only `name` and `description` in YAML. The description must include both what the skill does and when to use it — that is the triggering mechanism.
- Place the codified script in `scripts/`, the fixture in `references/` or alongside the test, and the test wherever it makes sense given the skill's structure.
- Keep SKILL.md body lean. A few sentences on what the skill produces and how to run it. No conversation context.

skill-creator owns the authoring conventions. jstack-skillify owns the codification logic. Use both.

## Step 7 — Run the test against staging

Run the test inside the staging directory. If it fails and the failure is a fixable logic bug, fix it and retry — at most twice. Show the diff before each retry.

If still failing after two retries, or the failure is environmental, remove the staging directory and report the failure. No on-disk artifact.

## Step 8 — Approval gate

Tests passed. Ask the user:

- **Commit it.** Moves the staged skill into `~/jstack/skills/<name>/` and symlinks across harnesses.
- **Show me first.** Print the SKILL.md and the main script, then re-ask (without the show option).
- **Discard.** Remove the staging directory. Nothing lands on disk.

## Step 9 — Commit or discard

If approved: move the staging directory into `~/jstack/skills/<name>/` (the canonical jstack location), then symlink it into `.agents`, `.claude`, `.codex`, and `.hermes/skills/jstack/` using the jstack convention. The `new-jstack-skill.sh` script handles the symlinks — it is idempotent.

If rejected: `rm -rf /tmp/jstack-skillify-<name>/`. Report: "Discarded. No skill was written to disk."

## Step 10 — Verify

Run the committed skill once against the live source to confirm it still produces the expected output. If it diverges, surface the discrepancy. Do not silently roll back.

End with: "Skill '<name>' committed at ~/jstack/skills/<name>/."

---

## Limits (be honest)

- **You are reconstructing from memory.** The conversation transcript is your only record of what happened. If the prototype had nuance you can't recover, say so.
- **JavaScript-rendered pages.** If the prototype used a real browser to render a SPA, and your chosen deterministic route uses static HTTP, the output may differ. Flag this before committing.
- **Fixture staleness.** The test passes against a frozen snapshot. When the source changes, the test becomes a no-op.
- **Single-task only.** One codified workflow per skill. Multi-phase pipelines with branching logic are out of scope.

## What this skill does NOT do

- Codify failed or partial attempts.
- Codify flows that fundamentally require human judgment at runtime.
- Edit existing skills.
- Remove or tombstone skills.

## Next steps

| Next | When |
|------|------|
| `skill-creator` | Step 6 — authoring the skill files. Load it before writing SKILL.md. |
| `/jstack-savetobrain` | The codified skill or its output is durable knowledge worth ingesting into the second brain. |

Otherwise standalone — the committed skill is the deliverable.
