#!/usr/bin/env python3
"""OPTIONAL perceptual dedupe of a new gallery dir against an existing dir.

Default is NO dedupe (the user re-triages by hand). Use only when asked.
Run via uv (system python lacks PIL):  uv run --with pillow dedupe_dhash.py ...

dHash 64-bit; hamming <= --thresh (default 6) = same photo. Verified on the
Serenity Sands galleries 2026-06-12: all true dupes landed at distance 0-2
across two different CDNs (imgix vs bstatic); zero borderline cases.

Usage:
  uv run --with pillow dedupe_dhash.py --new /tmp/booking --existing qa/.../media
Output: JSON {"new": [...files unique to --new...], "dupes": {file: match}}
"""
import argparse, json, os
from PIL import Image


def dhash(path, size=8):
    img = Image.open(path).convert('L').resize((size + 1, size), Image.LANCZOS)
    px = list(img.getdata())
    rows = [px[i * (size + 1):(i + 1) * (size + 1)] for i in range(size)]
    bits = ''.join('1' if r[j] > r[j + 1] else '0' for r in rows for j in range(size))
    return int(bits, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--new', required=True)
    ap.add_argument('--existing', required=True)
    ap.add_argument('--thresh', type=int, default=6)
    a = ap.parse_args()

    exts = ('.jpg', '.jpeg', '.png', '.webp')
    old = {f: dhash(os.path.join(a.existing, f))
           for f in sorted(os.listdir(a.existing)) if f.lower().endswith(exts)}
    new_files, dupes = [], {}
    for f in sorted(os.listdir(a.new)):
        if not f.lower().endswith(exts):
            continue
        h = dhash(os.path.join(a.new, f))
        match = min(old.items(), key=lambda e: bin(h ^ e[1]).count('1'), default=None)
        if match and bin(h ^ match[1]).count('1') <= a.thresh:
            dupes[f] = match[0]
        else:
            new_files.append(f)
    print(json.dumps({'new': new_files, 'dupes': dupes}, indent=1))


if __name__ == '__main__':
    main()
