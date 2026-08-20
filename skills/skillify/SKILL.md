---
name: skillify
description: "Turn a proven workflow into a reusable skill, or make a repeatable part of an existing skill run by code. Use when successful work should become a skill, or an existing skill has a repeatable step that should be scripted. Use /skilltune to measure output improvements."
---

# skillify

Turn working work into a skill that a future agent can run with less discovery.

Two routes exist:

| Route | Use it when | Read |
|---|---|---|
| **Codify** | A successful workflow should become a new skill. | [references/codify.md](references/codify.md) |
| **Harden** | One repeatable step in an existing skill should run by code. | [references/harden.md](references/harden.md) |

Route requests to `/skilltune` when the goal is a measured improvement to an existing skill's output.

## Common contract

Before writing files, state these facts:

1. **Source.** Name the proven workflow or the exact skill step.
2. **Contract.** State the input, required output, and checks that prove success.
3. **Data.** Use synthetic or redacted test data. Keep secrets, tokens, and private user data out of the skill.
4. **Destination.** A new project skill stays in its project by default. A jstack suite skill needs explicit user approval for global promotion.

Create all candidate files in a unique staging directory. Keep the canonical skill unchanged until the candidate passes its checks and the user approves promotion.

Use the tools and workers available in the current environment. Choose a script when it removes repeatable work. Keep runtime judgment in the skill when code cannot make the decision safely.

For a jstack suite skill, read `../suite/references/packaging.md`. Use its scaffolder for a new global skill. Do not create installation links by hand.

## Completion

The work is complete only when all of these are true:

- The staged skill passes its behavior test and destination checks.
- The user approves the staged change.
- Promotion preserves a backup until the canonical check passes.
- A safe live check passes, or the report states why a live check is unsafe or unavailable.
- For a jstack suite skill, canonical lint, `build-plugin.sh --print-only`, and `git diff --check` pass. Each installed harness link resolves directly to the canonical skill directory.

Call the skill ready only after all required canonical checks pass. If promotion restores a prior skill, report that the requested skill is not ready.

## Gotchas

- A stable test input proves the transform. It does not prove that a live website or API is unchanged.
- Test state-changing work with recorded, mocked, or disposable inputs.
- A step that needs current human judgment stays in the skill. Do not force it into code.
- Keep test cases, captured data, and staging notes out of the shipped skill unless the skill needs them at runtime.

## Next skills

| Next | When |
|---|---|
| `skill-creator` | The staged skill needs a clearer structure or new reusable files. |
| `/skilltune` | The goal is to measure and improve an existing skill's output. |

Otherwise standalone. The changed or new skill is the deliverable.
