"""Validate a packaged Tileforge contract against its atlas and metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

CARDINAL = {"up", "down", "left", "right"}


def validate(contract_path: Path, output_dir: Path) -> dict:
    contract = json.loads(contract_path.read_text())
    metadata = json.loads((output_dir / "metadata.json").read_text())
    assert metadata["format"] == "tileforge-package-v1"
    assert metadata["name"] == contract["name"]
    assert metadata["style_profile"] == contract["style_profile"]
    declared = {asset["id"]: asset for asset in contract["assets"]}
    packaged = {asset["id"]: asset for asset in metadata["assets"]}
    assert len(declared) == len(contract["assets"]), "contract IDs must be unique"
    assert set(packaged) == set(declared), "required IDs must exist exactly once"
    with Image.open(output_dir / metadata["atlas"]["file"]) as raw:
        atlas = raw.convert("RGBA")
    assert atlas.size == (metadata["atlas"]["width"], metadata["atlas"]["height"])
    rectangles = []
    for asset_id, asset in packaged.items():
        expected = declared[asset_id]
        assert asset["size"] == expected["size"]
        x, y, width, height = asset["atlas_rect"]
        assert width > 0 and height > 0 and 0 <= x and 0 <= y
        assert x + width <= atlas.width and y + height <= atlas.height
        for previous in rectangles:
            px, py, pw, ph = previous
            assert not (x < px + pw and px < x + width and y < py + ph and py < y + height), "atlas rectangles overlap"
        rectangles.append(asset["atlas_rect"])
        anchor_x, anchor_y = asset["anchor"]
        assert 0 <= anchor_x < width and 0 <= anchor_y < height, f"{asset_id} drawing anchor out of bounds"
        collision = asset["collision"]
        assert len(collision) == 4
        cx, cy, cw, ch = collision
        assert 0 <= cx <= width and 0 <= cy <= height and 0 <= cw <= width - cx and 0 <= ch <= height - cy
        if "seat" in asset:
            seat = asset["seat"]
            assert seat["facing"] in CARDINAL, f"{asset_id} seat must be cardinal"
            sx, sy = seat["anchor"]
            assert 0 <= sx < width and 0 <= sy < height, f"{asset_id} seat anchor out of bounds"
        crop = atlas.crop((x, y, x + width, y + height))
        with Image.open(output_dir / "assets" / f"{asset_id}.png") as raw_asset:
            assert crop.tobytes() == raw_asset.convert("RGBA").tobytes(), f"{asset_id} disagrees with atlas pixels"
        assert crop.getchannel("A").getbbox() is not None, f"{asset_id} is empty"
        if asset["transparent"]:
            alpha = crop.getchannel("A")
            border = ([alpha.getpixel((column, 0)) for column in range(width)]
                      + [alpha.getpixel((column, height - 1)) for column in range(width)]
                      + [alpha.getpixel((0, row)) for row in range(1, height - 1)]
                      + [alpha.getpixel((width - 1, row)) for row in range(1, height - 1)])
            assert not any(border), f"{asset_id} alpha border is not clean"
    for orientation_set in contract["required_orientation_sets"]:
        prefix = orientation_set["prefix"]
        actual = {asset["seat"]["facing"] for asset in metadata["assets"]
                  if asset["id"].startswith(prefix + "-") and "seat" in asset}
        assert actual == set(orientation_set["directions"]), f"{prefix} cardinal set incomplete"
    colors = sorted({"#%02x%02x%02x" % pixel[:3] for pixel in atlas.get_flattened_data() if pixel[3]})
    assert colors == metadata["palette"], "metadata and PNG palette disagree"
    palette_limit = contract.get("palette_limit")
    assert palette_limit is not None, "contract must declare a package palette limit"
    assert metadata.get("palette_limit") == palette_limit, "metadata palette limit disagrees with contract"
    assert len(colors) <= palette_limit, f"package palette has {len(colors)} colors; limit is {palette_limit}"
    for asset in packaged.values():
        x, y, width, height = asset["atlas_rect"]
        asset_colors = {"#%02x%02x%02x" % pixel[:3] for pixel in atlas.crop((x, y, x + width, y + height)).get_flattened_data() if pixel[3]}
        assert asset_colors <= set(colors), f"{asset['id']} uses colors outside package palette"
    report = {
        "format": "tileforge-validation-v1",
        "status": "PASS",
        "asset_count": len(packaged),
        "checks": [
            "unique-required-ids", "atlas-rectangles", "alpha-borders", "anchors",
            "collision-footprints", "cardinal-seating", "orientation-sets", "metadata-png-agreement", "asset-atlas-agreement", "palette-limit"
        ],
    }
    (output_dir / "validation-report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    report = validate(args.contract, args.outdir)
    print(f"validated {report['asset_count']} assets in {args.outdir}")


if __name__ == "__main__":
    main()
