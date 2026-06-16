#!/usr/bin/env python3
"""Deterministic trim+stitch bookends for the StayFrame reel assembly step.

Two deterministic operations, no model judgment inside:
  filmstrip        — extract N evenly-spaced frames from ONE clip, tiled L->R into one PNG
  filmstrip-batch  — same, for many clips at once (one <stem>-strip.png per clip)
  stitch           — trim + resolution-normalize + concat a list of beats into one reel

The judgment seam (which trim window per beat, red-line check) is the agent's job at
runtime: it looks at the filmstrips, then writes a stitch spec. This script never decides.

Backend: ffmpeg/ffprobe only. No third-party Python deps.

Stitch spec (JSON) — the agent's vision output, fed to `stitch --spec`:
  {
    "output": {"width": 720, "height": 1280, "fps": 24, "crf": 18},   // all optional
    "beats": [
      {"clip": "/abs/beat-1.mp4", "start": 0.0, "end": 2.6},          // trim window
      {"clip": "/abs/beat-2.mp4"},                                     // whole clip
      ...
    ]
  }
Omit start -> 0.0; omit end -> clip duration. Beats concat in array order. Video-only
output (the ambient/audio bed is a separate edit step).
"""
import argparse
import json
import os
import subprocess
import sys

DEFAULTS = {"width": 720, "height": 1280, "fps": 24, "crf": 18}


def _run(cmd):
    """Run a command, raising RuntimeError with stderr on non-zero exit."""
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(
            "command failed (%d): %s\n%s" % (p.returncode, " ".join(cmd), p.stderr.strip())
        )
    return p.stdout


def probe_duration(clip):
    """Return float duration (seconds) of a media file via ffprobe."""
    out = _run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", clip,
    ]).strip()
    try:
        return float(out)
    except ValueError:
        raise RuntimeError("could not read duration of %s (got %r)" % (clip, out))


def cmd_filmstrip(args):
    """Tile N evenly-spaced frames of one clip into a single horizontal PNG."""
    if not os.path.isfile(args.clip):
        raise RuntimeError("clip not found: %s" % args.clip)
    if args.frames < 1:
        raise RuntimeError("--frames must be >= 1")
    dur = probe_duration(args.clip)
    fps = args.frames / dur if dur > 0 else 1.0
    vf = "fps=%.6f,scale=%d:-1,tile=%dx1" % (fps, args.width, args.frames)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    _run(["ffmpeg", "-y", "-i", args.clip, "-vf", vf, "-frames:v", "1", args.out])
    print(args.out)
    return 0


def cmd_filmstrip_batch(args):
    """One filmstrip per clip, named <stem>-strip.png in --out-dir."""
    os.makedirs(args.out_dir, exist_ok=True)
    written = []
    for clip in args.clips:
        stem = os.path.splitext(os.path.basename(clip))[0]
        out = os.path.join(args.out_dir, "%s-strip.png" % stem)
        sub = argparse.Namespace(clip=clip, frames=args.frames, width=args.width, out=out)
        cmd_filmstrip(sub)
        written.append(out)
    print("\n".join(written))
    return 0


def _load_beats(args):
    """Resolve beats + output config from --spec JSON or repeated --beat tokens."""
    out_cfg = dict(DEFAULTS)
    if args.spec:
        with open(args.spec) as fh:
            spec = json.load(fh)
        out_cfg.update(spec.get("output", {}))
        beats = spec.get("beats", [])
    else:
        beats = []
        for tok in (args.beat or []):
            # path[:start[:end]]  (start/end are seconds)
            parts = tok.split(":")
            b = {"clip": parts[0]}
            if len(parts) > 1 and parts[1] != "":
                b["start"] = float(parts[1])
            if len(parts) > 2 and parts[2] != "":
                b["end"] = float(parts[2])
            beats.append(b)
    if not beats:
        raise RuntimeError("no beats: pass --spec <json> or one or more --beat path[:start:end]")
    return beats, out_cfg


def cmd_stitch(args):
    """Trim each beat to its window, normalize to one canvas, concat, encode video-only."""
    beats, out_cfg = _load_beats(args)
    w, h = int(out_cfg["width"]), int(out_cfg["height"])
    fps, crf = float(out_cfg["fps"]), int(out_cfg["crf"])

    inputs, filters, labels = [], [], []
    for i, beat in enumerate(beats):
        clip = beat["clip"]
        if not os.path.isfile(clip):
            raise RuntimeError("beat %d clip not found: %s" % (i, clip))
        start = float(beat.get("start", 0.0))
        end = beat.get("end")
        if end is None:
            end = probe_duration(clip)
        end = float(end)
        if end <= start:
            raise RuntimeError("beat %d: end (%.3f) must exceed start (%.3f)" % (i, end, start))
        inputs += ["-i", clip]
        filters.append(
            "[%d:v]trim=%.3f:%.3f,setpts=PTS-STARTPTS,scale=%d:%d,setsar=1,fps=%g[v%d]"
            % (i, start, end, w, h, fps, i)
        )
        labels.append("[v%d]" % i)

    filter_complex = ";".join(filters) + ";" + "".join(labels) + \
        "concat=n=%d:v=1:a=0[outv]" % len(beats)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", str(crf), "-preset", args.preset, "-an", args.out,
    ]
    _run(cmd)
    total = probe_duration(args.out)
    print("%s  (%d beats, %.2fs, %dx%d @ %gfps)" % (args.out, len(beats), total, w, h, fps))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="StayFrame reel trim+stitch bookends (ffmpeg).")
    sub = p.add_subparsers(dest="op", required=True)

    f = sub.add_parser("filmstrip", help="N evenly-spaced frames of one clip -> one PNG")
    f.add_argument("--clip", required=True)
    f.add_argument("--frames", type=int, default=6)
    f.add_argument("--width", type=int, default=220, help="per-frame width (px)")
    f.add_argument("--out", required=True)
    f.set_defaults(func=cmd_filmstrip)

    fb = sub.add_parser("filmstrip-batch", help="one filmstrip per clip into --out-dir")
    fb.add_argument("--clips", nargs="+", required=True)
    fb.add_argument("--frames", type=int, default=6)
    fb.add_argument("--width", type=int, default=220)
    fb.add_argument("--out-dir", required=True)
    fb.set_defaults(func=cmd_filmstrip_batch)

    s = sub.add_parser("stitch", help="trim+normalize+concat beats into one reel")
    s.add_argument("--spec", help="JSON stitch spec (see module docstring)")
    s.add_argument("--beat", action="append", help="inline beat path[:start:end] (repeatable)")
    s.add_argument("--out", required=True)
    s.add_argument("--preset", default="medium")
    s.set_defaults(func=cmd_stitch)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except RuntimeError as e:
        print("trim_stitch: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
