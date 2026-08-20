# Harden one skill step

Use this route to replace one repeatable step in an existing skill with code while preserving the defined behavior.

## 1. Select the step

Resolve any skill link to its canonical directory. Check its worktree before copying it. Stop and ask the user when the target has uncommitted changes outside the requested hardening work.

Read the existing skill and name the exact step to replace. Keep a step in natural-language instructions when it needs current context, human preference, or a decision code cannot make safely.

**Done when:** the canonical source is known, its changes are in scope, and the selected step has a clear input and output boundary.

## 2. Capture the baseline

Create test cases that cover each behavior branch of the selected step. Use at least three cases only when three cases add coverage. Record the required output fields for each case.

Normalize values that are expected to change, such as timestamps, generated IDs, and ordering. State every allowed difference. Treat all other required fields as exact matches.

Use recorded, mocked, or disposable inputs for state-changing work. Redact the captured data before it enters staging.

**Done when:** each test case has an input, normalized expected output, and pass rule.

## 3. Build in staging

Copy the existing skill into a unique staging directory. Add the script under `scripts/`. Replace only the selected step with an instruction that calls the script and states its parameters and failure behavior.

Keep the existing behavior contract. A desired behavior improvement belongs in `/skilltune` after this work.

**Done when:** the staged skill calls the script and retains all unrelated files and instructions.

## 4. Verify behavior

Run every baseline case against the staged skill or script. A pass requires every required normalized field to match its baseline. Run the destination linter and package checks.

Do not use a subjective "better" judgment as proof of preserved behavior. Record an explicit allowed change, get user approval, and route output improvement work to `/skilltune`.

**Done when:** every case passes its stated rule.

## 5. Review and promote

Show the diff, script, and test result when the user asks. Ask for approval before replacing the canonical skill.

After approval, retain a backup, promote through the destination's normal tool, and run the canonical checks. Restore the backup when any canonical check fails. Run a live check only when it is safe under the common contract.

**Done when:** the canonical skill passes, or the backup is restored and the failure is reported.
