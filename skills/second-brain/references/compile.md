# Compile evidence into current knowledge

Compile only admitted registered raw IDs, under explicit compile/ingest intent.
Read the selected raw evidence, relevant current canonical pages and supersession
links. Preserve attribution and source locations. Distinguish an external author's
claim from a user-accepted decision. Link related ideas only where the evidence
supports the connection; inferred connections must remain labelled as synthesis.
When actual graph connectivity is requested, read graph-connections before
authoring the extraction. Wikilinks and `raw:` metadata alone do not create edges.

Prefer a small update to an existing page. Create a canonical page only when it
adds durable knowledge; allow an explicit no-change decision. Keep categories
under the three role directories and use wikilinks for cross-cutting topics.

## Dot runtime

Use the public brainwork compile runbook when its runtime worker requirements
are available. Dot performs semantic extraction/integration on its own computer;
do not send daily compile work to Codex or a laptop. For the transferable JSON
route, use the repository's existing `remote_compile.py` processor through
`scripts/dot_runtime.py` as documented in dot-runtime. This reuses the published
remote compile contract on dot's computer without Actions.

Before constructing a request, read these live target-repository contracts:
`tools/remote_compile.py`, `schemas/extraction-v1.json`,
`schemas/canonical-v2.json`, and `tools/remote_compile_verify.py`.

The request has exactly `schema`, `raw_ids`, `extractions`, `operations`:

- Set schema to `sb.remote-compile-request/v1` and provide a non-empty unique
  list of existing stable `raw-...` IDs in state `captured`.
- Supply exactly one extraction per selected raw ID, with exactly `raw_id`,
  `source_digest`, `key_claims`, `nodes`, `edges`, `hyperedges`, `canonical_impact`.
  `key_claims` is a list of claim strings in this transport, not local location
  objects. Keep the digest within the extraction validator's bounds. Use actual
  source evidence for semantic objects; the processor adds file-node identity
  and constructs validated extraction artifacts with provenance.
- Supply operations with exactly `action`, `raw_ids`, `path`,
  `before_blob_sha`, `content`. Cover every selected raw ID. Choose `update`,
  `create` or `no-change`. A raw ID cannot mix no-change with canonical writes.
- For update, include the current **Git blob SHA**, not SHA256, preserve its
  canonical ID and supply complete validated content. For create, set before
  SHA to null and normally use `id: AUTO` so the processor assigns a canonical ID.
  For a new page named by explicit graph edges, the processor also accepts a
  preallocated schema-valid canonical UUID; see graph-connections for endpoint
  identity and the required explain/path checks.
- Use flat Markdown paths under `wiki/personal`, `wiki/concepts` or
  `wiki/system`, matching the page's role. Include every supporting request raw
  ID in canonical `raw:` provenance. Follow all required canonical-v2 fields.
- For no-change, set path, before SHA and content to null. Keep a meaningful
  extraction and explanation of why no canonical delta is warranted.

Run one bounded related group at a time. Start from a clean isolated checkpoint
after capture; preserve the supplied request outside the checkout. The driver
persists a receipt, invokes the processor, builds views/inputs/overlay, checks
freshness, runs the narrow compile verifier, then runs `sb verify --json`.
It never publishes or invokes Actions. A replay after any compile attempt stops
for inspection rather than applying proposals twice.

## Failure and completion

A before-blob mismatch is a conflict: re-read the current page and produce a new
reviewed proposal. Do not force the old content over another change. Processor
failure may leave partial extraction/canonical/manifest work in the dot checkout;
preserve its receipt and inspect `compile show`, `compile conflicts` and public
`compile resume` before deciding recovery. Do not copy Actions' destructive reset
step into the dot runtime.

For Actions compatibility only, use the documented remote-compile request path.
Inspect the run plus canonical/extraction/manifest diff. Failure diagnostics are
committed separately; a removed request or manifest state alone is insufficient.

Done when: each selected raw ID has an observed canonical action and provenance,
generated state is fresh, and final `sb verify` passes or its real blockers are
persisted. Report `compiled`, `indexed` and `verified` separately. Do not compile
unrelated backlog merely to make the global gate green.
