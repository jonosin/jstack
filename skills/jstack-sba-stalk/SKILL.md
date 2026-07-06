---
name: jstack-sba-stalk
description: "Enrich a Second Brain Agency prospect end to end — who they are, what their company does, LinkedIn About + recent posts, size/revenue signals — then calculate a defensible internal price-estimate band (WTP-matched, ADR-0008) and write the whole read to clients/<slug>/research.md with every claim cited. Use when Jono says /jstack-sba-stalk <slug>, 'stalk <prospect>', 'research <prospect> before the call', 'enrich <slug>', 'what should I charge <prospect>', or a reply/call needs full client context. NOT for drafting outreach or the B0 video (jstack-sba-personalization), NOT for adding prospects (jstack-sba-add-prospects)."
---

# jstack-sba-stalk

Pre-call intel + pricing pass for one SBA prospect. Produces ONE artifact — an enriched
`clients/<slug>/research.md` — that any future agent can read cold for full client context.
Quality bar: `clients/gga/research.md` (the exemplar) — wallet-first sizing, per-claim
confidence, landmines flagged. The estimate is **internal**: the quoted number still follows
ADR-0008 (hold until the call).

Venture root: `SBA_VENTURE` (`~/.jstack/config.env` → default `~/ventures/second-brain-agency`) = `$SBA`.

> **Registry first (family rule):** `$SBA/prospects/prospects.csv` + `conversations.json` (read
> surgically via `prospects/convo.py`) are the source of truth for who the prospect is and what
> they said. Resolve the prospect there before fetching anything.

## Inputs

Slug (preferred; `clients/<slug>/` must exist — if not, run `$SBA/scaffold_client.sh <slug>` first).
Fallbacks: `--lead <salesnav id/url>`, `--url <linkedin /in/ url>`, `--row <registry row>`.
Read the reply thread too (`python3 $SBA/prospects/convo.py --name <x> --no-messages`, drop
`--no-messages` only if the thread matters): `last_inbound` + `segment` shape the wallet read.

## Step 1 — deterministic LinkedIn fetch (free, live, logged-in)

```bash
python3 ~/.claude/skills/jstack-sba-stalk/scripts/stalk_fetch.py --slug <slug> --posts 3
```

Runs the OpenCLI CDP ladder against Jono's Brave (:9222) and writes
`$SBA/clients/<slug>/stalk-raw.json`: **salesnav-profile** (About, positions, education,
industry — via URN built from the lead ID; works for every registry row) → **profile-read**
(canonical vanity URL via the `/in/<leadId>` 301 + About fallback) → **posts** (top N with
engagement). Rungs fail independently into `meta.failures`; exit 69 = run the `brave-cdp`
skill and retry; `posts: EMPTY_RESULT` usually just means they don't post (common — note it,
it is itself a signal). Sales Nav rung dies when the subscription lapses — the other rungs
still deliver.

**Escalation:** blocked/rate-limited, or a FULL feed pull is wanted (GGA precedent: 518 items,
$0.94) → Apify HarvestAPI via `~/.claude/skills/jstack-linkedin-leads/scripts/linkedin_apify.py
posts --input '{"targetUrls": ["<canonical>"], "maxPosts": 0, "includeReposts": true}'` —
dry-run by default; spend only with `--execute --max-charge`, 1-post shape test (cap $0.05)
before a full pull; if the sync call times out, recover the dataset by run id (see
`references/method-archaeology.md`). Company-side facts → step 2, never scraped from LinkedIn.

## Step 2 — company-side research (judgment, cited)

Route through `research-router` (Exa discovery + `mcp__exa__web_fetch_exa`/Jina extraction;
Tavily quota-fails often — fall back to Exa). For a substantial account, fan out parallel
**Sonnet** subagents (identity/company · size/revenue · buyer background) like the five prior
research.md files were built. Hunt specifically:
- **Identity:** site, HQ, what they actually do (not what the name suggests), structure, end markets.
- **Size/revenue signals:** aggregator reads (Prospeo/RocketReach/Blitzr-style — label LOW-MED),
  real payroll headcount vs headline scale, funding/ownership.
- **Disambiguation:** same-name entities (GGA ≠ GGA Solutions). A wrong fact burns credibility.
- Every claim gets a source + confidence (HIGH/MED/LOW). Inference is labelled inference.

Never web-fetch `linkedin.com/in/…` directly (403s). If step 1's CDP path is down entirely,
profile facts come from **Exa's cached person library** (`exa.ai/library/person/…`) +
aggregators — the pre-CDP method (see `references/method-archaeology.md`).

## Step 3 — price estimate (internal band, WTP-matched)

Reason the **spendable wallet, not headline scale** (template doctrine). Drivers, each cited
from steps 1–2:
1. **Ownership/authority** — owner-operator (fast close, personal wallet) vs employed exec
   (procurement gate)?
2. **Real wallet** — HQ payroll + modeled revenue + margin posture; a big network/brand with a
   2-person office prices like a 2-person office (GGA lesson).
3. **Tech-spend posture** — visible SaaS/site quality; low spend = price-sensitive but
   outcome-buying (price the outcome, never a subscription).
4. **Felt pain / awareness** — their own words in the reply thread; AI-aware hunters carry
   higher WTP than educated-from-scratch owners.

Map onto the venture ladder (brain: build ~$1.5k–5k one-time, retainer ~$300–1.5k/mo; offer
ladder audit $500–750 → build ~$2.5k → retainer ~$500/mo) per **ADR-0008**: high-WTP → a range
("$2k–5k depending on scope"); floor-WTP → single low anchor ("starts around $2k"), never the
full range. Output = **band + anchor shape + top 3 drivers + confidence** — and the note that
the number is held until the call (`~/jstack-sba/playbook/price-ask-response.md` governs the ask).

## Step 4 — write the artifact

Fill EVERY section of the template shape (`$SBA/clients/_template/research.md`) plus a
`## Price estimate` section (band, anchor shape, drivers, confidence, what would move it).
Keep `stalk-raw.json` beside it as evidence. Flag landmines prominently (political feeds —
Jennifer/Doug precedent; stale facts; do-not-say items). Then:
- Acceptance: `grep -c '<' $SBA/clients/<slug>/research.md` shows no template placeholders left;
  every claim has a source; posts cited with dates.
- Update the folder `README.md` status line (e.g. `status: researched`).
- A durable strategy fact surfaced? → `/jstack-savetobrain` (never write the brain from the repo).

## Gotchas

Read-only stalking: never connect/message/react through the driven session. Respect the
Commercial Use Limit (no people-search sweeps; this skill reads known profiles). Method
lineage + evidence of what each rung returns: `references/method-archaeology.md`.

## Next skills

| Next | When |
|------|------|
| `jstack-sba-personalization` | The enriched read feeds a B0/video/reply for this prospect. |
| `/jstack-myvoice` | Drafting the actual price-ask reply or call opener in voice. |
| `/jstack-savetobrain` | A durable venture fact (pricing posture shift, ICP signal) surfaced. |
| `jstack-sba` | Back to the venture front door for the next account. |
