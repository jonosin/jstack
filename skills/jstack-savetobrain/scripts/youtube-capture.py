#!/usr/bin/env python3
"""YouTube transcript capture for second brain.
Deterministic: URL in, cleaned readable .md out. One shot, zero decisions.

Usage:
    python3 youtube-capture.py <youtube_url> [--out-dir <path>]

Output:
    raw/clips/YYYY-MM-DD-<slug>-readable-transcript.md
    Prints the absolute path to stdout on success.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# --- Configurable paths ---
FETCH_SCRIPT = os.path.expanduser(
    "~/.hermes/skills/media/youtube-content/scripts/fetch_transcript.py"
)
SECOND_BRAIN = os.path.expanduser(
    os.environ.get("SECOND_BRAIN_PATH", "~/second-brain")
)

# --- ASR / name fixes ---
# Map of common YouTube ASR misspellings → corrections.
# Extend this map when you encounter new patterns.
NAME_FIXES = {
    # General podcast artifacts
    ">>": " ",
    # Huberman-specific (safe no-ops on other content)
    "Ompic": "Ozempic",
    "ombic": "Ozempic",
    "Monaro": "Mounjaro",
    "Bachri": "Bakri",
    "Bacher": "Bakri",
    "Bockery": "Bakri",
    "Norvo": "Novo Nordisk",
    "Novaist": "Novo Nordisk",
    "Lily": "Eli Lilly",
    "teptide": "tirzepatide",
    "retride": "retatrutide",
    "Retroide": "Retatrutide",
    "reetta": "retatrutide",
    "Red True Tide": "Retatrutide",
    "Tresepite": "tirzepatide",
    "Zmpic": "Ozempic",
    "semiglutide": "semaglutide",
    "Semiglutide": "Semaglutide",
    "luraglutide": "liraglutide",
    "dlutide": "dulaglutide",
    "oroplon": "orforglipron",
    "Orupon": "Orforglipron",
    "epithelen": "epitalon",
    "pinealin": "pinealon",
    "Pinealin": "Pinealon",
    "tessamarellin": "tesamorelin",
    "Hila monsters": "Gila monsters",
    "Hansely": "Hans Selye",
    "Soia": "Selye",
}


def extract_video_id(url: str) -> str:
    patterns = [
        r"(?:v=|youtu\.be/|shorts/|embed/|live/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    url = url.strip()
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return url


def fetch_transcript(video_id: str) -> dict:
    """Fetch transcript JSON from the youtube-content helper."""
    result = subprocess.run(
        ["python3", FETCH_SCRIPT, video_id],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        # Try installing dependency and retry once
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "youtube-transcript-api", "-q"],
            capture_output=True,
        )
        result = subprocess.run(
            ["python3", FETCH_SCRIPT, video_id],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            sys.exit(f"Transcript fetch failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def fetch_metadata(video_id: str) -> dict:
    """Get title, channel, date, duration via yt-dlp."""
    result = subprocess.run(
        ["yt-dlp", "--print", "%(title)s", "--print", "%(channel)s",
         "--print", "%(upload_date)s", "--print", "%(duration)s",
         f"https://youtu.be/{video_id}"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        return {"title": video_id, "channel": "Unknown", "upload_date": None, "duration": 0}
    lines = result.stdout.strip().split("\n")
    return {
        "title": lines[0] if len(lines) > 0 else video_id,
        "channel": lines[1] if len(lines) > 1 else "Unknown",
        "upload_date": lines[2] if len(lines) > 2 else None,
        "duration": int(lines[3]) if len(lines) > 3 and lines[3].isdigit() else 0,
    }


def slugify(title: str, max_len: int = 60) -> str:
    """Generate a filesystem-safe slug from a title."""
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    if len(slug) > max_len:
        slug = slug[:max_len].rstrip("-")
    return slug


def format_duration(seconds: int) -> str:
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def clean_transcript(text: str) -> str:
    """Remove podcast artifacts and normalize whitespace."""
    # Remove bracketed non-speech markers
    text = re.sub(r"\[snorts\]\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[clears throat\]\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[music\]\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[laughter\]\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[applause\]\s*", "", text, flags=re.IGNORECASE)

    # Remove segment separators
    text = text.replace(">>", " ")

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove common filler words
    text = re.sub(r"\b(uh|um)\s+", "", text)

    # Apply name/product fixes
    for wrong, right in NAME_FIXES.items():
        text = text.replace(wrong, right)

    # Final whitespace pass
    text = re.sub(r"\s+", " ", text).strip()

    return text


def build_frontmatter(meta: dict, video_id: str, collected: str, slug: str) -> str:
    title = meta["title"].replace('"', "'")
    published = meta.get("upload_date")
    if published and len(published) == 8:
        published = f"{published[:4]}-{published[4:6]}-{published[6:8]}"
    else:
        published = "Unknown"

    duration_str = format_duration(meta["duration"])

    return f"""---
title: "{title}"
source: "https://youtu.be/{video_id}"
channel: "{meta['channel']}"
video_id: "{video_id}"
duration: "{duration_str}"
published: {published}
collected: {collected}
tags: [youtube, transcript, readable]
---

# {title}

Source: https://youtu.be/{video_id}
Channel: {meta['channel']}
Video ID: {video_id}
Duration: {duration_str}
Collected: {collected}

"""


def main():
    parser = argparse.ArgumentParser(description="Capture YouTube transcript for second brain")
    parser.add_argument("url", help="YouTube URL or video ID")
    parser.add_argument("--out-dir", default=None, help="Output directory (default: SECOND_BRAIN/raw/clips/)")
    args = parser.parse_args()

    video_id = extract_video_id(args.url)
    collected = datetime.now().strftime("%Y-%m-%d")

    print(f"Fetching transcript for {video_id}...", file=sys.stderr)

    transcript = fetch_transcript(video_id)
    meta = fetch_metadata(video_id)

    print(f"Title: {meta['title']}", file=sys.stderr)
    print(f"Channel: {meta['channel']}", file=sys.stderr)
    print(f"Duration: {format_duration(meta['duration'])}", file=sys.stderr)

    slug = slugify(meta["title"])
    filename = f"{collected}-{slug}-readable-transcript.md"

    out_dir = Path(args.out_dir) if args.out_dir else Path(SECOND_BRAIN) / "raw" / "clips"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename

    cleaned = clean_transcript(transcript["full_text"])
    frontmatter = build_frontmatter(meta, video_id, collected, slug)

    with open(out_path, "w") as f:
        f.write(frontmatter)
        f.write(cleaned)
        f.write("\n")

    print(f"Saved: {out_path} ({len(cleaned)} chars)", file=sys.stderr)
    print(str(out_path.resolve()))


if __name__ == "__main__":
    main()
