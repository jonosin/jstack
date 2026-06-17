---
name: jstack-sf-leads
description: "Maintain and enrich the StayFrame/Facet prospect table. Use when adding hospitality leads, rerunning Apify social/contact enrichment, summarizing S6/S7 lead status, cleaning stale prospect CSVs, or preparing the canonical prospects-s6-100-apify-social.csv for outreach."
---

# jstack-sf-leads - prospect table and enrichment

Maintains the canonical Facet/StayFrame prospect table and turns new hospitality leads into a clean,
deduped, enriched list ready for S7 scoring and S8 outreach.

All paths assume `~/ventures/stayframe/`.

## Source of Truth

Canonical CSV:
`leads/list/prospects-s6-100-apify-social.csv`

Do not use or recreate:
- `leads/list/prospects-s6-100.csv`
- `leads/list/prospects-s6-100-social-pass1.csv`
- `leads/list/prospects-s6-100-social-pass2.csv`

For field meanings, load `references/schema.md`.

## Workflow

1. Run the table check:
   ```bash
   python3 ~/jstack/skills/jstack-sf-leads/scripts/sf_leads.py validate
   ```
2. If adding leads, append a seed CSV:
   ```bash
   python3 ~/jstack/skills/jstack-sf-leads/scripts/sf_leads.py append --input /path/to/new-leads.csv
   ```
3. Enrich official-site rows through Apify:
   ```bash
   python3 ~/jstack/skills/jstack-sf-leads/scripts/sf_leads.py apify-run --limit 25
   ```
   Requires `APIFY_TOKEN`. If not available, build an input with `apify-input` and run later.
4. Re-rank for S7:
   ```bash
   python3 ~/jstack/skills/jstack-sf-leads/scripts/sf_leads.py rank --top 25
   ```
5. Hand the ranked CSV to `/jstack-sf-outreach`.

For command details and Apify notes, load `references/enrichment.md`.

## Rules

- Keep the canonical table as the only outreach CSV. Intermediate raw Apify JSON is fine for audit.
- `verified + in_icp` beats every other row type.
- `out_of_icp` stays for benchmark context, not outreach, unless Jono overrides.
- Never send from the base table alone. Run `rank` first so channel and tier are explicit.
- When a durable strategy or ICP decision changes, offer `/jstack-savetobrain`; table mechanics stay here.

## Next skills

| Next | When |
|------|------|
| `/jstack-sf-outreach` | The ranked lead file exists and Jono wants messages, channel strategy, or a send plan. |
| `/jstack-sf-new <resort>` | A lead becomes a spec-piece target and needs a reel made from public photos. |
| `/jstack-msgdraft` | Drafting the actual message copy in Jono's voice. |
