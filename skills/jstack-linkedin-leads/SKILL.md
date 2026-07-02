---
name: jstack-linkedin-leads
description: Build qualified LinkedIn prospect lists end to end: choose/search filters, run no-user-cookie HarvestAPI lead search/profile enrichment/posts, dedupe against prior sends, split qualification batches, and prepare candidates for outreach CSV creation. Use when the user wants a lead list, prospect database, ICP-qualified LinkedIn leads, expansion run, profile/post pull, or reusable search/filter workflow. For sending use jstack-linkedin-send.
---

# jstack-linkedin-leads

Build a qualified LinkedIn prospect list from search filters or enriched profile candidates.

This skill is the campaign workflow layer. It may use HarvestAPI/Apify under the hood, but the job is broader than Apify: filters, pagination, dedupe, qualification batches, and handoff to outreach.

## When To Use

Use this skill when the user asks to:

- build a LinkedIn lead/prospect list
- expand an existing LinkedIn campaign
- qualify LinkedIn leads against an ICP
- dedupe new leads against old sends
- turn search/enrichment output into qualification batches
- reproduce a previous LinkedIn search/filter workflow without rebuilding scripts

Use the raw actor commands here for one-off HarvestAPI profile search, profile posts, or simple normalization.
Use `jstack-linkedin-send` after a final `prospects.csv` exists and needs validation/sending.

## Workflow

1. If filters are missing, ask for titles, seniority, company headcount, locations, industries, activity/stage filters, and exclusions.
2. For raw HarvestAPI actor schemas/pricing, read `references/actors.md`.
3. For search/filter/dedupe/qualification batches, read `references/search-qualification-workflow.md`.
4. For enrichment by public identifier or merging another scraped profile source, read `references/enrichment-workflow.md`.
5. Use `scripts/campaign_workflow.py` for campaign steps or `scripts/linkedin_apify.py` for one-off actor calls.
6. Keep qualification verdicts explicit: `keep/drop`, `dropReason`, `tier`, and campaign-specific hook/question fields.
7. Hand the final outreach CSV to `jstack-linkedin-send`.

## Core Commands

```bash
# Build search input from built-in owner-operator preset
python3 scripts/campaign_workflow.py build-search-input \
  --preset owner-operator \
  --out search_input.json

# Dry-run paginated search. Add --execute only after cost approval.
python3 scripts/campaign_workflow.py paginated-search \
  --input-file search_input.json \
  --target 200 \
  --out leads_raw.json

# Dedupe against prior raw pulls and send sheets
python3 scripts/campaign_workflow.py dedupe \
  --raw leads_raw.json \
  --existing-raw old/leads_raw.json \
  --existing-csv old/prospects.csv \
  --out-net-new leads_net_new.json \
  --out-dupes leads_dupes.json

# Split net-new leads for qualification review
python3 scripts/campaign_workflow.py split-qualification \
  --leads leads_net_new.json \
  --out-dir batches \
  --batch-size 20

# One-off profile posts pull
python3 scripts/linkedin_apify.py posts \
  --input '{"targetUrls":["https://www.linkedin.com/in/satyanadella/"],"maxPosts":5}'
```

## Safety

- Paid HarvestAPI calls are dry-run by default; require `--execute`.
- Use `--max-charge` for any paid run.
- Never print `APIFY_API_TOKEN`.
- `startPage` means a HarvestAPI Lead Search result page, not the user's logged-in Sales Navigator browser page.
- "No cookies" means no customer-supplied LinkedIn cookies; HarvestAPI does not disclose the full backend mechanism.
