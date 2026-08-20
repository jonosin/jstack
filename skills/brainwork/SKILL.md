---
name: brainwork
description: >
  Compile pending raw evidence into canonical second-brain knowledge, run a
  bounded migration, or maintain the brain. Use when the user asks for
  brainwork, compile, migration, schema or link checks, overlay freshness,
  generated views, verification, or a dry run.
---

# brainwork

This skill owns three explicit operations:

- **Compile** turns admitted pending raw evidence into a small canonical delta and
  refreshes the retrieval overlay.
- **Migration** plans and applies reversible corpus or metadata changes.
- **Maintenance** checks and repairs contracts, generated views, and overlay
  freshness without changing the meaning of knowledge.

Raw evidence and the canonical wiki remain authoritative. The retrieval overlay is
generated discovery data. A compile may propose a canonical page, but it does not
create one page for every raw artifact.

## Operating contract

1. **Load the live contract.** Resolve `SECOND_BRAIN_PATH` from
   `~/.jstack/config.env`, with `~/second-brain` as the default. Read that
   repository's `AGENTS.md` and `CONTEXT.md` before routing. Work from the vault
   root for every command.
   Done when: the active vault path and its authority, lifecycle, and role rules are known.

2. **Choose one route.** Read
   [references/decision-router.md](references/decision-router.md). Apply its
   word-first rules and select exactly one of compile, migration, maintenance,
   dry run, or no-op.
   Done when: one route and its scope are recorded, with no second operation mixed into the run.

3. **Load one runbook.** Read only the selected runbook from the table below.
   Read [references/wrapper-contract.md](references/wrapper-contract.md) when a
   command response or exit code needs interpretation.

   Done when: only the route-specific procedure and required wrapper contract are in working context.

   | Route | Runbook |
   | --- | --- |
   | Compile | [references/compile-runbook.md](references/compile-runbook.md) |
   | Migration | [references/migration-runbook.md](references/migration-runbook.md) |
   | Maintenance | [references/maintenance-runbook.md](references/maintenance-runbook.md) |
   | Dry run or no-op | [references/final-report.md](references/final-report.md) |

4. **Run the selected procedure.** Use the public `tools/sb.py` command surface
   in the runbook. Keep runtime semantic workers sequential and bounded by
   token-sized groups. Keep raw bodies immutable. Keep canonical changes focused
   and reviewable. Treat a conflict, failed gate, stale overlay, or protected
   dirty path as a reportable stop state.

   Done when: every command returned structured output, every selected state transition is recorded, and no unsafe write is pending.

5. **Verify the result.** Run the route's final `schema`, state, generated-view,
   overlay, and `verify` checks. A failed check remains visible in the report;
   resume through the public command for that state.

   Done when: the required checks pass, or the exact stable failure and resume command are recorded.

6. **Report and hand off.** Use [references/final-report.md](references/final-report.md)
   for the short status payload. Include the route, selected artifacts, changes,
   check result, and remaining work.

   Done when: the report is four lines or fewer and another fresh session can resume from it.

## Guardrails

- Call repository operations only as `python3 tools/sb.py ...` from the active
  second-brain root. The runbooks are the command interface; skill text does not
  embed Python, private Graphify calls, or an alternate wrapper.
- Use `compile` for semantic work, `migrate` for controlled corpus changes, and
  `maintenance` for contract repair. Capture is a separate operation.
- Classify raw evidence by its v2 metadata and stable ID. A filesystem location
  does not decide its canonical role.
- Preserve supersession and raw provenance. Current canonical knowledge wins for
  normal answers; raw evidence is opened for exact, disputed, stale, high-stakes,
  drafting, or implementation work.
- Keep output bounded. Do not print complete manifests, graphs, or corpus listings.
- Preserve unrelated dirty worktree paths. If an owned path is protected, save a
  blocked proposal and continue only with disjoint work.

## Next skills

| Next | When |
|---|---|
| `querybrain` | The compiled result needs retrieval or evidence checks. |
| `to-spec` | The result needs an execution contract. |
