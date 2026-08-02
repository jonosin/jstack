---
name: jstack-fopus-tileforge
description: Use when the user asks to create, process, package, repair, or validate reusable pixel-art environment tiles and objects for a named world style.
---

# Fopus: Tileforge

Forge reusable environment assets from coherent source sheets. Generated art proposes pixels; the declared contract and bundled scripts own geometry, transparency, anchors, atlas metadata, previews, and structural acceptance.

## Contract

Produce preserved raw sources, processed individual assets, an atlas, metadata, contact sheet, assembled test scene, validation report, and contemporaneous `trace.md`. Do not build character animation, infer gameplay data from pixels, or silently compose a final world as one generated background.

## Runtime

Call `load_workspace_dependencies`. Set `PYTHON` to the returned Python executable and `SKILL_DIR` to this directory. Create a run directory, copy `references/trace-template.md` to `<run>/trace.md`, and append every prompt, input role, source, rejection, repair, command, checksum, and verdict as it happens.

## Required selection gate

Stop before generation until the user selects one named file under `references/styles/`.

1. Use an explicitly named profile.
2. Otherwise list available profile filenames and obtain a choice.
3. If none fits, copy `references/styles/style-template.md`, complete a new named profile, and obtain approval.

Read exactly the selected profile. Never silently default or combine profiles. Record its path and SHA-256 in `trace.md`. The main skill owns no visual style language.

## Workflow

### 1. Declare the package

Copy `references/asset-contract-template.json` or select an explicit compatible contract. Declare every stable ID, family, source cell, logical size, drawing anchor, collision footprint, layer, transparency rule, and optional cardinal seat anchor. Record the contract hash before generation.

### 2. Generate fixed-cell guides

Create one guide per coherent source family:

```sh
"$PYTHON" "$SKILL_DIR/scripts/generate_layout_guide.py" \
  --contract references/contracts/<contract>.json \
  --family <family> --output guide/<family>.png
```

Labels stay outside art cells. The guide is placement-only and uses flat `#ff00ff` for transparent objects. Generated cell geometry is never trusted without exact cropping.

### 3. Generate coherent sources

Load `$imagegen`. Generate related assets together using the selected style profile, declared guide, and explicitly recorded visual-reference roles. Preserve each raw output before processing. Require isolated assets, cardinal alignment where declared, no text, logos, UI, diagonal objects, clipping, overlap, guide marks, or cast shadows outside declared cells.

Reject or regenerate a complete failing family when style, perspective, geometry, or orientation drifts. Do not patch one final cell from an unrelated generation.

#### Directional chair metadata and contextual orientation

`seat.facing` is cardinal gameplay/interaction metadata for the sitter. It is not screen-side geometry and cannot prove a chair's pixels, backrest location, or 2.5D orientation. The structural validator checks only that a chair declares a cardinal `seat.facing`; it never certifies visual orientation.

For ambiguous or occluded directional furniture, use the accepted calibration map as the only visual reference and deliberately exclude ambiguous chair crops. First generate a complete, unobstructed contextual station—not an isolated asset—showing the relationship that must read. Describe that relationship naturally, for example: “one wooden chair pulled slightly away from the near edge of the table, centered, as if someone sitting in it would look across the tabletop toward the far wall.” Do not prompt with asset labels or cardinal wording such as “up,” “down,” or “facing upward.”

Show the accepted calibration map and generated station to the user, obtain explicit contextual-orientation acceptance, and record the reference, natural-language relationship, prompt, and acceptance in `trace.md` and `visual-review.json`. A contextual review must set `user_accepted` and `isolated_after_acceptance` to `true`, provide both relationships, and use verdict `accepted`. Only then crop/forge the chair. QA it by placing the forged tile back into the same table-and-chair relationship and inspect that relationship visually. Filenames, direction labels, `seat.facing`, `expected_backrest_side`, `rear-seat-edge`, and deterministic declarations are not visual evidence.

### 4. Process and package

Run from the package directory:

```sh
"$PYTHON" "$SKILL_DIR/scripts/process_sheet.py" \
  --contract references/contracts/<contract>.json \
  --source <family>=input/<family>.png \
  --outdir output --palette <profile-limit> --tolerance <profile-tolerance>

"$PYTHON" "$SKILL_DIR/scripts/package_assets.py" \
  --contract references/contracts/<contract>.json \
  --asset-dir output/assets --outdir output
```

The processor crops declared cells, removes chroma, normalizes exact dimensions, applies one package palette, and records opaque extents. The packager builds the atlas, contact sheet, metadata, and report without deriving collision or interaction from pixels.

### 5. Validate

```sh
"$PYTHON" "$SKILL_DIR/scripts/validate_output.py" \
  --contract references/contracts/<contract>.json --outdir output

"$PYTHON" "$SKILL_DIR/scripts/validate_map.py" \
  --asset-manifest output/metadata.json --map <assembled-map.json>
```

Require unique IDs, exact atlas rectangles, clean alpha, in-bounds anchors and footprints, palette agreement, cardinal-only seating, complete required orientation sets, map connectivity, and declared circulation widths. Structural validation and visual acceptance are separate verdicts.

### 6. Review

Review the final contact sheet, assembled map, metadata, and validation report. Check simplicity, coherent palette and perspective, seams, scale, lighting, repetition, readable paths, cardinal seating, character compatibility, and source-to-atlas mapping. Use the built-in in-app Browser for the assembled proof and capture screenshot evidence.

For every contextual directional-furniture review, inspect the calibration map, the accepted unobstructed station, and the recreated post-forge placement together. Confirm the chair is pulled from the intended table edge and that a sitter would look across the tabletop toward the intended wall. Record that relationship and the explicit user acceptance in `visual-review.json`; do not substitute filename, direction label, metadata, or screen-side inspection for it.

### 7. Report

Return source, atlas, assets, metadata, contact sheet, assembled proof, validation report, trace, and screenshot paths. State structural checks and visual QA separately. Report every unresolved failure; never call a partially skipped run complete.

## Tests

```sh
"$PYTHON" "$SKILL_DIR/tests/test_tileforge_structure.py"
"$PYTHON" "$SKILL_DIR/tests/test_replay.py"
```

## Gotchas

- Preserve generated raw sheets before resizing or cleanup; chroma removal must happen before nearest-neighbor normalization.
- Reject guide-line or chroma residue even when structural validation passes.
- Keep character pixels out of Tileforge environment sources; Worldforge or the proof renderer places characters from validated authored anchors.

## Next skills

| Next | When |
|---|---|
| `$imagegen` | Generate coherent environment source sheets against the fixed-cell guides. |
| `/jstack-skilltune` | Measure and improve an installed Tileforge workflow against held-out packages. |
