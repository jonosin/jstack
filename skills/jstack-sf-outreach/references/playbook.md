# StayFrame Cold Outbound Playbook

Input:
`~/ventures/stayframe/leads/scoring/prospects-s7-ranked.csv`

If missing, invoke `/jstack-sf-leads` and run:

```bash
python3 ~/jstack/skills/jstack-sf-leads/scripts/sf_leads.py rank --top 25
```

## Core Position

Facet/StayFrame sells an AI content operator for boutique hospitality: no-shoot, public-asset-based
reels and organic management for owner-operated resorts, villas, glamping, and boutique hotels.

Do not lead by insulting the prospect's current creative. Lead with the upside:
- their property already has strong raw material
- guests check social proof before booking
- Facet can multiply existing public assets into platform-native travel content
- the free preview is a give-first proof artifact, not a generic audit

## Message Frames

`visual-multiplication`
: Best for high-ADR villa/luxury properties with strong visuals. Frame as multiplying existing
photos into short-form reels without another shoot.

`occupancy-led`
: Best for small hotels, lodges, nature/glamping, and OTA-dependent properties. Frame as keeping the
property alive when guests check IG/TikTok before booking.

`commission-led`
: Use lightly. It is price logic and an A/B frame, not a hard promise. Say "built to recover some
demand into direct LINE/IG inquiries", never guarantee direct bookings.

`ab-test`
: Use when the row says `commission_or_occupancy`; draft both and send only one after a human pick.

`do-not-prioritize`
: Do not send unless Jono explicitly wants a benchmark, one-off, or channel-partner pitch.

## First Touch Shape

Keep it short and permission-based.

```
Hi <name/property>,

I was looking at <property> and your public photos already have a lot to work with.

I made a short preview showing how they could look as native travel reels, without a new shoot.
Want me to send it over?
```

For active ad advertisers, adapt:

```
I noticed you are already putting budget behind the property.
The thought was: your existing photos could probably be turned into more scroll-native variants,
without another shoot.
```

For TH direct:
say LINE/IG booking inquiries. Do not say official website bookings.

For AU:
email first when available, then Instagram DM. Phone is for owner discovery, not a hard pitch.

## Reply Path

If they say yes:
1. Produce or polish the preview/spec reel.
2. Send the reel plus a short Loom walkthrough.
3. Loom structure: greet them, show the reel, name 2-3 precise observations, explain that the system
   turns existing photos into many variants, then ask whether this is useful enough to test monthly.
4. If interest persists, move to paid pilot terms. Do not keep making free full reels.

If they ask what this is:
explain "I run an AI content operator for boutique hospitality. We turn existing property assets into
weekly short-form reels and manage posting/iteration."

If they ask for results:
be honest. The first pilots are proof engines. Use craft proof and comparable channel logic, not fake
booking-lift claims.

## Scoreboard

Manual first 50 sends:
- 25 commission-led or direct-demand frame
- 25 occupancy/visibility frame
- metric: qualified positive replies

Targets:
- reply >= 18%
- positive >= 8%
- connection acceptance >= 40% where relevant

Diagnose:
- low acceptance: targeting or warm-up problem
- low reply: copy/channel problem
- low positive: offer-fit problem

## Channel Priority

1. Email when a direct property email exists.
2. Instagram DM when the feed is active and visually strong.
3. Facebook DM for TH properties or pages with current ad activity.
4. Phone only to ask who handles marketing, not to deliver the pitch cold.
5. LinkedIn only after owner/operator discovery.

For owner access, do not over-solve before first touch. If the direct email or IG account is official,
ask a routing question:
"Is there a better person who handles marketing/content for the property?"
