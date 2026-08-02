# Contact enrichment contract

Use public sources only. Check the official site first, then one bounded search for the exact property plus `email contact` only if needed. Never infer an email pattern.

Each prepared property receives exactly one result object matching `contact-result-schema.json`.

| Status | Email | Source URL | Mail-domain status | Draft gate |
|---|---|---|---|---|
| `contact_ready` | Required | Required | `confirmed` or `present` | Eligible |
| `contact_held` | Required | Required | Any observed value | Blocked |
| `published_unverified` | Required | Required | Inconclusive | Blocked |
| `contact_missing` | Must be null | Must be null | Not applicable | Blocked |
| `blocked` | Must be null | Must be null | Not applicable | Blocked |

Third-party email domains require a documented relationship with the property. Otherwise hold or exclude the email. Visible publication plus MX/mail-domain confirmation does not prove the individual mailbox accepts email.
