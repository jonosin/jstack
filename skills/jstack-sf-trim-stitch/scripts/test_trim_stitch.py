#!/usr/bin/env python3
"""Replay trim_stitch.py against frozen fixture clips.

Verifies the two deterministic bookends produce output of the expected SHAPE
(not just non-crash): filmstrip dimensions, and stitched reel duration +
resolution-normalization. Run: python3 scripts/test_trim_stitch.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
FX = os.path.join(SKILL, "references", "fixtures")
SCRIPT = os.path.join(HERE, "trim_stitch.py")
CLIP_A = os.path.join(FX, "clipA-716x1284-3s.mp4")  # 3s, odd 716x1284
CLIP_B = os.path.join(FX, "clipB-720x1280-2s.mp4")  # 2s, 720x1280


def run(*args):
    p = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)
    assert p.returncode == 0, "exit %d\nSTDOUT:%s\nSTDERR:%s" % (p.returncode, p.stdout, p.stderr)
    return p.stdout


def probe(path, entries):
    """entries: a valid ffprobe -show_entries spec, e.g. 'stream=width,height'
    or 'format=duration'. Returns the csv stdout as a list of fields."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", entries, "-of", "csv=p=0", path],
        capture_output=True, text=True,
    ).stdout.strip()
    return out.split(",")


def test_filmstrip():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "strip.png")
        run("filmstrip", "--clip", CLIP_A, "--frames", "6", "--width", "220", "--out", out)
        assert os.path.isfile(out), "filmstrip PNG not written"
        w, h = probe(out, "stream=width,height")
        # 6 frames * 220px wide, tiled horizontally -> ~1320 wide (allow scaler rounding)
        assert abs(int(w) - 1320) <= 12, "filmstrip width %s, expected ~1320" % w
        assert int(h) > 0, "filmstrip height not positive"
    print("  [ok] filmstrip: 6x220 frames -> %sx%s PNG" % (w, h))


def test_stitch_spec():
    with tempfile.TemporaryDirectory() as d:
        spec_path = os.path.join(d, "spec.json")
        out = os.path.join(d, "reel.mp4")
        spec = {
            "output": {"width": 720, "height": 1280, "fps": 24, "crf": 30},
            "beats": [
                {"clip": CLIP_A, "start": 0.0, "end": 1.5},  # trim 3s -> 1.5s window
                {"clip": CLIP_B},                              # whole 2s clip
            ],
        }
        with open(spec_path, "w") as fh:
            json.dump(spec, fh)
        run("stitch", "--spec", spec_path, "--out", out)
        assert os.path.isfile(out), "stitched reel not written"
        dur = float(probe(out, "format=duration")[0])
        # 1.5 + 2.0 = 3.5s expected
        assert abs(dur - 3.5) <= 0.3, "reel duration %.3f, expected ~3.5" % dur
        w, h = probe(out, "stream=width,height")
        # odd 716x1284 input must be normalized to the 720x1280 canvas
        assert (int(w), int(h)) == (720, 1280), "reel not normalized: %sx%s" % (w, h)
    print("  [ok] stitch: trim+normalize+concat -> %.2fs @ %sx%s" % (dur, w, h))


def test_stitch_inline():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "reel2.mp4")
        run("stitch", "--beat", "%s:0:1.0" % CLIP_A, "--beat", CLIP_B, "--out", out)
        dur = float(probe(out, "format=duration")[0])
        assert abs(dur - 3.0) <= 0.3, "inline reel duration %.3f, expected ~3.0" % dur
    print("  [ok] stitch inline --beat: -> %.2fs" % dur)


if __name__ == "__main__":
    assert os.path.isfile(CLIP_A) and os.path.isfile(CLIP_B), "fixtures missing"
    test_filmstrip()
    test_stitch_spec()
    test_stitch_inline()
    print("ALL PASS")
