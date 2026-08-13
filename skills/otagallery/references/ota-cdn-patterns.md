# OTA CDN patterns — per-site extraction notes

Status legend: ✅ verified end-to-end · ⚠️ pattern known, untested (verify before trusting).

## Booking.com ✅ (2026-06-12, Serenity Sands, 91/91)

- CDN: `cf.bstatic.com/xdata/images/hotel/<size>/<id>.jpg?k=<hex>&o=`
- The `k=` hash is REQUIRED and per-photo — harvest id+k pairs together.
- Size segment is caller-controlled: `max1600` (good default), `max1280x900`,
  `max1024x768`, `square60`… Rewriting the size on a harvested URL works.
- Page embeds every gallery photo in the initial HTML (no gallery clicking needed).
- Unique-photo identity = the numeric `<id>`; the same id appears at many sizes.
- `scripts/booking_gallery.py` implements this lane.

## Direct-booking engines on imgix ✅ (book-directonline.com, 56/56, 2026-06-12)

Many boutique properties run booking engines whose galleries sit on imgix — fully
anonymous, no headless browser needed:

```
r.jina.ai/https://book-directonline.com/properties/<PropertySlug>
→ grep 'tbb-prod-apac.imgix.net/attachments/[^")]*jpg'
→ strip query params, append ?auto=format&w=1600&q=85
```

imgix params are caller-controlled (`w=`, `q=`, `auto=format`); original aspect, no crop.
Check the property's own site / linktr.ee for which engine they use.

## Agoda ⚠️

- CDN: `pix{1..10}.agoda.net/hotelImages/<hotel_id>/.../<file>.jpg?ce=0&s=<W>x<H>`
- `s=` size param is caller-controlled — try `s=1600x` or strip for original.
- Property page embeds an image array in initial HTML (`hotelImages`); harvest like Booking.

## Airbnb ⚠️

- CDN: `a0.muscache.com/im/pictures/<...>.jpg?im_w=<width>`
- `im_w=` caller-controlled: 320/720/1200/1440. Listing page embeds a JSON blob
  (`"pictures"` array) in initial HTML. Headless render usually required.

## Expedia / Hotels.com / Vrbo ⚠️

- CDN: `images.trvl-media.com/lodging/<...>/<id>.jpg` with `?rw=<width>&rh=...` params.
- Same harvest pattern; gallery JSON in initial page state.

## General recipe for an unlisted OTA

1. Render page headless, dump `outerHTML`.
2. Find the image CDN host: look at any visible photo's URL.
3. Regex-harvest all URLs on that host; identify the per-photo unique id segment and any
   required auth/hash params (keep them) vs size params (maximize them).
4. Download in parallel from the CDN with a browser UA (CDNs rarely bot-wall).
5. Verify count against what the listing claims ("N photos" badge) and report both numbers.

## Anti-patterns

- Plain `curl` on OTA pages: bot-walled, returns a stub. Always render headless first.
- Screenshotting galleries: lossy, slow, no provenance. The full-res originals are in the DOM.
- Re-pulling into an already-triaged QA batch: create a new batch instead, verdicts are
  keyed by item id and the human's work must survive.
