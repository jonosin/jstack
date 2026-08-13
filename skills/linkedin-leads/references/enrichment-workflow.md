# Enrichment workflow

Use this when search results contain public identifiers or related-profile candidates that need full profile details before qualification.

## 1. Candidate shape

The enrichment script accepts a JSON list of either strings:

```json
["satyanadella", "another-public-id"]
```

or objects:

```json
[
  {"publicIdentifier": "satyanadella"},
  {"public_identifier": "another-public-id"}
]
```

## 2. Dry-run enrichment

```bash
python3 scripts/campaign_workflow.py enrich-public-ids \
  --candidates related_candidates.json \
  --out enriched_profiles.json \
  --chunk-size 10
```

## 3. Execute enrichment

```bash
python3 scripts/campaign_workflow.py enrich-public-ids \
  --candidates related_candidates.json \
  --out enriched_profiles.json \
  --chunk-size 10 \
  --max-charge 2.00 \
  --execute
```

This uses `harvestapi~linkedin-profile-scraper` with `publicIdentifiers`. It does not use the user's LinkedIn cookies.

## 4. Normalize or merge

If the returned shape differs from `linkedin-profile-search`, normalize it into the fields required by your campaign:

- `id`
- `publicIdentifier`
- `linkedinUrl`
- `firstName`
- `lastName`
- `headline`
- `location.parsed.country`
- `currentPosition[0].companyName`
- `experience`
- `about`

Then run the dedupe and qualification steps in `references/search-qualification-workflow.md`.

## 5. Next step

Once enriched profiles are merged and deduped, continue with qualification batches from `references/search-qualification-workflow.md`, then hand the final `prospects.csv` to `linkedin-send` for validation and sending.
