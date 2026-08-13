# Brainwork final report

Emit one to four short lines. Use this order:

1. **Route:** `compile`, `migration`, `maintenance`, `dry run`, or `no-op`, with
   the reason or scope.
   Done when: the selected route is named.

2. **Work:** snapshot, raw IDs, migration batch, or check scope; state `none` if
   no artifact was processed.
   Done when: a fresh session can identify exactly what was selected.

3. **Changes:** canonical pages, generated views, overlay generations, migration
   paths, or `none`.
   Done when: every write is named by repository-relative path or stable ID.

4. **Checks:** `verify`, schema, freshness, and pending or blocked result. Include
   the exact resume command when work remains.
   Done when: the report says `clean` or gives the stable failure and next command.

Example:

```text
Route: compile (pending snapshot state/compile-snapshot.json)
Work: raw-<id>; action no-change
Changes: overlay generation <hash>; views refreshed
Checks: verify clean; pending 0
```
