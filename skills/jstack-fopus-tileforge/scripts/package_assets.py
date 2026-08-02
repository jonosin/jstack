"""Pack processed assets into a deterministic shelf atlas and metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw


def package(contract_path: Path, asset_dir: Path, output_dir: Path, *, atlas_width: int = 384) -> dict:
    contract = json.loads(contract_path.read_text())
    placements, x, y, row_height = [], 0, 0, 0
    for asset in contract["assets"]:
        width, height = asset["size"]
        if x and x + width > atlas_width:
            x, y, row_height = 0, y + row_height, 0
        placements.append((asset, x, y))
        x += width
        row_height = max(row_height, height)
    atlas_height = y + row_height
    atlas = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))
    metadata_assets = []
    for asset, left, top in placements:
        image = Image.open(asset_dir / f"{asset['id']}.png").convert("RGBA")
        if image.size != tuple(asset["size"]):
            raise ValueError(f"{asset['id']} dimensions disagree with contract")
        atlas.alpha_composite(image, (left, top))
        record = {key: value for key, value in asset.items() if key not in {"cell", "family"}}
        record["source_family"] = asset["family"]
        record["atlas_rect"] = [left, top, image.width, image.height]
        metadata_assets.append(record)
    palette_limit = contract.get("palette_limit")
    if palette_limit:
        # Quantize RGB independently from alpha: translucent light masks may use
        # many alpha levels without consuming additional package palette entries.
        alpha = atlas.getchannel("A")
        rgb = atlas.convert("RGB").quantize(colors=palette_limit, method=Image.Quantize.MEDIANCUT).convert("RGB")
        atlas = rgb.convert("RGBA")
        atlas.putalpha(alpha)
        for asset, left, top in placements:
            atlas.crop((left, top, left + asset["size"][0], top + asset["size"][1])).save(asset_dir / f"{asset['id']}.png")
    output_dir.mkdir(parents=True, exist_ok=True)
    atlas.save(output_dir / "tileforge-atlas.png")
    colors = sorted({"#%02x%02x%02x" % pixel[:3] for pixel in atlas.get_flattened_data() if pixel[3]})
    metadata = {
        "format": "tileforge-package-v1",
        "name": contract["name"],
        "style_profile": contract["style_profile"],
        "tile_size": contract["tile_size"],
        "palette_limit": palette_limit,
        "atlas": {"file": "tileforge-atlas.png", "width": atlas.width, "height": atlas.height},
        "palette": colors,
        "assets": metadata_assets,
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    scale, label = 3, 14
    cell_width = max(asset["size"][0] for asset in contract["assets"])
    cell_height = max(asset["size"][1] for asset in contract["assets"])
    columns = 6
    rows = (len(contract["assets"]) + columns - 1) // columns
    contact = Image.new("RGBA", (columns * cell_width * scale, rows * (cell_height * scale + label)), (15, 23, 42, 255))
    draw = ImageDraw.Draw(contact)
    for index, asset in enumerate(contract["assets"]):
        column, row = index % columns, index // columns
        image = Image.open(asset_dir / f"{asset['id']}.png").convert("RGBA")
        px, py = column * cell_width * scale, row * (cell_height * scale + label)
        contact.alpha_composite(image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST), (px, py + label))
        draw.text((px + 2, py + 2), asset["id"], fill=(248, 250, 252, 255))
    contact.save(output_dir / "contact-sheet.png")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--asset-dir", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--atlas-width", type=int, default=384)
    args = parser.parse_args()
    package(args.contract, args.asset_dir, args.outdir, atlas_width=args.atlas_width)
    print(f"packaged {args.outdir}")


if __name__ == "__main__":
    main()
