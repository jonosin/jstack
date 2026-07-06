# Method lineage + live-test evidence

Why the skill's ladder looks the way it does: what the five prior enriched research.md files
(gga, aicg, bargains-group, ark-simplify, marinesolar-energy — 2026-06-12→07-01) actually used,
plus captured evidence from the 2026-07-06 OpenCLI live tests that grounded step 1.

## OpenCLI CDP live tests (2026-07-06, this skill's build session)

All via `opencli-cdp.sh linkedin <cmd> -f json` against Jono's logged-in Brave (:9222).

| Command | Input tested | Result |
|---|---|---|
| `profile-read --profile-url https://www.linkedin.com/in/marcshepard/` | third-party public URL | ✅ name + headline; `about` empty (profile genuinely has none) |
| `profile-read --profile-url https://www.linkedin.com/in/<leadId>/` | Kohler's SN lead ID as /in/ URL | ✅ 301s to canonical vanity URL (`andrew-kohler-4475151b0`), full About returned |
| `posts --profile-url … --limit 3` | third-party public URL | ✅ full bodies, engagement, `posted_at`, repost attribution |
| `posts` on a non-poster | Kohler | `EMPTY_RESULT` exit 66 — means "doesn't post", not "broken" |
| `salesnav-profile <sales/people URL>` | registry's raw URL | ❌ ARGUMENT error — not an accepted form |
| `salesnav-profile "urn:li:fs_salesProfile:(<leadId>,NAME_SEARCH,blank)"` | URN built from lead ID | ✅ richest read: About, positions, education, industry, degree, openProfile |

Decisive tricks the fetch script encodes:
- **Registry lead ID → URN**: `urn:li:fs_salesProfile:(<leadId>,NAME_SEARCH,blank)` makes
  `salesnav-profile` work for every registry row (no public URL needed).
- **`/in/<leadId>` 301 recovery**: resolves the canonical vanity URL while logged in — same
  mechanism as the brain's SN-cancellation workaround card (2026-07-01). Feeds the `posts` rung.
- `salesnav-profile` needs a live Sales Navigator subscription; `profile-read`/`posts` don't.

Apify fallback (dry-run verified 2026-07-06): `linkedin_apify.py posts --input
'{"profileUrls": […], "maxPosts": N}'` → HarvestAPI `linkedin-profile-posts`, pay-per-result,
`--execute --max-charge` to spend.

## How the five prior research.md files were made (artifact evidence)

From the files' own headers + the GGA exemplar:
- **Parallel research subagents** (gga: "three parallel research agents", 2026-06-29) doing
  company-side lanes; Exa as the discovery workhorse + aggregator reads
  (Prospeo/RocketReach/Blitzr/success.ai — revenue labelled LOW-MED), Jina/curl extraction.
  **Tavily was plan-rate-limited repeatedly** and fell back to Exa (gga + aicg headers).
- **LinkedIn profile facts arrived indirectly** pre-CDP: e.g. gga cites
  `linkedin.com/in/jswilliamsgga (via Exa crawl 2026-06-12; page itself 403s)`.
- **The GGA "full post pull 2026-06-29"** (518 feed items) was an **Apify run**
  (`Wuygtf2xDcRHTqt0E`, $0.94) — raw → `jennifer-posts.json`, curated →
  `jennifer-voice-extract.md`. That pull produced the political-feed landmine finding, the
  reason step 4 requires a landmine scan of posts.
- Conventions the exemplars set, kept by this skill: per-claim confidence (HIGH/MED/LOW),
  disambiguation warnings up top, wallet-vs-network sizing, inference labelled as inference.

## Transcript archaeology (session search 2026-07-06)

Sessions: GGA post pull = `623a18bd`; GGA 3 parallel sales-intel agents = `f32fe935`;
ark-simplify/marinesolar/bargains-group/gga personalize-with-fresh-research quartet = `50c94f4d`;
AICG/Sam Fagan 3-agent build = `f8969c9b`; Harry WTP = `f830441c`; Kohler read = `60745b81`.

**The GGA post pull, exactly.** Apify HarvestAPI `linkedin-profile-posts` via
`linkedin_apify.py posts`, two rungs: a 1-post shape test capped at `--max-charge 0.05`, then
the full pull with input `{"targetUrls": ["…/in/jswilliamsgga/"], "maxPosts": 0,
"postedLimit": "any", "includeReposts": true, "includeQuotePosts": true}` capped at $1.00 →
518 items, $0.94, run `Wuygtf2xDcRHTqt0E`. **Field name is `targetUrls`.** The sync call blew
the 2-min shell timeout; the dataset was recovered without re-charging via
`curl "https://api.apify.com/v2/datasets/<runId>/items?token=$APIFY_API_TOKEN&clean=true&format=json"`.

**Subagent pattern.** `Agent` tool, `general-purpose`, explicit `model: sonnet`, 3–4 in
parallel, background. Two shapes: (A) sales-intel lanes — identity/structure · size&budget ·
buyer/authority (GGA, AICG); (B) per-client "personalize with fresh research first"
(the 50c94f4d quartet). Every prompt hard-coded: the template's section skeleton, "every
factual claim needs a source URL or an explicit '(inference, not sourced)' tag", HIGH/MED/LOW
per claim, "say so plainly rather than padding", and — in later sessions — "read and follow
the global research-router skill EXACTLY … do not freelance with random tools."

**Tool truth per lane.** Exa carried discovery + fetch (`exa-search "<q>" 10 auto`,
`web_fetch_exa`); Jina/`r.jina.ai` + curl as extraction fallback; **Tavily was the weak link**
(plan-rate-limited across sessions; `tvly research --model pro` exhausts quota and keeps
failing — don't retry, reserve `tvly extract` only); `gh` for repos; xAI `x_search`
opportunistic (AICG: no matches, recorded as such).

**LinkedIn profile facts pre-CDP** were never fetched live (`/in/` 403s to web tools). They
came from **Exa's cached person library** (`exa.ai/library/person/…`, e.g. `pxz0h65hq0r` for
Jennifer — crawl date 2026-06-12) + aggregators (RocketReach, success.ai, ZoomInfo, Apollo,
Prospeo, Blitzr). Still the right fallback when CDP is unavailable. (The original 2026-06-12
Exa crawl predates retained transcripts — output confirmed, exact call not recoverable.)

**Wallet reasoning lineage.** ADR-0008 doctrine; GGA band reasoned off the HQ family wallet
vs the 15-plant network; the Kohler "$2k–5k" (2026-07-05) was the standing benchmark applied
to a high-WTP owner-operator via drivers 1+4 — **benchmark-derived, not economics-derived**
(ADR-0008 flags the economics session as still owed). Estimates produced by this skill should
carry that caveat until the pricing-economics session lands.
