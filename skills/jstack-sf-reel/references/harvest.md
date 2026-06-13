# Phase 1 — Harvest (OTA gallery → screening batch)

Goal: a resort name or OTA link → every listing photo at max resolution → a `reference-images`
screening batch the dashboard auto-discovers. Mechanics live in the `jstack-otagallery` skill
(kept as a general tool); this is the StayFrame-wired path.

## 1. Resolve the listing URL
Name only? Find the listing: `tvly search "<property> site:booking.com"` or exa. Prefer Booking.com
(verified end-to-end); Agoda/Airbnb/Expedia work via the same DOM-harvest pattern.

## 2. Render the page (headless)
gstack browse (preferred):
```bash
B="$HOME/.claude/skills/gstack/browse/dist/browse"
$B newtab "<url>"; sleep 6; $B html > /tmp/ota-page.html; $B closetab
```
Fallbacks in order: playwright MCP → `r.jina.ai/<url>` → brave-cdp logged-in session. Sanity: the
HTML must be >500KB — a few KB is a bot stub (retry with longer sleep or the next fallback).

## 3. Extract + download
```bash
python3 ~/jstack/skills/jstack-otagallery/scripts/booking_gallery.py \
  --html /tmp/ota-page.html --outdir /tmp/<slug>-gallery
# --size max1600 (default) · --workers 8 · re-runs skip files >10KB (safe retry)
```
Other OTAs: per-site CDN regex in `~/jstack/skills/jstack-otagallery/references/ota-cdn-patterns.md`.

## 4. Write the screening batch
**Path note:** otagallery's own SKILL step 5 still shows a stale `pipeline/qa/queues/` path — use
the real one below (`qa/queues/`), per `~/ventures/stayframe/qa/AGENTS.md`.
```
~/ventures/stayframe/qa/queues/<batch-id>/
├── manifest.json
└── media/<id>.jpg          # copy the downloads here
```
- `batch-id` = `YYYY-MM-DD-<slug>-reference-images` (a re-pull gets `-n2`, etc. — NEVER append to a
  batch Jono already triaged; new pulls = new batch so existing verdicts stay intact).
- `manifest.json` (per qa/AGENTS.md): `{ batch_id, gate:"reference-images", property:"<slug>",
  title, created, items:[ { id, file:"media/<f>.jpg", source:"<OTA> gallery, pulled <date> @<size>",
  agent_note } ] }`.

## 5. Optional dedupe (default OFF — Jono re-triages by hand)
Only when asked: `uv run --with pillow ~/jstack/skills/jstack-otagallery/scripts/dedupe_dhash.py
--new <dir> --existing <reviewed-dir>` (dHash, hamming ≤6 = dup).

## 6. Hand off (HUMAN GATE — screening)
Ensure the dashboard is up, then stop:
```bash
curl -s -o /dev/null http://localhost:7777/ || (cd ~/builds/stayframe-qa && node server.js &)
```
Tell Jono: "`<N>` photos from `<OTA>` ready to screen at http://localhost:7777 — batch `<title>`."
Screening is his. The pipeline resumes (Phase 3) when he re-invokes `/jstack-sf-reel <resort>`.
