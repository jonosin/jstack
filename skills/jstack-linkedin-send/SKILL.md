---
name: jstack-linkedin-send
description: Build the per-lead prospects.csv (subject + message + Sales Navigator /sales/people link + A/B variant) and auto-send LinkedIn Sales Navigator InMails in halt-safe batches over CDP, then track A/B reply and conversion rates (demo/call/deposit). Use when the user wants to automate Sales Navigator sends or InMails, send a cold InMail batch, burn LinkedIn InMail credits, or track which A/B variant replied or converted.
---

# jstack-linkedin-send

Build and send a personalized InMail batch through LinkedIn Sales Navigator, then track A/B outcomes.

## Workflow

### 1. Source leads

Get leads from `jstack-linkedin-leads` (HarvestAPI, no login needed) or `jstack-linkedin-salesnav` (open Sales Nav tab). Or use the router: `jstack-linkedin`.

### 2. Build prospects.csv

Follow the schema in `references/csv-schema.md`. Every row needs:
- `OpenInSalesNav`: `https://www.linkedin.com/sales/people/<leadId>` (the send target)
- `Subject` and `Message`: per-lead, personalized

Composing the message:
- Use `jstack-gtmarketing` (references/cold-outreach.md) for the framework and `jstack-myvoice` for voice (no em dashes).
- Opener ~25-40 words (do not overrun). Pin one real, specific detail about the lead/company.
- Assign A/B ~50/50 across the lead order.

### 3. Validate

```bash
python3 scripts/validate_csv.py --dir <DIR>
```

Must print `PASS` before proceeding. Checks required columns, unique Rows, Sales Nav links, message length, non-empty Variant.

### 4. Build the send queue

```bash
python3 scripts/rebuild_send_queue.py <DIR>
```

Converts `prospects.csv` to `send_queue.json`. Preserves sent-state from any previous run (never re-sends). Set `LINKEDIN_SEND_TIERS=A` to restrict to Tier A only.

### 5. Start the browser with CDP

Follow `references/cdp-setup.md`. Launch Brave or Chrome with `--remote-debugging-port=9222`, log into LinkedIn + Sales Navigator. Verify:

```bash
curl -s localhost:9222/json/version
```

### 6. Send (canary first)

```bash
# canary: 3 sends
LINKEDIN_SEND_DIR=<DIR> node scripts/send_batch.js 3

# inspect
cat <DIR>/batch_result.json

# if clean, batches of ~20
LINKEDIN_SEND_DIR=<DIR> node scripts/send_batch.js 20
```

The runner **auto-halts** and saves a screenshot to `<DIR>/cdp-shots/` on any restriction language or unverified send. The queue is fully resumable. This drives a **real** LinkedIn account -- canary first; halt on any restriction; pause between batches.

### 7. Track replies

As replies arrive (any session):

```bash
# log an outcome
python3 scripts/track_reply.py log \
  --lead <row|name|leadId-substr> \
  --outcome <replied|positive|negative|demo_sent|call_booked|deposit|closed_lost> \
  --text "optional note" \
  --dir <DIR>

# A/B conversion report
python3 scripts/track_reply.py stats --dir <DIR>
```

Outcomes update `prospects.csv` status columns (Reply, DemoSent, Call, Deposit, Notes) and append to `replies.jsonl`. `stats` shows per-variant reply rates and conversions so you can tell whether A or B is winning.

## Next skills

| Next | When |
|------|------|
| `jstack-linkedin-leads` / `jstack-linkedin-salesnav` | Need more leads before building the next batch. |
| Otherwise | Standalone — repeat steps 6-7 as replies come in; no required next step. |
