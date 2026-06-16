# Creating new content on the dashboard (deterministic)

Jono interacts with the pipeline **only through the dashboard**. To put new content in front of him —
a new reel, a new format, or a variant — a fresh-session agent **deterministically scaffolds the
page(s)** with `tools/new_reel.py`, formatted per the engine, then fills each beat and tells Jono to
reload. No prompt is hand-shaped from scratch; no workflow is re-derived. This is a **general**
primitive — comparing engines (a bake-off) is just one application of it.

Authoritative dashboard↔agent contract: `~/ventures/stayframe/qa/AGENTS.md` → "Creating new content on
the dashboard (deterministic)". Prompt rules + per-engine formats: `playbook/prompts/reel-prompt-system.md`
+ `playbook/method/reel-deconstruction.md §7`. Engine matrix: `playbook/index.md §2`.

## Procedure

1. **Scaffold** one page per format (all paths under `~/ventures/stayframe/`):
   ```bash
   python3 tools/new_reel.py --client <slug> --reel <reel-slug> --beats <N> --engine "<engine>" \
     [--stills-from <reel-or-stills-dir>] [--experimental]
   ```
   - **`--engine`** selects the clip-prompt **format** (`sf_lint` enforces it): Kling O3/V3 →
     **9-field** director; Veo 3.1 / Vidu Q3 Pro → **single-start** block; Seedance → **six-block**.
     Default `Veo 3.1`.
   - **`--stills-from <reel-or-stills-dir>`** reuses an approved stills set (e.g.
     `renders/v4-bluehour/stills`). The page's beats show those stills; its **clips** resolve from its
     own `render_subdir`. No duplication, no symlinks.
   - **`--experimental`** marks a not-yet-canon clip engine/format (e.g. `Vidu Q3 Pro`): relaxes only
     the engine-matrix lint; the **format guard still applies**.

2. **Fill each beat's skeleton** from `clients/<slug>/brand.md` + the approved still by **invoking the
   craft skills** — `creative-production-skills:kling-3-prompt-director` +
   `creative-production-skills:cinematic-motion-language` (Kling), or the single-start / six-block rules
   in `prompts/reel-prompt-system.md`. The format is already stamped; you supply real content. **Red
   line:** augment the property's REAL look only — no invented people/structures/amenities.

3. **Lint** → must be green: `python3 tools/sf_lint.py`.

4. **Tell Jono** the new page(s) are at http://localhost:7777 (start the server if down:
   `cd ~/builds/stayframe-qa && node server.js &`). He copies each beat's prompt + still from the
   dashboard and renders each engine himself — **the RENDER GATE is his; the agent spends no render
   credits.**

## Parallel variants / engine bake-off

Comparing engines == **N pages sharing one stills set**. Call the scaffolder once per engine with the
same `--stills-from`, then fill each in its format:

```bash
python3 tools/new_reel.py --client serenity-sands --reel sands-v4-kling --beats 6 \
  --engine "Kling O3" --stills-from renders/v4-bluehour/stills
python3 tools/new_reel.py --client serenity-sands --reel sands-v4-vidu --beats 6 \
  --engine "Vidu Q3 Pro" --experimental --stills-from renders/v4-bluehour/stills
```

Both pages display the same approved stills; each collects its own clips. The page that **owns** the
shared stills marks `stills_source: true` in frontmatter (its clips live on the per-engine pages, so
its clip-format is not enforced). When a candidate engine wins, promote it into the matrix via
`/jstack-sf-learn` and drop `--experimental`.

## Add a beat

Append one beat section in the same skeleton shape (the `beat_section` template in `new_reel.py`) to an
existing brief and reload — the dashboard re-parses live.
