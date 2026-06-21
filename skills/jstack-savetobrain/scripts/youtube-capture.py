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


def resolve_python() -> str:
    """Interpreter used for the transcript fetch subprocess.

    The ambient `python3` may be broken (e.g. a Homebrew/uv 3.14 with a busted
    pyexpat) or lack `youtube-transcript-api`. Prefer, in order:
      1. $YT_CAPTURE_PYTHON (explicit override)
      2. the dedicated capture venv at ~/.jstack/venvs/youtube
      3. this process's own interpreter
    """
    env = os.environ.get("YT_CAPTURE_PYTHON")
    if env and os.path.isfile(env):
        return env
    venv = os.path.expanduser("~/.jstack/venvs/youtube/bin/python")
    if os.path.isfile(venv):
        return venv
    return sys.executable


PYTHON = resolve_python()


def _fetch_cmd(video_id: str) -> list:
    """Command that runs the (unmodified) Hermes fetch script under a forced-IPv4
    bootstrap. The IPv4 fix lives HERE — in this versioned repo — not in the fetch
    script (which is outside version control): on networks where IPv6 is
    blackholed, requests/urllib3 connect to the IPv6 address YouTube resolves
    first and hang forever with no Happy-Eyeballs fallback. Pinning AF_INET in the
    child process before any network call makes the fetch deterministic.
    """
    bootstrap = (
        "import socket\n"
        "try:\n"
        "    import urllib3.util.connection as _c\n"
        "    _c.allowed_gai_family = lambda: socket.AF_INET\n"
        "except Exception:\n"
        "    pass\n"
        "import runpy, sys\n"
        f"sys.argv = ['fetch_transcript', {video_id!r}]\n"
        f"runpy.run_path({FETCH_SCRIPT!r}, run_name='__main__')\n"
    )
    return [PYTHON, "-c", bootstrap]

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
        _fetch_cmd(video_id),
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        # Try installing dependency into the resolved interpreter and retry once
        subprocess.run(
            [PYTHON, "-m", "pip", "install", "youtube-transcript-api", "-q"],
            capture_output=True,
        )
        result = subprocess.run(
            _fetch_cmd(video_id),
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            sys.exit(f"Transcript fetch failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def fetch_metadata(video_id: str) -> dict:
    """Get title, channel, date, duration via yt-dlp."""
    result = subprocess.run(
        ["yt-dlp", "--force-ipv4",
         "--print", "%(title)s", "--print", "%(channel)s",
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

    # Remove common filler words (any case, optional trailing comma + space):
    # catches sentence-initial "Uh ..." and comma-trailed "um, ..." that the old
    # lowercase-only \s+ form left behind.
    text = re.sub(r"\b(uh|um)\b,?\s*", "", text, flags=re.IGNORECASE)

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


def split_body(clip_text: str):
    """Return (head, body) where head = frontmatter+title block, body = transcript prose.
    Body begins after the 'Collected: ...' header line + blank line."""
    marker = re.search(r"^Collected: .*\n\n", clip_text, flags=re.MULTILINE)
    if marker:
        cut = marker.end()
        return clip_text[:cut], clip_text[cut:]
    return "", clip_text


def segment_offsets(body: str, target_segments: int = 60):
    """Group sentences into ~even windows; return [{i, offset, preview}].
    Coarse on purpose: ~40-60 candidate boundaries is plenty even for a 3h pod,
    so the scaffold the agent reads stays a few KB regardless of body size."""
    # sentence starts (after . ? ! followed by space + capital)
    starts = [0] + [m.start() for m in re.finditer(r"(?<=[.?!])\s+(?=[A-Z0-9\"'])", body)]
    if len(starts) <= target_segments:
        bounds = starts
    else:
        step = len(starts) / target_segments
        bounds = [starts[int(k * step)] for k in range(target_segments)]
        bounds = sorted(set(bounds))
    SPONSOR_RE = r"\b(sponsor|brought to you by|thank our sponsor|use code|go to \w+\.com|today'?s episode is brought)\b"
    QA_RE = r"\b(question from|audience question|q&a|let'?s take.{0,12}questions|someone asks)\b"

    def snap(cue_pos):
        """Move the boundary to the start of the sentence holding the cue, so the
        inserted heading caps the actual sponsor/Q&A read, not a paragraph before it."""
        prior = [s for s in starts if s <= cue_pos]
        return prior[-1] if prior else cue_pos

    segs = []
    for k, off in enumerate(bounds):
        # scan the FULL window (this boundary -> next) for cue phrases the 12-word
        # preview would miss — esp. mid-stream sponsor reads. The scan is free
        # (runs in-script over the body); only a tiny flag enters the scaffold.
        nxt = bounds[k + 1] if k + 1 < len(bounds) else len(body)
        window = body[off:nxt]
        cue = None
        m = re.search(SPONSOR_RE, window, re.I)
        if m:
            cue = "sponsor"
        else:
            m = re.search(QA_RE, window, re.I)
            if m:
                cue = "qa"
        if cue:  # snap boundary to the cue sentence's start
            off = snap(off + m.start())
        seg = {"i": k, "offset": off, "preview": " ".join(body[off:off + 120].split()[:12])}
        if cue:
            seg["cue"] = cue
        segs.append(seg)
    return segs


def cmd_scaffold(clip_path: str):
    """Emit a compact JSON outline of a clip's body so Phase-2 can pick section
    boundaries WITHOUT loading the full transcript into context."""
    text = open(clip_path).read()
    _, body = split_body(text)
    segs = segment_offsets(body)
    out = {"body_chars": len(body), "n_segments": len(segs), "segments": segs}
    print(json.dumps(out, ensure_ascii=False))


def cmd_insert(clip_path: str, picks_path: str):
    """Insert '## heading' lines at picked segment byte-offsets. Body otherwise
    untouched -> body integrity is guaranteed by construction (no LLM rewrite)."""
    text = open(clip_path).read()
    head, body = split_body(text)
    picks = json.loads(open(picks_path).read()) if os.path.isfile(picks_path) else json.loads(picks_path)
    segs = {s["i"]: s["offset"] for s in segment_offsets(body)}
    # resolve each pick to a body offset, sort descending so earlier offsets stay valid
    items = sorted(picks, key=lambda p: segs.get(p["i"], 0), reverse=True)
    new_body = body
    for p in items:
        off = segs.get(p["i"])
        if off is None:
            continue
        heading = p["heading"].strip().lstrip("#").strip()
        # cleaned body is a single newline-free paragraph; the heading must start
        # its own line, so add a leading break unless we're at the very start.
        lead = "" if off == 0 else "\n\n"
        insertion = f"{lead}## {heading}\n\n"
        # snap to the start of the sentence at off (already a boundary)
        new_body = new_body[:off] + insertion + new_body[off:]
    with open(clip_path, "w") as f:
        f.write(head + new_body)
    print(clip_path)


def main():
    # Subcommand dispatch (keeps the documented `... <url>` call working as default).
    if len(sys.argv) > 1 and sys.argv[1] in ("scaffold", "insert"):
        if sys.argv[1] == "scaffold":
            cmd_scaffold(sys.argv[2])
        else:
            cmd_insert(sys.argv[2], sys.argv[3])
        return
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
