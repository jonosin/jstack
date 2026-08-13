# Per-backend capability table (pre-flight validation)

> Read this BEFORE the first submit of any generation. Validate `model` + `duration` +
> `resolution` (+ `aspect_ratio` where noted) against the row for the chosen engine. If the
> requested combination is not in the row, **fail fast and tell the user the allowed values** —
> never let a raw backend/argparse error (`INVALID_ARGUMENT`, `ret:1201`, etc.) be the first
> thing the human sees.

## Veo on Vertex (backend: `references/veo-vertex-backend.md`)

| Model | Allowed duration (s) | Allowed resolution | Aspect ratio | Notes |
|---|---|---|---|---|
| `veo-3.1-generate-001` (standard) | 4, 6, 8 | 720p, 1080p | 9:16, 16:9 | native audio on by default |
| `veo-3.1-fast-generate-001` (fast) | 4, 6, 8 (min ~4s — 3s is rejected) | 720p, 1080p | 9:16, 16:9 | default iterate tier |

## Topview (backend: `references/topview-backend.md`)

| Engine | Allowed resolution | Duration | Aspect ratio | Notes |
|---|---|---|---|---|
| Vidu Q3 Pro (i2v) | subset of `{480,540,720,768,1080,2160}` — check `list-models` | per `list-models` | takes `--aspect-ratio` | single-image i2v |
| Seedance (1.0/1.5/2.0, i2v) | subset of `{480,540,720,768,1080,2160}` — check `list-models` | per `list-models` (typ. 4–15s) | derives from image — `--aspect-ratio` auto-stripped | six-block prompt |
| Kling (O3/V3, i2v) | subset of `{480,540,720,768,1080,2160}` — check `list-models` | per `list-models` | derives from image — `--aspect-ratio` auto-stripped | i2v; prompt cap 2500 chars |
| Kling R2V / t2v models (Kling R2V, Sora, Vidu t2v) | per `list-models` | per `list-models` | takes `--aspect-ratio` | reference-to-video / text-to-video |

**Topview's exact allowed set is model-dependent and can change** — `list-models --type i2v` is
the source of truth per engine; treat this table as the shape of the check, not a frozen value
list. The CLI itself blocks an out-of-set value pre-submit (see `topview-backend.md` "Key guards").

## Pre-flight validation procedure

1. Resolve the backend + model from the user's request (Backend-selection rule in `SKILL.md`).
2. Look up the model's row here (Topview: confirm/refresh via `list-models` first).
3. Check `duration` and `resolution` (and `aspect_ratio` where the row takes one) are IN the
   allowed set.
4. If not: stop before any billed call, tell the user the allowed values from this table, and ask
   them to pick one — do not submit and let the backend reject it.
5. If yes: proceed to Universal Rule 4 (estimate cost, confirm, submit).
