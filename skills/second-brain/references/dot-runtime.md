# Run on dot's computer

## Contents

- Prerequisites and credentials
- Commands and publication
- Replay and transfer
- Verification limits

## Prerequisites and credentials

Use a complete private brain checkout at a known commit, with its `tools/`,
`schemas/`, raw/wiki sources and required state/history. Do not copy another
machine's absolute paths into dot. Obtain the snapshot through an approved
private Git checkout/export or supported connector transfer. A GitHub connector
session does not automatically give shell git authentication. Keep credentials
in the host's approved secret/connection store; do not extract connector tokens
or save credentials in requests, logs, skill files or shell command history.

Minimum processing dependencies verified against the repository implementation:

- Python 3.12 is the Actions-tested version. Driver uses Python standard library.
- Git is required for checkpoints, blob comparisons and scoped verification.
- PyYAML is required by the repository processors and `sb` imports. Install in a
  dot-owned venv, e.g. `python3 -m pip install PyYAML==6.0.3` in that venv.
- Bun and Node are unnecessary for this driver. `graphifyy` is pinned by the
  existing Actions requirements, but the complete `sb_overlay.py` adapter
  directly used here has no Graphify package import. Engine administration
  still uses its separate requirements/runbook.
- The public bounded `sb query` command needs no hosted model credentials.
  For the richer semantic remote-query ranker on dot, additionally install
  `requirements-retrieval.txt` and explicitly prepare the pinned checked model
  with `python3 tools/remote_query_model.py --prepare`. This downloads model
  assets, not brain/query text. Keep model/vector caches private. Report missing
  wheels, assets or network access rather than silently switching rankers.
- X input already fetched by dot needs no X credential. The driver accepts its
  supplied Markdown and never refetches. Browser authentication remains in the
  browser. The public mirror is optional acquisition, not a secret-store route.

No credential is required for processing an available checkout. Publication
requires an authorised GitHub connector write or separately configured Git
credential. Verify that capability independently; local success is not remote
durability.

## Commands and publication

Place this skill package and the private checkout in dot's workspace. Define
`BRAIN`, `DRIVER`, `RECEIPTS` and `INPUTS` as task-specific paths there; keep
receipts/inputs outside the checkout. Use the same private receipt directory
for every operation on that checkout. Start with:

```bash
python3 "$DRIVER" --repo "$BRAIN" --state "$RECEIPTS" doctor
python3 "$DRIVER" --repo "$BRAIN" --state "$RECEIPTS" capture --id source-001 --request "$INPUTS/capture.json"
```

Construct `capture.json` from the obtained source Markdown using the exact capture
fields in the capture reference. The JSON body is the source Markdown including
provenance, not a summary or fabricated raw-v2 header. Dot should use JSON
serialization, not shell interpolation, for the article text. Keep inputs private.

The driver copies one request to `state/dot-runtime-requests/`, calls the existing
repository capture processor, then runs final `sb verify`. This path does not
match the current Actions request triggers. It preserves an external receipt
even when verification fails. Inspect `captured` independently of exit status.

After reviewing only the owned raw/manifest/preparation changes, checkpoint those
exact paths in the isolated dot checkout. Use an already configured non-sensitive
commit identity. Never stage unrelated work. Compile starts from a clean
checkpoint so the scoped verifier can detect unexpected changes:

```bash
python3 "$DRIVER" --repo "$BRAIN" --state "$RECEIPTS" compile --id compile-001 --request "$INPUTS/compile.json"
```

Dot authors the semantic request from opened sources per the compile reference.
The driver invokes existing repository processors and public `sb` checks. No LLM
API key is needed by the driver; the active dot supplies semantic judgement.
For direct query/checks, run from the brain root:

```bash
python3 tools/sb.py query "requested topic" --depth evidence --budget 1200 --json
python3 tools/sb.py node get "wiki/concepts/selected-page.md" --budget 1200 --json
python3 tools/sb.py overlay freshness --json
python3 tools/sb.py compile status --json
python3 tools/sb.py verify --json
```

Run the documented overlay update first if the query reports `OVERLAY_NOT_READY`.
Open returned canonical/raw locations before answering. To use the semantic
ranker, process the supported query JSON with `python3 tools/remote_query.py
state/dot-runtime-requests/query-001.json` on dot; this is execution on dot,
not submission to Actions.

Review diffs and publish exact owned files through available GitHub commit APIs
or authenticated Git. Use expected branch/blob SHAs; do not force push. Report
the resulting branch/commit and verify the published files against local hashes.
Keep request/receipt files out of Actions watched paths. No driver command
publishes, merges, changes access or disables workflows.

## Replay and transfer

Use stable operation IDs and identical payloads for capture retry. The driver
checks request identity, existing source/body/role, manifest registration and
body hash. It returns an existing capture without calling finalize again.
A changed body or operation-ID payload blocks for a deliberate version/correction.
A partial raw file without registration blocks for inspection/public recovery.
After any compile attempt the same ID blocks, because proposals may already be
applied; inspect receipt + compile state and public resume commands. An OS crash
may leave `operation.lock`; inspect the active process and receipt before
removing a stale lock. Use one receipt directory and one writer per checkout.

Transfer this complete skill folder via a GitHub tree/ref or the validated
`.skill` ZIP through a supported Library import. The parent must materialise
files into **its own** filesystem; a child executor path is not a dot path.
Fetch private brain files only through authorised private transfer. A partial
snapshot can run a synthetic smoke test but cannot prove whole-brain verification.

## Verification limits

The published whole-repo verifier includes historical migration evidence,
machine-path-dependent audits, pending backlog and a frozen retrieval evaluation.
An ordinary new capture can be valid while global `sb verify` remains nonzero.
Preserve its JSON and distinguish the exact failing gates. Do not label narrow
compile verification or successful queryability as a whole-repo pass.

Before switching daily operations/schedules away from the old pipeline, test on
dot: dependency doctor, supplied-text capture once, duplicate retry, semantic
compile, overlay freshness, source-backed query and persisted final verification.
The parent's coordinated real-source capture owns that test. Building this skill
does not authorise a second independent ingestion or disabling Actions.
