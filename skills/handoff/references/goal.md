# Goal

Use goal after an execution spec exists. The spec is the source of truth; goal mode only produces a
fresh-task prompt. It does not create another artifact.

Find the spec. If it is missing, stop and direct the user to `/to-spec`.

## Goal-readiness

Read the spec's Contract before writing the prompt. Confirm it supplies a usable execution goal:

- **Outcome:** a concrete end state.
- **Acceptance:** binary or quantitative evidence that proves completion.
- **Scope:** the intended work and material exclusions.
- **Constraints:** applicable operating limits.
- **Stop / escalation:** when the executor must stop and ask.

Use the settled artifact and conversation to resolve a gap when that is safe. Otherwise ask one
concise question only when a missing outcome, validator, boundary, or stop condition would change
the goal. Record the answer in the governing spec's Contract before generating the prompt; never
put the canonical answer only in this handoff.

Do not call `get_goal` or `create_goal`. This mode produces a copy-paste `/goal` prompt; it does
not create platform goal state.

Write a paste-ready `/goal` prompt. Decide its wording for the task, keep it under 1500 characters,
name the spec, and give one verifiable stop condition from the spec's Acceptance section.
For example, its essential shape is:

```text
/goal Read <spec path> first. It is the source of truth. <focus>. Stop when <verifiable condition>.
```

Do not state a working directory or repeat scope, decisions, validation, or progress from the spec.
