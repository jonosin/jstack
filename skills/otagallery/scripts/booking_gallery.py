#!/usr/bin/env python3
"""Extract + download a Booking.com property gallery at max resolution.

Input: an HTML file (the rendered property page — fetch it with a headless
browser first; plain curl is bot-walled) OR a JSON map file {photo_id: k_hash}.
Output: <outdir>/<photo_id>.jpg for every unique gallery photo + manifest line
        on stdout per file. CDN (cf.bstatic.com) is NOT bot-walled — downloads
        run anonymously and in parallel.

Usage:
  booking_gallery.py --html page.html --outdir /tmp/gallery
  booking_gallery.py --map idmap.json --outdir /tmp/gallery
  booking_gallery.py --html page.html --outdir /tmp/gallery --size max1600
"""
import argparse, concurrent.futures, json, os, re, sys, urllib.request

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')


def extract_map(html: str) -> dict:
    """cf.bstatic.com/xdata/images/hotel/<size>/<id>.jpg?k=<hash> -> {id: k}"""
    urls = re.findall(r'cf\.bstatic\.com/xdata/images/hotel/[^"\'\\ )]+', html)
    out = {}
    for u in urls:
        mid = re.search(r'/(\d+)\.jpg', u)
        mk = re.search(r'[?&]k=([0-9a-f]+)', u)
        if mid and mk:
            out.setdefault(mid.group(1), mk.group(1))
    return out


def download(pid: str, k: str, outdir: str, size: str):
    url = f'https://cf.bstatic.com/xdata/images/hotel/{size}/{pid}.jpg?k={k}&o='
    path = os.path.join(outdir, f'{pid}.jpg')
    if os.path.exists(path) and os.path.getsize(path) > 10_000:
        return pid, 'cached'
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r, open(path, 'wb') as f:
            f.write(r.read())
        return pid, os.path.getsize(path)
    except Exception as e:  # noqa: BLE001
        return pid, f'FAIL {e}'


def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--html', help='rendered property-page HTML file')
    src.add_argument('--map', help='JSON file {photo_id: k_hash}')
    ap.add_argument('--outdir', required=True)
    ap.add_argument('--size', default='max1600',
                    help='bstatic size segment (max1600, max1280x900, max1024x768)')
    ap.add_argument('--workers', type=int, default=8)
    a = ap.parse_args()

    if a.html:
        idmap = extract_map(open(a.html, encoding='utf-8', errors='ignore').read())
    else:
        idmap = json.load(open(a.map))
    if not idmap:
        sys.exit('no bstatic photo URLs found — page not fully rendered? '
                 'Fetch with a headless browser, not curl.')

    os.makedirs(a.outdir, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(a.workers) as ex:
        results = list(ex.map(lambda it: download(*it, a.outdir, a.size), idmap.items()))
    fails = [r for r in results if isinstance(r[1], str) and r[1].startswith('FAIL')]
    for pid, st in results:
        print(f'{pid}.jpg\t{st}')
    print(f'\n{len(results) - len(fails)}/{len(results)} downloaded -> {a.outdir}', file=sys.stderr)
    if fails:
        sys.exit(1)


if __name__ == '__main__':
    main()
