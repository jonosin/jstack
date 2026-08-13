# Brainwork decision router

Run this router after loading the repository contract. Select one route. Do not
run a second route in the same invocation.

## Route rules

1. If the request contains `dry run`, select **dry run**. This rule has first
   priority and permits no writes.
   Done when: the request is marked dry run and no mutating command is selected.

2. If the request names migration, `migrate`, `flatten`, metadata repair, a
   migration plan, a migration batch, or a preflight freeze, select **migration**.
   Done when: the migration scope and batch or manifest, if supplied, are recorded.

3. If the request names maintenance, `lint`, `check`, `health`, `graph`, `fix
   links`, schema checks, overlay freshness, generated views, or verification,
   select **maintenance**. This rule wins over pending compile work.
   Done when: the maintenance intent and requested check or repair are recorded.

4. If the request names compile, brainwork, pending raw, ingest, a raw artifact
   ID or path, or `all pending`, select **compile**. A bare `/brainwork`
   also selects compile and processes the pending snapshot.
   Done when: the compile scope is either the named artifact(s) or the pending snapshot.

5. If the request explicitly says no-op or asks only for status, select **no-op**.
   Done when: no write route is selected and the requested status is clear.

6. If no rule matches, select **compile** and take a pending snapshot. The
   snapshot can produce a no-op when no non-deferred records exist.
   Done when: the snapshot proves whether compile work exists.

## Route handoff

- **Compile:** load `compile-runbook.md`.
- **Migration:** load `migration-runbook.md`.
- **Maintenance:** load `maintenance-runbook.md`.
- **Dry run or no-op:** load `final-report.md` and report the selected action.

The public wrapper commands and their bounded response contract are in
`wrapper-contract.md`. Load that file only when a command is needed or its output
needs interpretation.
