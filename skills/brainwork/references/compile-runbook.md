# Compile runbook

Compile is the later operation after capture. It reads each new raw artifact one
time, persists a structured extraction, then applies a small canonical delta. It
does not create a routing card for every source. Raw evidence stays immutable.

## Required sequence

1. **Snapshot the work.** Run:

   ```bash
   python3 tools/sb.py compile snapshot --out <snapshot-path> --json
   python3 tools/sb.py compile status --json
   ```

   Use the returned snapshot as the fixed worklist. Include only non-deferred
   records captured before the snapshot. Use `compile next --limit <1..100>` for a
   bounded view; never print the full manifest.
   Done when: the snapshot artifact is written and the selected raw IDs have stable order and hashes.

2. **Take one extraction read.** For each selected record, load the raw artifact
   once. Use a sequential Luna/max worker for semantic extraction, with a
   60,000-token input cap and one oversized artifact per chunk. The extraction
   must contain Graphify nodes, edges, hyperedges, source locations, a bounded
   `source_digest`, key claims, raw provenance, and canonical-impact proposals.
   Done when: one extraction artifact exists for each assigned raw ID and no worker needs to reopen a successful source.

3. **Validate and persist extraction.** Run the public wrapper for each artifact:

   ```bash
   python3 tools/sb.py compile validate-extraction <artifact> --json
   python3 tools/sb.py compile record-extraction <artifact> --json
   ```

   Reject an invalid artifact. It must not contain `node_summary`, hidden
   reasoning, an unbounded digest, or an inferred file-node join.
   Done when: every accepted extraction reaches `extracted` and its body and contract hashes match the manifest.

4. **Plan canonical impact.** Group accepted proposals by canonical page. Use:

   ```bash
   python3 tools/sb.py compile integration-plan --canonical-id <id> --out <proposal-path> --json
   ```

   The main compile session decides `update`, `create`, `no-change`, or
   `conflict`. New canonical pages are not created by workers. Keep raw
   provenance on every proposed claim.
   Done when: every extracted record has one canonical action and each write unit has a named proposal or an explicit conflict.

5. **Apply safe deltas.** Apply only non-conflicting proposals:

   ```bash
   python3 tools/sb.py compile apply-integration <proposal> --json
   ```

   If the current canonical hash differs from the proposal's before-hash, stop
   that write unit as a conflict. Do not overwrite another agent's change.
   Done when: each applied proposal has an after-hash and the affected manifest records reach `integrated`.

6. **Refresh generated state.** After canonical writes, run:

   ```bash
   python3 tools/sb.py views build --json
   python3 tools/sb.py overlay update --json
   python3 tools/sb.py overlay freshness --json
   ```

   Use `overlay build --profile complete --json` when the update command reports
   that a complete rebuild is required. The overlay is discovery data, not truth.
   Done when: views and the overlay are fresh, content-addressed, and tied to the current source and authority hashes.

7. **Verify each record and resume safely.** Run:

   ```bash
   python3 tools/sb.py compile resume [<raw-id>] --json
   python3 tools/sb.py compile status --json
   python3 tools/sb.py verify --json
   ```

   A valid extraction receipt resumes an interrupted `extracting` record. A
   proposal receipt resumes an interrupted `integrating` record. Failed or
   blocked records remain visible with their stable error code.
   Done when: selected records are `verified`, or every unfinished record has a bounded failure and an exact resume command.

## Compile stop conditions

- A raw body or hash changed during the run: stop the record and report it.
- A source has no valid v2 metadata or stable ID: stop the record; do not patch
  evidence in prose.
- Canonical proposals conflict: leave them resumable and report the canonical ID.
- Overlay freshness is stale or missing: stop with `OVERLAY_NOT_READY` and run
  exactly `sb overlay update --json`. Do not start another retrieval lane.
- `verify` is non-zero: report the failed gate and stop claiming completion.

## Compile report inputs

Use `final-report.md`. Report the snapshot, raw IDs processed, canonical actions,
overlay/view artifacts, verification result, and remaining pending or blocked IDs.
