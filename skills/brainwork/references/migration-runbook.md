# Migration runbook

Migration changes paths or metadata in controlled, reversible batches. It never
changes a raw body. The migration manifest is separate from the compile manifest.

## Required sequence

1. **Freeze the preflight.** Run:

   ```bash
   python3 tools/sb.py preflight freeze --out <preflight-dir> --json
   python3 tools/sb.py migrate freeze --out <migration-manifest> --json
   ```

   Record both repository states, protected dirty paths, artifact hashes, raw
   body hashes, and the intended scope before any mutation.
   Done when: the preflight and migration manifest identify every candidate and every protected path.

2. **Plan a disjoint batch.** Run:

   ```bash
   python3 tools/sb.py migrate plan --manifest <migration-manifest> --json
   python3 tools/sb.py migrate status --limit <1..100> --json
   ```

   Use batches of at most 25 raw items, at most 25 raw metadata repairs, or at
   most 20 wiki pages. Keep one canonical conflict group together. Do not plan a
   protected dirty path for mutation.
   Done when: the batch has a stable ID, named paths, before-hashes, and one action per item.

3. **Dry-run the batch.** Run:

   ```bash
   python3 tools/sb.py migrate dry-run <batch-id> --json
   ```

   Inspect the bounded diff. Confirm that raw body hashes remain unchanged,
   stable IDs do not change, and active references are rewritten only where the
   manifest permits it.
   Done when: the dry-run proves the batch is recoverable and has no protected-path overlap.

4. **Checkpoint exact bytes.** Run:

   ```bash
   python3 tools/sb.py migrate checkpoint <batch-id> --json
   ```

   The checkpoint must include bytes and non-existence markers for every named
   path. Keep the checkpoint until closeout.
   Done when: the batch state is `checkpointed` and every before-state has a receipt.

5. **Apply and verify.** Run:

   ```bash
   python3 tools/sb.py migrate apply <batch-id> --json
   python3 tools/sb.py migrate verify-batch <batch-id> --json
   ```

   Then run the migration gates: schema, evidence, compile state, supersession,
   and generated-view or overlay freshness. Use the wrapper output as the source
   of truth for the batch state.
   Done when: the batch is `verified`, all body hashes match, and all references resolve.

6. **Rollback on a failed gate.** If apply or verification fails, run:

   ```bash
   python3 tools/sb.py migrate rollback <batch-id> --json
   ```

   Rollback restores only checkpointed paths and removes only files created by the
   batch. Do not use Git reset, checkout, clean, or restore. A rollback mismatch
   blocks the batch and preserves its checkpoint.
   Done when: the before-hash comparison passes, or the batch is explicitly `blocked` with its error code.

7. **Close the migration unit.** Run:

   ```bash
   python3 tools/sb.py schema check --scope all --json
   python3 tools/sb.py views build --json
   python3 tools/sb.py overlay freshness --json
   python3 tools/sb.py verify --json
   ```

   Continue with the next disjoint batch only after the current batch is
   verified. Keep deferred older evidence explicit; do not silently admit it.
   Done when: the batch is durable, the verification result is recorded, and the next batch can resume from the manifest.

## Migration stop conditions

- Any protected dirty path is required: write a blocked proposal and continue only
  with disjoint work.
- Any raw body hash changes: stop and roll back the batch.
- Any path collision, duplicate stable ID, or stale before-hash appears: block the
  batch and require a new plan.
- Any gate fails after rollback: stop further writes and report the checkpoint.
