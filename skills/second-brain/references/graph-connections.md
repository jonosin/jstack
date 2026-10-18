# Explicit graph connections

## Why a connected page can report zero

The current complete adapter seeds file nodes from eligible canonical/raw
envelopes, then merges the admitted raw extraction fragments. It does not parse
canonical wikilinks or `raw:` frontmatter into edges. `canonical_impact` records
an integration proposal; it is not an edge generator. An extraction with only
its auto-added raw file node and empty `edges` therefore yields an isolated page
even if its prose has useful links. This is an authoring omission, not proof that
the concepts are unrelated or an overlay-refresh failure.

`sb explain` counts pairwise edges incident on the selected file node. It does
not count hyperedges. `sb path` traverses pairwise edges in either direction.
Graph topology is navigation; open source pages/raw sections for claim authority.

## Connect during the original compile

1. Open the selected raw sections and current related canonical pages. Record
   exact source locations and the relationship being asserted. Use `supports`
   for source-to-synthesis provenance and a precise semantic label for a
   supported conceptual connection. Mark inferred relationships as synthesis;
   schema validity alone cannot prove a relationship.
2. Resolve existing file endpoints with `sb node get ... --json`. Read its actual
   `node_id`, stable artifact ID and current status. Do not use titles as IDs or
   duplicate those file nodes inside the extraction's `nodes` array.
3. For a graph-connected new page, choose its canonical ID before authoring
   edges. The current remote compile processor explicitly accepts a valid
   `canon-` UUID in create content as well as `AUTO`. Generate a fresh UUID with
   Python `uuid.uuid4()` and keep it stable in the proposal. Raw IDs still come
   only from capture registration. Inspect the live `sb_overlay_inputs.py` rule:
   a file node ID is `file-` plus the first 24 hex characters of SHA256 of the
   exact artifact ID. Compute the new canonical endpoint from that fixed ID,
   then confirm it through `sb node get` after compilation. `AUTO` cannot be an
   edge endpoint because its final ID is assigned after extraction authoring.
4. Author explicit pairwise `edges` in the semantic extraction. Render actual
   endpoint IDs and provenance in this shape, not these placeholders:

   ```json
   {"source":"RAW_FILE_NODE","target":"NEW_CANONICAL_FILE_NODE","type":"supports","source_locations":[{"path":"raw/DATE-example.md","start_line":12,"end_line":18,"heading":"Source"}]}
   ```

   Add the reviewed canonical-to-related-canonical edge separately. The current
   processor preserves edge objects and the overlay validates endpoint existence;
   extra provenance fields are retained as authored metadata, not independently
   inferred facts. Keep the canonical page's `raw:` IDs and wikilinks too.
   A provenance edge alone does not establish the requested conceptual relation.
5. Supply a graph-check file when invoking the driver compile command:

   ```json
   {"explain":["wiki/concepts/new-topic.md"],"paths":[{"source":"wiki/concepts/new-topic.md","target":"wiki/concepts/related-topic.md"}]}
   ```

   Add `--graph-check PATH` to `dot_runtime.py ... compile ...`. The driver runs
   public explain/path checks after scoped compile verification and overlay
   freshness. It records `graph_connected: true` only when all expected endpoints
   have real connections/paths. If these fail, report compiled/indexed but graph
   acceptance blocked. Whole-repo `sb verify` remains a separate final gate.

Use namespace-stable semantic nodes only when the evidence needs them. Avoid
cross-fragment references to newly authored semantic nodes whose processing
order has not yet admitted them. Direct file-to-file edges use the complete set
of eligible seeded file nodes and avoid this ordering problem.

## Already verified extraction

Check the actual command interface before selecting this branch. The original
public compile interface cannot re-record from `verified`; remote compile
requires `captured`, and terminal `compile resume` does not re-extract. A fresh
overlay rebuild cannot invent missing edges. Keep raw evidence and terminal
state intact.

A tested target-repository patch adds the public `compile enrich-graph` command.
Use it only after the approved code/schema files are materialised in dot's
isolated checkout and `python3 tools/sb.py compile enrich-graph --help` confirms
availability. Read that repository's `docs/graph-enrichment.md` and
`schemas/graph-enrichment-v1.json` before authoring the bounded proposal.

The proposal pins manifest/raw/original-extraction/current-fragment/canonical
hashes, supplies additions with exact evidence locations and reviewed rationale,
and declares expected explain/path checks. Run the public command with
`--check --json` first; review its candidate before the apply form without
`--check`. Apply writes a new content-addressed graph fragment and immutable
journal, then switches only `graph_fragment`. It preserves the original
extraction, compile receipts, raw/canonical bytes and verified/passed state.

Require a single-writer checkout. On a hash conflict preserve the concurrent
edit and prepare a new reviewed proposal. On interruption inspect the lock and
journal before retrying the identical proposal. After apply run overlay update,
freshness, actual explain/path checks and final `sb verify --json`; enrichment
alone cannot claim indexed or whole-repository verified completion.

If that command is absent, report graph enrichment blocked by missing code
capability. Do not recapture the source, reset a verified record or overwrite
old receipts to imitate it. Installing a draft patch is distinct from merging
it or publishing a knowledge change; preserve those user boundaries.
