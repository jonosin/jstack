---
name: jstack-adscan
description: Scan the Meta Ad Library for advertisers and pull their ads (creative, flight dates, video files, store/landing links) with no API key or identity verification. Use when the user says /jstack-adscan, "scan the ad library", "find advertisers running ads for X", "pull <app/brand>'s Meta ads", "who's advertising X on Facebook/Instagram", or wants competitor/lead ad creative from the Meta Ad Library. Wraps the local adscan repo.
user_invocable: true
---

# jstack-adscan — Meta Ad Library scanner

Wraps a separate **`adscan`** CLI (built on `meta-ads-collector`, an internal-GraphQL
scraper: no API key, no verification, all countries, all ad types incl. US commercial).
The official Ad Library API does **not** return US commercial ads; this does.

This skill wraps an external repo that is **not bundled with jstack** — install it
separately and point `ADSCAN_DIR` at it (default `~/builds/adscan`). See README.

Run the wrapper (uses the repo's bundled venv):

```bash
"$ADSCAN_DIR"/adscan <scan|resolve|build> ...      # ADSCAN_DIR default: ~/builds/adscan
```

> ## AGENT BEHAVIORAL RULE — page-id first, keyword is NEVER complete
>
> A keyword `scan` is **discovery only** and is **NEVER** a page's complete ad set.
> To pull an advertiser's ads, **resolve the vague name to a page id**
> (`adscan resolve` / `build --resolve`) and **enumerate by id**. Use
> `--query`/`--match` (or `--page-name`) only as a **lossy** discovery fallback.
> If the resulting `ads.json` reports a `recall_gap` with `lossy: true`, the keyword
> result was **incomplete** — do NOT present it as the full set; **re-pull by page id**.
>
> This rule exists because a past run returned **1 ad** when the page had more.
> The `recall_gap` signal is the tripwire that catches that; obey it.

## Three modes

**Discovery (`scan`)** — which advertisers run ads for a keyword. Discovery ONLY —
this never returns a page's complete set:
```bash
"$ADSCAN_DIR"/adscan scan "peptide tracker"          # US, active, by impressions
"$ADSCAN_DIR"/adscan scan "menopause tracker app" -n 40 -c US
```
Prints advertiser, ad count, active count, image/video mix, and each app/landing link.

**Resolve (`resolve`)** — deterministically map a vague advertiser name → its canonical
ad-library page id (prints the id + a candidate ranking). No LLM, no randomness:
```bash
"$ADSCAN_DIR"/adscan resolve "Acme Resort Krabi" -c US
```

**Build (`build`)** — write one advertiser's ads to `<out>/<slug>/ads.json` + download
creatives. **Page-id first**, in recall order (most complete first):
```bash
# 1. RECOMMENDED — complete enumeration by page id (recall-complete via view_all_page_id)
"$ADSCAN_DIR"/adscan build <slug> --page-id 61571201360436 --company "Acme" --out <dir>

# 2. RECOMMENDED for a fuzzy name — resolve the name, then enumerate completely by id
"$ADSCAN_DIR"/adscan build <slug> --resolve "Acme Resort Krabi" --company "Acme" --out <dir>

# 3. LOSSY fallback only — keyword + advertiser-substring filter (or --page-name)
"$ADSCAN_DIR"/adscan build <slug> --query "peptide tracker" --match "Acme" --out <dir>
```
Images saved directly; videos saved as `.mp4` with an ffmpeg poster `.jpg`. Captures real
flight dates, CTA, platforms, and the store/landing URL (which identifies the developer).
`--page-id` paginates the page to exhaustion (`-n` never caps it); `--cap` is applied AFTER
the complete pull and prints how many ads were dropped to stderr — no silent truncation.

`--out` defaults to `$ADSCAN_ADS_DIR` or the current dir. Slug must match `[a-z0-9][a-z0-9-]*`.
Other flags: `--page-id` · `--resolve "<name>"` · `--page-name` · `--query`/`--match` ·
`-c US` · `-t all|political|housing|employment|credit` · `-s active|inactive|all`
· `-n` pull size · `--cap 7` ads kept · `--gap "..."` · `--no-clean`. Full flags: `adscan build -h`.

## Page-id-first flow (and the lossy keyword fallback)

To pull an advertiser, **prefer the page-id path** — it enumerates the page completely
(via Meta's `view_all_page_id` primitive) instead of finding ads by keyword:

```bash
# best: you already have the id (from the Ad Library URL or a prior resolve)
"$ADSCAN_DIR"/adscan build my-slug --page-id 61571201360436 --company "Resort" --out "$OUT"

# you only have a fuzzy name: resolve → enumerate completely, in one step
"$ADSCAN_DIR"/adscan build my-slug --resolve "Resort Name Krabi" --company "Resort" --out "$OUT"

# or resolve first to inspect the candidate ranking, then build by the printed id
"$ADSCAN_DIR"/adscan resolve "Resort Name Krabi" -c US
"$ADSCAN_DIR"/adscan build my-slug --page-id <printed-id> --company "Resort" --out "$OUT"
```

`--page-id` accepts either the ad-library URL id or the internal serving id — adscan
auto-resolves between them.

**Lossy keyword fallback** — use `--query`/`--match` (or `--page-name`) only when the
page-id path can't land the advertiser. `--page-name` is precise but fragile: Meta page
names often have trailing spaces, Unicode variants, or punctuation that cause "no ads
matched"; fall back to `--query` + `--match` using the advertiser name from the scan:

```bash
"$ADSCAN_DIR"/adscan build my-slug --query "resort Krabi" --match "Resort Name" --out "$OUT"
```

On this lossy path adscan computes a **`recall_gap`**: it resolves the dominant matched
page, enumerates it completely, and compares counts. If `ads.json` shows
`recall_gap.lossy == true` (and `fetch_status: "incomplete-keyword-recall"`), the keyword
result is **INCOMPLETE** — re-pull by page id (`--page-id`/`--resolve`) before using it.
Always open the scan results first to copy the exact advertiser name for `--match`.

**Watch for truncated names in scan output.** The scan table column width is limited — names ending mid-word, at a punctuation mark, or with a trailing space/punctuation (e.g. `"Santhiya Phuket Natai Resort &"`, `"Baba Beach Club Natai by Sri p"`, `"The Cape Pool Villas - Koh Sam"`) are truncated. These will fail as `--page-name` values. When the scan name looks incomplete, skip `--page-name` and go straight to `--query` + `--match` with a known-unique substring from the visible portion.

## Batch builds

When pulling multiple advertisers, chain builds with `&&` under a single generous timeout.
Run a `scan` first to discover the advertisers, then batch the builds — prefer
`--resolve "<name>"` (or a resolved `--page-id`) so each build is recall-complete:

```bash
export ADSCAN_DIR=~/builds/adscan OUT=~/project/research/ads
"$ADSCAN_DIR"/adscan build slug1 --resolve "Advertiser One" --company "One" --out "$OUT" && \
"$ADSCAN_DIR"/adscan build slug2 --resolve "Advertiser Two" --company "Two" --out "$OUT" && \
"$ADSCAN_DIR"/adscan build slug3 --resolve "Advertiser Three" --company "Three" --out "$OUT"
```

A `--page-id`/`--resolve` build writes a clean empty `ads.json` (exit 0) when a page has no
ads, so it won't break the chain. The lossy `--query`/`--match` fallback also exits 0 on no
match. When running many builds (5+), prefer parallel `terminal()` calls with individual
timeouts over a single chained command — this avoids losing all progress when one build
fails. After a lossy build, check `recall_gap` in each `ads.json` and re-pull any
`lossy: true` result by page id.

## Verification pass (active-count reliability)

Active-ad counts from `scan` can be noisy (pagination timing, rate limiting). Before
reporting an active count as fact: re-run the same `scan`/`resolve` query once and compare
the two counts.
- **Match** → report the count normally.
- **Mismatch** → report BOTH counts explicitly and flag low confidence, e.g. "active count
  varied between runs (14 vs 17) — treat as approximate, re-pull by page id for the
  authoritative set." Never silently pick one number.
This is a re-query, not a full re-build — it only applies to the cheap `scan`/`resolve`
counts, not a full `build`.

## Friendly error mapping (no raw tracebacks)

Map the CLI's failure modes to one-line, actionable messages instead of surfacing a raw
Python traceback or stack dump:

| Failure mode | Message to give the user |
|---|---|
| No page/advertiser resolved (`resolve` returns no candidates) | "No advertiser page matched '<name>'. Try a shorter/different substring, or search the Ad Library UI for the exact page name." |
| Auth/session missing (internal GraphQL call unauthenticated or blocked) | "adscan's Meta session looks expired or blocked. Re-run the repo's login/session-refresh step in `$ADSCAN_DIR`, then retry." |
| Empty result (`ads.json` has zero ads, page has no active/inactive ads matching filters) | "No ads found for this advertiser under the current filters (country/status/type). Confirm the page id is correct or widen `-s`/`-c`/`-t`." |
| Stale `doc_id` warning | "Meta changed its internal API shape. Run the repo-maintenance upgrade below (`pip install -U meta-ads-collector`) and retry." |
| Any other non-zero exit with a traceback | Surface the last stderr line only, prefixed "adscan failed:" — do not paste the full Python traceback into the response. |

## Config resolution

All adscan output-path config (`ADSCAN_DIR`, `ADSCAN_OUT`, `ADSCAN_ADS_DIR`) resolves in
order: environment variable → `~/.jstack/config.env` → built-in default (`ADSCAN_DIR` →
`~/builds/adscan`; `ADSCAN_OUT`/`ADSCAN_ADS_DIR` → the consuming project's `research/ads`
dir, or the current dir if none). Never hardcode a personal absolute path in this skill —
use `$ADSCAN_DIR`/`$ADSCAN_OUT` or the config-file lookup above.

## What it does NOT do
Fetches and structures ads only. It does **not** grade creative (weak/okay/good) or write
any dossier — that's the agent/human's judgment after opening the downloaded media.

## Project use
When working inside a project, write creatives to that project's research dir so it
renders them as-is. Resolve the output dir in this order:
1. `$ADSCAN_OUT` if set (export it, or put it in `~/.jstack/config.env`).
2. Else the consuming project's `research/ads` dir.

If `~/.jstack/local.md` lists per-project output paths, honor the one for the project
you are working on.
```bash
"$ADSCAN_DIR"/adscan build acme --page-name "Acme.io" --company "Acme" \
  --out "${ADSCAN_OUT:-$HOME/projects/<your-project>/research/ads}"
# verify: curl -s "http://localhost:8770/api/ads?slug=acme"
```

## Repo maintenance
If a run warns about a stale `doc_id` (Meta changed its internal API) or the venv is missing:
```bash
cd "$ADSCAN_DIR" && python3.11 -m venv .venv && \
  ./.venv/bin/pip install -U meta-ads-collector
```
Needs `ffmpeg` on PATH for video poster frames.

## Next skills

| Next | When |
|---|---|
| `marketing-skills:ad-creative` | Turn the pulled competitor creative into your own ad-copy variations / iterations. |

Otherwise standalone — adscan fetches and structures ads; grading and dossier-writing are the agent's/human's judgment after opening the media.
