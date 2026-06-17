---
name: jstack-otagallery
description: Extract and download the full property photo gallery from an OTA listing (Booking.com verified; Agoda/Airbnb/Expedia/direct-booking engines via the same pattern) at max resolution, with optional perceptual dedupe and optional stayframe-qa review batch output. Use when the user says /jstack-otagallery, "download the photos from booking.com", "pull the gallery from the OTA listing", "get every photo of a property", "the listing has N images, download them all", or any request to collect a hotel/resort/villa's listing photos for the Stayframe pipeline.
---

# jstack-otagallery — full OTA gallery extraction

Pull every photo from a property's OTA listing at max resolution. Verified end-to-end on
Booking.com 2026-06-12 (Serenity Sands: 91/91 photos, ~22MB, anonymous — no login).

## Core insight (why this works)

OTA *pages* are bot-walled (plain curl gets a ~4KB stub), but their image *CDNs* are not.
So: render the page once in a headless browser → harvest CDN URLs from the DOM → download
everything anonymously and in parallel straight from the CDN. The page HTML embeds the FULL
gallery (all sizes of every photo), not just what's visible — no clicking through galleries.

## Workflow

### 1. Get the listing URL

If the user gives only a property name: `tvly search "<property> site:booking.com"` or
`exa-search "<property> booking.com hotel"` (research-router lanes).

### 2. Render the page (headless browser)

Any available browser tool works. gstack browse (preferred — fast, persistent):

```bash
B="$HOME/.claude/skills/gstack/browse/dist/browse"
$B newtab "<listing-url>" ; sleep 6
$B html > /tmp/ota-page.html
$B closetab
```

Fallbacks, in order: playwright MCP → `r.jina.ai/<url>` (extraction is lossier) →
brave-cdp logged-in session (only if the OTA blocks headless).

Sanity check: the HTML file should be >500KB. A few-KB file = bot stub; retry with longer
sleep or the next fallback.

### 3. Extract + download — `scripts/booking_gallery.py`

Booking.com (verified):

```bash
python3 {baseDir}/scripts/booking_gallery.py --html /tmp/ota-page.html --outdir <dir>
# options: --size max1600 (default) | max1280x900 | max1024x768 · --workers 8
```

Prints one `<id>.jpg <bytes|cached|FAIL ...>` line per photo; exits non-zero on failures.
Re-runs skip existing files (>10KB), so retry is safe.

Other OTAs / direct-booking engines: same harvest-from-DOM pattern, different CDN regex —
see [references/ota-cdn-patterns.md](references/ota-cdn-patterns.md) for per-site URL
patterns, max-res parameters, and the verified imgix direct-booking-engine lane. Adapt the
extraction regex inline; the download half of the script is reusable via `--map`.

### 4. OPTIONAL — perceptual dedupe vs an existing set

**Default is NO dedupe** (the user prefers to re-triage by hand). Only when asked:

```bash
uv run --with pillow {baseDir}/scripts/dedupe_dhash.py \
  --new <new-gallery-dir> --existing <already-reviewed-dir>
```

dHash, hamming ≤6 = duplicate. Verified across different CDNs of the same photos (imgix vs
bstatic): true dupes land at distance 0–2. Run via `uv` — system python lacks PIL.

### 5. OPTIONAL — stayframe-qa review batch

If the photos are for Stayframe triage, emit the file contract the QA dashboard
(`~/builds/stayframe-qa`, localhost:7777) auto-discovers:

```
~/ventures/stayframe/qa/queues/<batch-id>/
├── manifest.json   {"batch_id", "title", "gate": "reference-images",
│                    "property", "items": [{"id", "file": "media/<f>.jpg",
│                    "source": "<OTA> gallery (<cdn-id>), pulled <date> @<size>",
│                    "agent_note": "..."}]}
└── media/<id>.jpg  (copy the downloads here)
```

Batch-id convention: `YYYY-MM-DD-<property>-<source-slug>`. Never append to a batch the
human has already triaged — new pulls get a NEW batch so existing verdicts stay intact.

## Report back

Photo count found vs downloaded, output dir, total size, and (if QA batch) the batch title
as it appears in the dashboard. Log source URLs — provenance is part of the Stayframe
pipeline contract.

## Next skills

| Next | When |
|---|---|
| `/jstack-sf-new <resort>` | The harvested photos are for a resort reel — feed them into the pipeline (screen → catalog → creative → produce). |
| `/jstack-sf` | Unsure where the resort is in the pipeline — read-only status / route to the right next step. |
