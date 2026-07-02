---
title: prospects.csv schema
---

# prospects.csv schema

This is the single source of truth for a send campaign. `send_batch.js` reads it (via `send_queue.json`); `track_reply.py` writes back status columns.

## Columns

| Column | Required | Notes |
|--------|----------|-------|
| Row | yes | Unique integer. Primary key across all tools. |
| Tier | no | A / B / C. Qualification tier. Use `LINKEDIN_SEND_TIERS` to restrict queue build. |
| Variant | yes | A / B (or more). Experiment arm. ~50/50 split across leads. |
| Channel | no | "InMail (credit)" or "InMail (free/open)". Informational. |
| Name | yes | Full name of the lead. |
| FirstName | yes | First name only (used in connection-note fallback). |
| Business | yes | Company name (cleaned of LLC/Inc/etc). |
| Country | no | Lead's country. |
| OpenProfile | no | Profile URL (linkedin.com/in/... or similar). Informational. |
| OpenInSalesNav | yes | THE send target: `https://www.linkedin.com/sales/people/<leadId>`. `send_batch.js` navigates here to open the InMail composer. The `<leadId>` is the stable member id/URN from Sales Navigator. |
| Subject | yes | InMail subject line. Filled by `send_batch.js`. Personalized per variant. |
| Message | yes | InMail body (>= 50 chars). Filled by `send_batch.js`. Opener ~25-40 words + bridge + ask. |
| VideoQuestion | no | Follow-up question for after a reply (used to build a Loom). Optional. |
| ConnectionNote | no | Fallback connection-request note if InMail credits run out. |
| Sent | owned by send_batch | Timestamp string set by `send_batch.js` after a successful send. Format: `2026-06-29 12:34:56 sent (credit)` or `skip:...`. Synced back from `send_queue.json` by `rebuild_send_queue.py`. |
| Reply | owned by track_reply | "yes" when any reply/positive/negative outcome logged. |
| DemoSent | owned by track_reply | "yes" when `demo_sent` outcome logged. |
| Call | owned by track_reply | "yes" when `call_booked` outcome logged. |
| Deposit | owned by track_reply | "yes" when `deposit` outcome logged. |
| Notes | owned by track_reply | Free-text notes. Appended by `track_reply.py log --text`. Contains `[positive]` or `[negative]` tags. |

## Key relationships

- `send_batch.js` keys off `OpenInSalesNav` to navigate to the lead, then fills `Subject` and `Message`.
- The `Variant` column (A/B) is the experiment arm. Use `track_reply.py stats` to compare reply and conversion rates between variants.
- Status columns `Sent`, `Reply`, `DemoSent`, `Call`, `Deposit`, `Notes` are written by the tools, not by hand.

## Example (2 rows)

```csv
Row,Tier,Variant,Channel,Name,FirstName,Business,Country,OpenProfile,OpenInSalesNav,Subject,Message,VideoQuestion,ConnectionNote,Sent,Reply,DemoSent,Call,Deposit,Notes
1,A,A,InMail (credit),Jane Smith,Jane,Acme,US,https://linkedin.com/in/janesmith,https://www.linkedin.com/sales/people/ACoAAABxyz123,how Acme runs,"I saw how Acme handles onboarding without a central knowledge base. I would bring all of that into one AI brain for Acme, something that answers the way you would. Want me to put a short video together for Acme?",What is your biggest ops bottleneck?,Hi Jane I would bring everything that makes Acme run into one AI memory,,,,, 
2,B,B,InMail (free/open),Bob Lee,Bob,Globex,UK,https://linkedin.com/in/boblee,https://www.linkedin.com/sales/people/ACoAAAByyz456,one AI memory for Globex any AI can use,"I noticed Globex onboards each new hire from scratch. I would bring all of that into one AI memory of Globex, one that plugs into whatever you already use and that you would own outright. Want me to put a short video together for Globex?",What tool does your team use most?,Hi Bob I would bring everything that makes Globex run into one AI memory,,,,, 
```
