---
name: jstack-sf-outreach
description: "Run StayFrame/Facet cold outbound from the prospect table. Use when tiering hospitality leads, choosing contact channels, drafting first touches/follow-ups, planning give-first spec reel or Loom outreach, tracking reply metrics, or preparing the first 50 manual sends."
---

# jstack-sf-outreach - cold outbound playbook

Runs S7/S8/S9 for Facet/StayFrame: tier leads, choose channels, draft messages, and turn positive
replies into a spec reel plus Loom follow-up.

## Inputs

Preferred input:
`~/ventures/stayframe/leads/scoring/prospects-s7-ranked.csv`

If missing or stale, invoke `/jstack-sf-leads` and run:

```bash
python3 ~/jstack/skills/jstack-sf-leads/scripts/sf_leads.py rank --top 25
```

Load `references/playbook.md` when drafting or planning a send batch.
Load `references/contact-method.md` when deciding how to reach owners or route through generic inboxes.

## Flow

1. Select only T1/T2 leads unless Jono asks for a bench/one-off.
2. Pick the channel from `recommended_channel`: email, Instagram DM, Facebook DM, phone discovery, or LinkedIn after owner enrichment.
3. Pick the frame from `message_frame`: visual-multiplication, occupancy-led, commission-led, or ab-test.
4. Draft the message through `/jstack-msgdraft`, preserving the rules below.
5. If the prospect replies positively, create/polish the preview via `/jstack-sf-new <resort>` and send an async Loom walkthrough. Do not jump to Zoom as the default.
6. Track replies in `~/ventures/stayframe/outreach/logs/` when S9 starts.

## Rules

- Give-first works, but the first CTA should be permission-based: "Want me to send it over?"
- Do not open by criticizing their creative. Lead with the upside in their existing raw material.
- Do not reveal the list filter or make the message sound generated.
- Full reel plus Loom is for opt-ins or the highest T1s, not every cold lead.
- Commission recovery is price logic or an A/B frame, not a guaranteed outcome.
- TH direct means LINE/IG DM. Do not promise official-site bookings.
- AU first touch should usually be email, then Instagram if email is missing or ignored.

## Next skills

| Next | When |
|------|------|
| `/jstack-sf-leads` | The ranked S7 file is missing/stale, or more leads need enrichment. |
| `/jstack-msgdraft` | Drafting or polishing the actual email/DM in Jono's voice. |
| `/jstack-sf-new <resort>` | A prospect opted in and needs a preview/spec reel from public photos. |
| `/jstack-sf-check` | Jono left dashboard feedback on the preview/spec reel. |
