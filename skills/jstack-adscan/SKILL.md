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

## What it does NOT do
Fetches and structures ads only. It does **not** grade creative (weak/okay/good) or write
any dossier — that's the agent/human's judgment after opening the downloaded media.

## Project use
Point `--out` at the consuming repo so it renders the creatives as-is:
```bash
"$ADSCAN_DIR"/adscan build acme --page-name "Acme.io" --company "Acme" \
  --out ~/projects/<your-project>/research/ads
# verify: curl -s "http://localhost:8770/api/ads?slug=acme"
```

## Repo maintenance
If a run warns about a stale `doc_id` (Meta changed its internal API) or the venv is missing:
```bash
cd "$ADSCAN_DIR" && python3.11 -m venv .venv && \
  ./.venv/bin/pip install -U meta-ads-collector
```
Needs `ffmpeg` on PATH for video poster frames.
