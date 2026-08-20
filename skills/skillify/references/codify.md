# Codify a proven workflow

Use this route to make one successful, repeatable workflow into a new skill.

## 1. Confirm the source

Find the most recent successful workflow that has clear inputs, steps, and output. A user request to save the work as a skill counts as acceptance when the user has not rejected the result.

Stop and ask the user to run or identify the workflow when you cannot recover those facts from the session.

**Done when:** you can write one sentence for the input, output, and successful result.

## 2. Define the skill contract

Write these items in the staging notes or test:

- Input form and required parameters.
- Output form and assertions that must pass.
- Source boundary: fixed test data, live read-only data, or a state-changing service.
- Destination: project-local by default, or explicit jstack suite-global promotion.

Use redacted or synthetic test data. Keep only the smallest data set that proves the transform.

**Done when:** a future agent can run the test without guessing the expected result.

## 3. Build in staging

Create a unique staging directory before adding files. Put reusable code in `scripts/` when the same helper was needed in two or more runs, or when a fragile step needs fixed behavior.

Write a lean `SKILL.md`. Put route-specific detail in direct references. Keep only instructions an agent needs to run the skill.

For a jstack suite-global skill, classify it now and reserve the suite scaffolder for promotion after user approval. Use project instructions for a project-local skill.

**Done when:** the staged directory contains the skill instructions, required resources, and one test.

## 4. Verify the staged skill

Run the script or workflow against the test data. Assert required output values or structure. Run the destination linter and package checks that apply to the skill family.

For a jstack suite skill, run `bash skills/suite/scripts/skill-lint.sh [staged-skill-dir]` from the jstack repository root.

Fix a clear implementation error and run the checks again. Stop when the failure is environmental or the contract cannot be met. Remove the staging directory in that case.

**Done when:** all required checks pass and the staged output meets the contract.

## 5. Review and promote

Show the staged `SKILL.md`, main script, and test result when the user asks. Ask for approval before writing to the final destination.

After approval, use the destination's normal promotion tool. For a jstack suite-global skill, use the suite scaffolder to create the canonical container, then promote the checked staged files. Record every new canonical path and harness link the scaffolder creates. If a canonical check fails, remove only the recorded new paths after confirming they still match this promotion.

Keep a backup until the canonical check passes when promotion replaces an existing file. Run a live check only when it is read-only, reversible, or uses disposable state. Restore the backup if the canonical check fails.

**Done when:** the canonical skill passes the same required checks, or the prior skill is restored.
