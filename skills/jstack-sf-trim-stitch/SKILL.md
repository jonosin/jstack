---
name: jstack-sf-trim-stitch
description: Assemble a StayFrame reel from per-beat clips — extract filmstrips, pick trim windows by eye, then trim+normalize+concat into one reel. Use when Jono says /jstack-sf-trim-stitch, "stitch the reel", "assemble the beats", "trim and join these clips", "cut these down and stitch them", or after per-beat clips are rendered (mixed engines/durations/resolutions) and need to become one continuous reel. Covers the visual trim pass (where to cut each clip, plus a red-line check) and the deterministic ffmpeg assembly. NOT for generating clips (that is /jstack-vidgen) nor promoting method to canon (/jstack-sf-learn).
---

# jstack-sf-trim-stitch — reel assembly (filmstrip → trim pick → stitch)

The **assemble** step of the StayFrame pipeline (`playbook/index.md §1`). Turns N per-beat clips —
often mixed engines, durations, and resolutions — into one continuous reel. Two deterministic ffmpeg
bookends wrap one agent-judgment seam:

```
clips ──filmstrip──▶ PNG strips ──[AGENT LOOKS]──▶ trim spec ──stitch──▶ reel.mp4
        (script)                   judgment+red-line          (script)
```

`scripts/trim_stitch.py` (ffmpeg/ffprobe only, no deps) owns the deterministic ends. The agent owns
the look in the middle — the script never decides where to cut.

## 1. Filmstrip every clip (deterministic)
One horizontal strip of N evenly-spaced frames per clip (left→right = time):

```bash
python3 scripts/trim_stitch.py filmstrip-batch \
  --clips /path/beat-1.mp4 /path/beat-2.mp4 ... --frames 6 --out-dir /tmp/trim-pass
# single clip: filmstrip --clip <mp4> --frames 6 --width 220 --out strip.png
```
Use more frames (8–12) for long or reused clips where drift is likely; 6 is plenty for a ~3s clip.

## 2. Visual trim pass (AGENT judgment — the seam)
Read each strip image. For every beat decide:
- **trim window** `start`/`end` (seconds) — the cleanest sub-window. Off-length reused clips (e.g. an
  8s establish or a 4s interior) get cut to match the reel's rhythm; native-length clips usually pass whole.
- **red-line check** (StayFrame `playbook/produce/quality-gate.md`): cut any window that invents
  people / structures / amenities / sea, morphs trees or geometry, or drifts off the real property. A
  camera that wanders late in a long reused clip is the classic offender — trim before the drift starts.

Write the decisions into a stitch spec (`references/stitch-spec.example.json` is the template):
```json
{ "output": {"width":720,"height":1280,"fps":24,"crf":18},
  "beats": [ {"clip":"/abs/beat-1.mp4","start":0.0,"end":2.6},
             {"clip":"/abs/beat-2.mp4"} ] }
```
Omit `start`→0.0; omit `end`→clip duration. Beats concat in array order.

## 3. Stitch (deterministic)
```bash
python3 scripts/trim_stitch.py stitch --spec spec.json --out reel.mp4
# quick/no-spec: stitch --beat /path/beat-1.mp4:0:2.6 --beat /path/beat-2.mp4 --out reel.mp4
```
Per beat it does `trim → setpts → scale W:H → setsar=1 → fps`, then `concat`, single libx264 encode
(`yuv420p`, crf 18, `-an`). One encode = no double-loss. **Video-only by design** — the ambient/audio
bed is a separate edit step. Mismatched input resolutions are normalized to the output canvas.

## Where it sits
- Upstream: `/jstack-vidgen` renders the per-beat clips. This skill only assembles.
- After stitching: present the reel for **GATE B** (the human's call). Do not auto-promote.
- If the reel passed and proved a method: `/jstack-sf-learn` writes canon.

## Test
`python3 scripts/test_trim_stitch.py` replays both bookends against the frozen fixtures in
`references/fixtures/` (asserts filmstrip dimensions, and that stitch trims + normalizes a 716×1284
clip onto a 720×1280 canvas at the expected duration).
