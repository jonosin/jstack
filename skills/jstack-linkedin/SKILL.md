---
name: jstack-linkedin
description: Front door / router for LinkedIn prospecting and outreach automation; routes to the right sub-skill (lead-list builder, Sales Navigator lead extractor, or the auto-send pipeline). Use for any LinkedIn lead-gen, Sales Navigator, cold InMail automation, scrape/find prospects, or automate-LinkedIn-outreach request, especially when unsure which LinkedIn sub-skill applies.
---

# jstack-linkedin

Front door for LinkedIn prospecting and outreach. State what you want to do and load the matching sub-skill.

## Intent routing

| Want to... | Skill |
|------------|-------|
| Build/search/enrich/dedupe/qualify LinkedIn prospects, or run raw HarvestAPI profile/post pulls | `jstack-linkedin-leads` |
| Extract / enrich leads from an already-open Sales Navigator search tab (OpenCLI) | `jstack-linkedin-salesnav` |
| Build the per-lead CSV + auto-send Sales Nav InMails in halt-safe batches + track A/B replies / conversions | `jstack-linkedin-send` |

## Typical end-to-end pipeline

1. Build or source leads: `jstack-linkedin-leads` or `jstack-linkedin-salesnav`
2. Message and send: `jstack-linkedin-send` (builds CSV, validates, sends, tracks)

Load the chosen sub-skill by name to get full instructions.
