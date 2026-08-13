---
name: openbrain-sync
description: Deterministically synchronize the approved second-brain wiki/raw sources and allowlisted satellite documentation into the hosted OpenBrain retrieval database. Use when the user says OpenBrain sync, refresh OpenBrain, ingest the brain into OpenBrain, update the ChatGPT brain connector, or verify OpenBrain retrieval.
---

# openbrain-sync

## Contract

Synchronize only the source manifest at `~/builds/openbrain/config/sources.json`:

- `~/second-brain/wiki` → `brain-wiki`
- `~/second-brain/raw` (excluding `raw/scratch`) → `brain-raw`
- `~/ventures/second-brain-agency/docs/{strategy,build,superpowers}` → `satellite-docs`

Never add `docs/scratch`, client data, arbitrary repos, or new source roots without an explicit user request. Source files remain canonical in their own repos; OpenBrain stores retrieval chunks only.

## Run

1. Regenerate and ingest deterministically:

   ```bash
   cd ~/builds/openbrain && ./scripts/resync.sh
   ```

   The script regenerates `out/thoughts.jsonl`, embeds only unseen fingerprints, loads them, and reports stale migrated chunks. It is safe to rerun.

2. If the load succeeds, inspect the prune report. Only then remove stale migrated chunks:

   ```bash
   cd ~/builds/openbrain && python3 -m src.prune --apply
   ```

   Pruning is intentionally separate. It can delete only `brain-wiki`, `brain-raw`, and `satellite-docs` rows; MCP captures are outside its scope.

3. Verify retrieval:

   ```bash
   cd ~/builds/openbrain && python3 scripts/acceptance.py
   ```

4. Report source counts, load/prune result, acceptance result, and any failed network/auth step. Do not claim a refresh completed unless both load and acceptance pass.

## Source changes

Edit `~/builds/openbrain/config/sources.json` only after explicit approval for the new source. Keep paths allowlisted and assign a stable `source` plus `namespace`. Add or update chunking tests before changing ingestion behavior.

## ChatGPT connector

Expose the deployed MCP only after successful acceptance. Prefer ChatGPT's read-only `search` and `fetch` tools. Do not enable `capture_thought` unless the user explicitly wants ChatGPT to bypass the second-brain raw-first curation workflow.
