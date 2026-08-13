# Use case: feed Claude-Code-generated assets into Claude Design

Claude Design can invent decorative graphics, but it **cannot generate real media** and it has no access
to Jono's image pipeline. Claude Code can — via `/imgen` (Gemini image gen) for images, and the
StayFrame / `/vidgen` pipeline for video. This use case generates assets locally and feeds them
into a CD project so CD composes the design around real, on-brand assets instead of placeholders.

Read first: `designsync-mechanics.md`, `prompt-authoring.md`. Pairs with uc-build-existing / uc-edit-build.

## When this applies

- "generate the images and put them in the design", "make assets for the CD build", "feed new artwork to
  Claude Design", "replace the placeholders with real generated images".

## Division of labor

- **Claude Code generates** the assets: `/imgen` for images/sprites/textures (supports reference
  images + chroma-key post-processing), `/vidgen` for any video/clip. These are the things CD
  cannot make.
- **Claude Design composes** with them: placement, scale, cropping, layering, motion — its creative call.
- **This skill** moves the generated files into the project and writes the legend that frees CD to compose.

## Steps

1. **Decide what to generate** from the build's needs: which placeholders are images CD should compose
   (decorative/texture/hero art) vs media the finishing pass injects later (real reel, real photography).
   Only generate what CD will actually lay out.
2. **Generate locally.** Run `/imgen` (or `/vidgen` for clips). Save into the package dir as
   named `ref-*` files. Apply any required post-processing (e.g. tint/chroma) **before** upload so CD
   receives the final bytes.
3. **Upload.** `finalize_plan` (add the new `ref-*` paths to `writes`, `deletes:[]`) → `write_files`
   (`localPath` — bytes never enter context, which matters for many/large images) → `list_files` verify.
4. **Write the legend with creative latitude** (`prompt-authoring.md`): describe **what each generated
   asset depicts**, mark decorative-vs-literal honesty, lock only the hard constraints (brand, tint
   recipe, "decorative only"), and explicitly free placement/scale/crop/layer/motion. Offer an optional
   suggested pairing CD may override.
5. **Hand off or edit:** new build → fold into uc-build-existing's first-message; existing build → an edit
   message (uc-edit-build) or a direct push if the change is just swapping a file CD already references.

## Notes

- Keep generated assets in the package dir so a re-run / finishing pass finds them next to the build.
- Honesty rule still applies: generated decorative art is fine; never present generated imagery as a real
  photo of the real property where that would mislead. Mark it decorative in the legend.
