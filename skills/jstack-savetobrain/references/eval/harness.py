#!/usr/bin/env python3
"""Skilltune harness for jstack-savetobrain youtube route.
Prepares clip fixtures and grades machine assertions per probe.

Usage:
  python3 harness.py prep <version>        # build work/<version>/ clip files
  python3 harness.py scaffold-bytes <version> <probe>   # efficiency input size
  python3 harness.py grade-sections <version> <probe> <inserted_clip>  # JSON verdict
"""
import sys, os, re, json, importlib.util
from pathlib import Path

SB = Path(__file__).resolve().parent
FIX = SB / "fixtures"


def _jstack_cfg(key: str, default: str = "") -> str:
    """Resolve a config value: env var > ~/.jstack/config.env > default."""
    val = os.environ.get(key)
    if val:
        return val
    cfg = Path.home() / ".jstack" / "config.env"
    if cfg.exists():
        for line in cfg.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == key:
                return v.strip().strip('"').strip("'")
    return default


# Real ~200KB transcript clip used for the E5 efficiency probe. Resolve via
# env var / ~/.jstack/config.env (SAVETOBRAIN_EVAL_ANCHOR), falling back to
# the conventional path under SECOND_BRAIN_PATH so this still works out of
# the box on any machine with the second brain checked out.
_second_brain = Path(_jstack_cfg("SECOND_BRAIN_PATH", "~/second-brain")).expanduser()
_default_anchor = _second_brain / "raw/clips/2026-06-20-huberman-peptides-bakri-readable-transcript.md"
ANCHOR = Path(_jstack_cfg("SAVETOBRAIN_EVAL_ANCHOR", str(_default_anchor))).expanduser()

def load_script(version):
    p = SB / "snapshots" / version / "scripts" / "youtube-capture.py"
    spec = importlib.util.spec_from_file_location(f"yc_{version}", p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def synth_clip(yc, title, raw_text):
    cleaned = yc.clean_transcript(raw_text)
    head = (f'---\ntitle: "{title}"\nsource: "https://youtu.be/TESTID00000"\n'
            f'channel: "Test Channel"\nvideo_id: "TESTID00000"\nduration: "0:05:00"\n'
            f'published: 2026-06-01\ncollected: 2026-06-21\ntags: [youtube, transcript, readable]\n---\n\n'
            f'# {title}\n\nSource: https://youtu.be/TESTID00000\nChannel: Test Channel\n'
            f'Video ID: TESTID00000\nDuration: 0:05:00\nCollected: 2026-06-21\n\n')
    return head + cleaned + "\n"

def anchor_unsectioned():
    """The real 197KB clip with its existing '## ' headings stripped -> a sectionless body."""
    t = ANCHOR.read_text()
    return re.sub(r"^## .*\n\n?", "", t, flags=re.MULTILINE)

PROBES = {
    "E1": ("short-clip-raw.txt", "Sleep Basics"),
    "E4": ("short-clip-raw.txt", "Sleep Basics"),
    "E6": ("flat-monologue-raw.txt", "On Consistency"),
    "E7": ("medium-sponsored-raw.txt", "Cold Exposure Deep Dive"),
    "E8": ("medium-sponsored-raw.txt", "Cold Exposure Deep Dive"),
    "E5": ("__anchor__", "Peptides"),
}

def clip_path(version, probe): return SB / "work" / version / f"{probe}.md"

def cmd_prep(version):
    yc = load_script(version)
    outd = SB / "work" / version; outd.mkdir(parents=True, exist_ok=True)
    for probe,(fix,title) in PROBES.items():
        if fix == "__anchor__":
            clip = anchor_unsectioned()
        else:
            clip = synth_clip(yc, title, (FIX/fix).read_text())
        clip_path(version, probe).write_text(clip)
    print(f"prepped {len(PROBES)} clips in {outd}")

def body_of(version, clip_text):
    yc = load_script(version)
    if hasattr(yc, "split_body"):
        return yc.split_body(clip_text)[1]
    # v0 has no split_body: body = after the Collected header
    m = re.search(r"^Collected: .*\n\n", clip_text, flags=re.MULTILINE)
    return clip_text[m.end():] if m else clip_text

def cmd_scaffold_bytes(version, probe):
    yc = load_script(version)
    clip = clip_path(version, probe).read_text()
    body = body_of(version, clip)
    if hasattr(yc, "segment_offsets"):
        segs = yc.segment_offsets(body)
        scaffold = json.dumps({"body_chars": len(body), "n_segments": len(segs), "segments": segs}, ensure_ascii=False)
        sb_bytes = len(scaffold.encode())
    else:
        sb_bytes = len(body.encode())  # v0: full re-read
    body_bytes = len(body.encode())
    eff = 1 - min(1, sb_bytes / body_bytes) if body_bytes else 1.0
    print(json.dumps({"scaffold_bytes": sb_bytes, "body_bytes": body_bytes, "efficiency_score": round(eff,4)}))

def cmd_grade_sections(version, probe, inserted):
    text = Path(inserted).read_text()
    headings = re.findall(r"^## (.+)$", text, flags=re.MULTILINE)
    n = len(headings)
    # body integrity: remove heading lines -> compare to original sectionless body
    orig_body = body_of(version, clip_path(version, probe).read_text())
    stripped = re.sub(r"^## .*\n\n?", "", text, flags=re.MULTILINE)
    stripped_body = body_of(version, stripped)
    integrity = re.sub(r"\s+"," ",stripped_body).strip() == re.sub(r"\s+"," ",orig_body).strip()
    checks = {"n_sections": n, "body_integrity": integrity,
              "headings_are_h2": all(text.count(f"## {h}") for h in headings),
              "headings_short": all(len(h.split()) <= 8 for h in headings)}
    # probe-specific bands
    band = {"E4": (2,4), "E5": (10,15), "E6": (0,2), "E7": (3,5), "E8": (1,99)}[probe]
    checks["count_in_band"] = band[0] <= n <= band[1]
    if probe == "E7":
        checks["has_sponsor"] = any(re.search(r"sponsor|eight ?sleep", h, re.I) for h in headings)
        checks["has_qa"] = any(re.search(r"q&a|question", h, re.I) for h in headings)
    bools = [v for v in checks.values() if isinstance(v, bool)]
    checks["assertion_pass_rate"] = round(sum(bools)/len(bools), 3)
    checks["headings"] = headings
    print(json.dumps(checks, ensure_ascii=False))

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "prep": cmd_prep(sys.argv[2])
    elif cmd == "scaffold-bytes": cmd_scaffold_bytes(sys.argv[2], sys.argv[3])
    elif cmd == "grade-sections": cmd_grade_sections(sys.argv[2], sys.argv[3], sys.argv[4])
