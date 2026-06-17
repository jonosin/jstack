# Lead Enrichment Workflow

Use the script:

```bash
python3 ~/jstack/skills/jstack-sf-leads/scripts/sf_leads.py <command>
```

## Routine Commands

Summarize the canonical table:

```bash
python3 ~/jstack/skills/jstack-sf-leads/scripts/sf_leads.py summary
```

Validate no stale CSVs or duplicate IDs exist:

```bash
python3 ~/jstack/skills/jstack-sf-leads/scripts/sf_leads.py validate
```

Append new seed rows from a CSV:

```bash
python3 ~/jstack/skills/jstack-sf-leads/scripts/sf_leads.py append \
  --input /path/to/new-leads.csv \
  --source-seed "manual_search"
```

The append CSV may contain any subset of canonical headers, but must include `property_name`.
Prefer also including `market`, `country`, `location`, `official_site`, `segment`, `icp_status`,
`verification_status`, `outreach_angle`, and `evidence_urls`.

Build the S7 ranked working file:

```bash
python3 ~/jstack/skills/jstack-sf-leads/scripts/sf_leads.py rank --top 25
```

Output:
`~/ventures/stayframe/leads/scoring/prospects-s7-ranked.csv`

## Apify Enrichment

Actor:
`apify/social-media-leads-analyzer`

Use this actor because it starts from an official website and extracts linked social/contact data.
Do not use Instagram-profile scraping until an Instagram URL is already known.

Build an input JSON without calling the API:

```bash
python3 ~/jstack/skills/jstack-sf-leads/scripts/sf_leads.py apify-input \
  --limit 25 \
  --output /tmp/stayframe-apify-input.json
```

Run the actor directly when `APIFY_TOKEN` is present:

```bash
APIFY_TOKEN=... python3 ~/jstack/skills/jstack-sf-leads/scripts/sf_leads.py apify-run \
  --limit 25 \
  --timeout 600
```

This writes raw JSON into:
`~/ventures/stayframe/leads/list/apify/`

Merge previously downloaded Apify outputs:

```bash
python3 ~/jstack/skills/jstack-sf-leads/scripts/sf_leads.py merge-apify \
  ~/ventures/stayframe/leads/list/apify/social-media-leads-run-*.json
```

## Owner Discovery

The current table mostly has `decision_maker=unknown`.
For S7, enrich owners/operators only for T1/T2 accounts. Good sources:
- official site About/Contact pages
- LinkedIn company and founder search
- Facebook page admins are not visible, but posts can reveal owner/operator names
- local press, hospitality awards, Google Business profile, booking engine footer

Do not block outreach waiting for owner discovery if a direct email or IG account is strong.
Use the first touch to ask who owns marketing if needed.
