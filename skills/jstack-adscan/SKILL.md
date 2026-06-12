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
"$ADSCAN_DIR"/adscan <scan|build> ...      # ADSCAN_DIR default: ~/builds/adscan
```

## Two modes

**Discovery** — which advertisers run ads for a keyword:
```bash
"$ADSCAN_DIR"/adscan scan "peptide tracker"          # US, active, by impressions
"$ADSCAN_DIR"/adscan scan "menopause tracker app" -n 40 -c US
```
Prints advertiser, ad count, active count, image/video mix, and each app/landing link.

**Build** — write one advertiser's ads to `<out>/<slug>/ads.json` + download creatives:
```bash
# precise (recommended): by page name
"$ADSCAN_DIR"/adscan build <slug> --page-name "Acme.io" --company "Acme" --out <dir>

# or keyword + advertiser-substring filter
"$ADSCAN_DIR"/adscan build <slug> --query "peptide tracker" --match "Acme" --out <dir>
```
Images saved directly; videos saved as `.mp4` with an ffmpeg poster `.jpg`. Captures real
flight dates, CTA, platforms, and the store/landing URL (which identifies the developer).

`--out` defaults to `$ADSCAN_ADS_DIR` or the current dir. Slug must match `[a-z0-9][a-z0-9-]*`.
Other flags: `-c US` · `-t all|political|housing|employment|credit` · `-s active|inactive|all`
· `-n` pull size · `--cap 7` ads kept · `--gap "..."` · `--no-clean`. Full flags: `adscan build -h`.

## Page-name vs query fallback

`--page-name` is precise but fragile. Meta page names often have trailing spaces, Unicode
variants, or punctuation that cause "no ads matched." When a `--page-name` build fails,
retry with `--query` + `--match` using the advertiser name from the scan output:

```bash
# first attempt (precise)
"$ADSCAN_DIR"/adscan build my-slug --page-name "Resort Name" --company "Resort" --out "$OUT"

# fallback (query + substring match)
"$ADSCAN_DIR"/adscan build my-slug --query "resort Krabi" --match "Resort Name" --out "$OUT"
```

Always open the scan results first to copy the exact advertiser name for `--match`.

**Watch for truncated names in scan output.** The scan table column width is limited — names ending mid-word, at a punctuation mark, or with a trailing space/punctuation (e.g. `"Santhiya Phuket Natai Resort &"`, `"Baba Beach Club Natai by Sri p"`, `"The Cape Pool Villas - Koh Sam"`) are truncated. These will fail as `--page-name` values. When the scan name looks incomplete, skip `--page-name` and go straight to `--query` + `--match` with a known-unique substring from the visible portion.

## Batch builds

When pulling multiple advertisers, chain builds with `&&` under a single generous timeout.
Run a `scan` first to discover exact page names, then batch the builds:

```bash
export ADSCAN_DIR=~/builds/adscan OUT=~/project/research/ads
"$ADSCAN_DIR"/adscan build slug1 --page-name "Advertiser One" --company "One" --out "$OUT" && \
"$ADSCAN_DIR"/adscan build slug2 --page-name "Advertiser Two" --company "Two" --out "$OUT" && \
"$ADSCAN_DIR"/adscan build slug3 --page-name "Advertiser Three" --company "Three" --out "$OUT"
```

Failed builds exit non-zero and stop the chain. Retry failed ones individually with `--query` + `--match`. When running many builds (5+), prefer parallel `terminal()` calls with individual timeouts over a single chained command — this avoids losing all progress when one build fails.

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
