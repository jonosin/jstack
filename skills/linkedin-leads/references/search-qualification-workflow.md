# Search + qualification workflow

Use this when the user wants a campaign-grade LinkedIn prospect list, not just a one-off actor call.

## 1. Gather filters

If the user has not provided filters, ask for:

- target titles or roles
- seniority levels
- company headcount
- countries or regions
- industries or industry ids
- activity filters such as recently posted
- stage filters such as years at current company
- exclusions, especially tech/SaaS/AI, recruiters, brokers, real estate, agencies, or freelancers

For a generic established-owner-operator campaign, the built-in preset is `owner-operator`. Treat it as a starting point, not venture knowledge. If the campaign has a different ICP, pass a user-supplied filter JSON instead.

## 2. Build the HarvestAPI search input

```bash
python3 scripts/campaign_workflow.py build-search-input \
  --preset owner-operator \
  --industry-ids industry_ids_parents.json \
  --out search_input.json
```

Or pass a user-supplied filter JSON:

```bash
python3 scripts/campaign_workflow.py build-search-input \
  --filters filters.json \
  --out search_input.json
```

## 3. Run paginated search

Dry-run first:

```bash
python3 scripts/campaign_workflow.py paginated-search \
  --input-file search_input.json \
  --target 200 \
  --start-page 1 \
  --max-pages 20 \
  --out leads_raw.json
```

Execute only after the user accepts cost/risk:

```bash
python3 scripts/campaign_workflow.py paginated-search \
  --input-file search_input.json \
  --target 200 \
  --start-page 1 \
  --max-pages 20 \
  --max-charge 3.00 \
  --execute \
  --out leads_raw.json
```

Notes:

- The actor returns about 25 profiles per page.
- `startPage` is the HarvestAPI Lead Search result page, not a logged-in browser page from the user's Sales Navigator tab.
- Use a deeper `--start-page` for expansion runs that should avoid the first pages of a prior pull.
- The actor is no-user-cookie HarvestAPI infrastructure; it is not driving the user's Sales Navigator tab.
- Public HarvestAPI docs distinguish this Lead Search path from basic `linkedin.com/search/results/people/`.
  "No cookies" means no customer-supplied LinkedIn cookies; HarvestAPI does not fully disclose the backend
  mechanism and may use its own resources/session pools.
- HarvestAPI's underlying Lead Search API supports Sales Navigator URL compatibility, but this Apify actor
  should be treated as parameter/filter-driven unless a live test proves exact Sales Nav URL parity.

## 4. Dedupe against prior sends

```bash
python3 scripts/campaign_workflow.py dedupe \
  --raw leads_raw.json \
  --existing-raw ../leads_raw.json \
  --existing-csv ../prospects.csv \
  --out-net-new leads_net_new.json \
  --out-dupes leads_dupes.json
```

Deduping compares LinkedIn profile URLs and `/sales/people/<id>` IDs.

## 5. Split for qualification

```bash
python3 scripts/campaign_workflow.py split-qualification \
  --leads leads_net_new.json \
  --out-dir batches \
  --batch-size 20
```

Qualification is still a judgment step unless the user provides exact rules. Ask for the campaign's
keep/drop rubric before review. For an established-owner-operator campaign, possible keep criteria are:

- real owner/operator authority
- established operating business
- team/process complexity
- budget/ability to buy, using whatever evidence the campaign allows
- low DIY likelihood, if relevant to the offer
- no excluded pattern named by the user, such as agency, consultant, freelancer, commission-income, recruiter, broker, or high-DIY tech/SaaS

Each qualification output should include:

- `index`
- `firstName`
- `business`
- `linkedinUrl`
- `country`
- `decision`: `keep` or `drop`
- `dropReason`
- `tier`: `A`, `B`, `C`, or null
- campaign-specific question or hook field

## 6. Next step

After qualification, read `references/enrichment-workflow.md` if you need to enrich public identifiers or merge another scraped source before building the final outreach CSV.
