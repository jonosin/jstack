---
name: jstack-geo-leads
description: Use when building or refreshing an Australian independent hospitality lead list from Apify Google Maps results, or preparing and merging public-email contact enrichment after GEO qualification. Preserve source lineage, enforce a strict included-credit ceiling, and block outreach drafting without a contact-ready result.
---

# jstack-geo-leads

Run one bounded pipeline phase at a time. Preserve source artifacts. Do not send outreach.

## Provider routing

Use **GCP Places Text Search** for new discovery batches. Use **Apify only after
qualification** for bounded official-site/contact enrichment. The legacy Apify
Maps discovery route below remains for existing Australian runs; do not use it
for a new international batch.

For a GCP batch, create `leads/gcp-discovery/runs/<UTC timestamp>/`, preserve
the immutable query plan, one raw response per query, combined raw responses,
field mask, authenticated-project identifier, and source ledger. Run the
parameterized runner before any qualification:

```bash
python3 scripts/gcp_discovery.py prepare --markets <markets.json> --output <run-dir>-input.json
python3 scripts/gcp_discovery.py run --input <run-dir>-input.json --output-dir <run-dir>
python3 scripts/gcp_discovery.py normalize --input <run-dir>/raw-combined.json --output-dir <run-dir>/prefilter
```

It uses application-default credentials and OAuth; never store a token or API
key. The field mask includes Place ID, official website, Maps URL, address,
type, and business status. Deduplication is Place ID,
official-site domain, then normalized name/locality. A retained property is
only plausible, never business-qualified.

Project GCP-only records into explicit qualification outcomes with:

```bash
python3 scripts/gcp_qualify.py --retained <run-dir>/prefilter/retained-plausible.json \
  --excluded <run-dir>/prefilter/excluded.json --output-dir <run-dir>/qualification
```

Without official-site evidence, every retained record is `needs_review`; do
not promote it merely because GCP returned a website. The prefilter exclusions
remain explicit `rejected` records with their original rule.

## Phase 1: discovery

Build a small, auditable Apify Maps run. Stop after map-level prefiltering. Do not infer room counts, test GEO pain, enrich contacts, draft outreach, or send anything in this phase.

Require approved Australian micro-markets, remaining included credit, a per-run USD ceiling, an authenticated Apify account, and an output run directory under `leads/apify-discovery/runs/<UTC timestamp>/`. Never write the token into the repository, artifacts, ledger, or command history.

1. Start with a small pilot. Set `maxTotalChargeUsd` at or below the approved cap and remaining included credit. Set reviews, images, contacts, social enrichment, and every optional enrichment to zero or false.
2. Use `compass/crawler-google-places` only. Preserve actor ID, run ID, dataset ID, terminal status, input, raw dataset, account-limit snapshot, charged events, and actual cost.
3. Prepare the run before paying:

```bash
python3 scripts/geo_leads.py prepare \
  --markets references/markets-fixture.json \
  --output <run-dir>/input.json \
  --max-crawled-places-per-search 12 \
  --max-total-charge-usd <approved-cap> \
  --remaining-included-credit-usd <available-credit>
```

4. Submit only that generated input. Save unchanged raw dataset pages and a `source-ledger.json` before processing.
5. Prefilter only after the raw array and ledger exist:

```bash
python3 scripts/geo_leads.py prefilter \
  --input <run-dir>/dataset-items.json \
  --lineage <run-dir>/source-ledger.json \
  --output-dir <run-dir>/prefilter
```

Deduplicate in order: Google Place ID, CID, official-site domain, normalized name plus locality. Reject only closed, website-less, major-chain, clearly non-accommodation, or obvious single-unit map records. A retained record is not business-qualified.

## Phase 2: contact enrichment

For a new GCP batch, run a bounded Apify official-site crawler on the explicit
website-backed plausible/qualified cohort before GEO testing. Preserve actor,
run, dataset, exact input, raw output, source-page URL, terminal run record,
and actual cost. A returned email is `published_unverified` unless its
mail-domain status is confirmed; a third-party domain is `contact_held`.
Only `contact_ready` can enter `jstack-geo-qualify` for consumer ChatGPT
testing. It never searches, guesses, or sends email itself.

The prepared-shard workflow below is retained for the legacy agent-assisted
public-web contact pass; it is not the default enrichment lane for a new GCP
batch.

### Prepare stable inputs

```bash
python3 scripts/contact_enrichment.py prepare \
  --input <qualified-property-results.json> \
  --output-dir <contact-run-dir>/inputs \
  --shard-count 2
```

The source must be an object with a non-empty `prospects` array. Each prospect needs a unique `property` and non-empty `website`; `region`, `locality`, `query`, `conversation_url`, `candidate_status`, and `safe_claim` are retained when present. The script sorts the records, creates balanced `shard-XX.json` files, and writes `prepare-summary.json`. Shard count is input-controlled, not tied to a historic list size.

### Delegate the public-web judgment

Give one prepared shard to an agent or browser workflow. That judgment may use the official property site first, then one bounded public-web search for the exact property plus `email contact`. It must not use a guessed address, bulk LinkedIn scraping, access-control bypass, contact form, or send action.

Require one JSON object per prepared property, using `references/contact-result-schema.json`. The judgment must return exactly one of:

- `contact_ready`: published, relevant email and confirmed/present mail-domain status.
- `contact_held`: published email but recipient/source relevance needs human review.
- `published_unverified`: published email but mail-domain status is inconclusive.
- `contact_missing`: no relevant public email found after the bounded search.
- `blocked`: access or technical issue prevented the bounded search.

For a published email, require the visible source URL, observed timestamp, confidence, and search notes. Third-party email domains need a proven property relationship; otherwise return `contact_held` or `contact_missing`. Do not guess.

### Merge and gate drafting

Store agent JSON arrays as `<results-dir>/shard-XX-results.json`. Optionally put reviewed corrections in a JSON object keyed by property name. Then run:

```bash
python3 scripts/contact_enrichment.py merge \
  --input-dir <contact-run-dir>/inputs \
  --results-dir <contact-run-dir>/results \
  --schema references/contact-result-schema.json \
  --output-dir <contact-run-dir>/merged \
  --overrides <contact-run-dir>/reviewed-overrides.json
```

The merge fails on missing/duplicate/unexpected properties, website mismatch, invalid email syntax, invalid status, or invalid source/status combination. It writes JSON, CSV, and `summary.json`. Only `contact_ready` records are draft-eligible. Keep every other record out of drafting.

## Gotchas

- Mail-domain confirmation does not prove an individual inbox accepts mail.
- A directory, broker, or unrelated same-name property is not a valid contact source without a documented relationship.
- Do not declare a contact missing before checking earlier official-site evidence from qualification work.

## Next skills

| Next | When |
|---|---|
| `jstack-geo-qualify` | Discovery candidates need business-fit and GEO-pain qualification. |
| `jstack-geo-dashboard` | Qualified or contact-enriched records need projection into the control room. |
| `jstack-skilltune` | Measure or improve contact-judgment accuracy against a held-out review set. |
