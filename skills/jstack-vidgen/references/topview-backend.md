# Backend: Topview

Adapter/pointer for the **Topview** video backend. This is NOT a copy of the Topview skill —
it routes to it. Topview owns its mechanical guards; `jstack-vidgen` owns the universal rules.

## Where it lives

- Skill: `topview-skill` at `~/builds/topview-skill/` (read its `SKILL.md` for full detail).
- Script: `~/builds/topview-skill/scripts/video_gen.py` (subcommands: `list-models`,
  `estimate-cost`, `run`, `submit`, `query`).
- **Run via the bundled venv** (homebrew python3 is broken on this machine):
  ```bash
  ~/builds/topview-skill/.venv/bin/python ~/builds/topview-skill/scripts/video_gen.py <subcmd> ...
  ```

## Engines that live here

Non-Google engines, credit-based pricing:

| Engine | Notes |
|---|---|
| **Vidu Q3 Pro** | single-image i2v; takes `--aspect-ratio` |
| **Seedance** (2.0 = "Standard" / 1.5 Pro / 1.0 Pro Fast) | six-block prompt craft |
| **Kling** (O3 / V3) | 9-field director formula; native audio on V3 |

(Topview also exposes Sora 2, Veo 3.1, wan2.7 etc. via its catalog, but for Veo prefer the
**Veo-on-Vertex** backend when the user wants GCP credits — see the backend-selection rule in
`SKILL.md`.)

## Vidgen-relevant flow (i2v from a single still)

```bash
PY="~/builds/topview-skill/.venv/bin/python ~/builds/topview-skill/scripts/video_gen.py"

# 1. See models + per-model param constraints
$PY list-models --type i2v

# 2. Estimate credits BEFORE submit (cost driver: model × resolution × duration × count × sound)
$PY estimate-cost --model "<m>" --resolution <r> --duration <d> --count 1 [--sound on|off]

# 3. Submit + poll to completion (single-image i2v = --first-frame only, NO --end-frame)
$PY run --type i2v --model "<m>" --prompt "..." \
    --first-frame <still> --aspect-ratio "9:16" --resolution <r> --duration <d> \
    --count 1 --output-dir <dir> --output-name <stem>

# 4. Re-retrieve a timed-out / earlier task
$PY query --type i2v --task-id <taskId> --output-dir <dir>
```

`run` submits and polls automatically; downloads are named by `taskId` (`<taskId>.mp4`) unless
`--output-name` overrides. Use `query` only to resume a timed-out `run` (same `--type`).

## Key guards (Topview enforces; know them anyway)

- **Charges on SUBMIT.** Credits are spent at submit; refund only if the task itself fails.
  → always `estimate-cost` and confirm `duration`+`resolution` before the first submit.
- **Kling prompt cap = 2500 chars.** Over-cap → API `ret:1201`. CLI blocks and says how much to cut.
  Trim prose, not director fields.
- **`--aspect-ratio` auto-strip on image-derived models.** Kling i2v, Seedance i2v, MiniMax, Wan
  derive aspect from the image — passing `--aspect-ratio` would 400 (`[4000] does not support
  aspectRatio`). CLI auto-strips with a notice. t2v / Reference-to-Video models (Kling R2V, Veo,
  Sora, Vidu) DO take it.
- **Single-image i2v uses `--first-frame` ONLY** — no `--end-frame`.
- **Dup first+end frame is RETIRED** — same still as both frames yields micro-motion only
  ("slideshow"). For a single still use a single-image i2v engine (Vidu Q3 Pro / Seedance 1.0 Pro)
  or Kling R2V. First+end frame is ONLY for genuinely DISTINCT frames. (CLI warns, non-blocking.)
- **resolution / duration must be in the model's set** — check `list-models` first; CLI blocks
  an out-of-set value pre-submit.

## Resolution flags

`--resolution` accepts `{480,540,720,768,1080,2160}` (model-dependent — `list-models` shows the
allowed set per model). `--count` is 1–4.
