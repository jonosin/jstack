"""Render native-size asset, placement, and before/after QA images from a package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw


def _contact(contract: dict, asset_dir: Path, destination: Path, *, scale: int) -> None:
    items = contract["assets"]
    columns, label = 6, 14
    cell_w, cell_h = max(a["size"][0] for a in items), max(a["size"][1] for a in items)
    rows = (len(items) + columns - 1) // columns
    image = Image.new("RGBA", (columns * cell_w * scale, rows * (cell_h * scale + label)), (15, 23, 42, 255))
    draw = ImageDraw.Draw(image)
    for index, spec in enumerate(items):
        x, y = (index % columns) * cell_w * scale, (index // columns) * (cell_h * scale + label)
        item = Image.open(asset_dir / f"{spec['id']}.png").convert("RGBA")
        image.alpha_composite(item.resize((item.width * scale, item.height * scale), Image.Resampling.NEAREST), (x, y + label))
        draw.text((x + 2, y + 2), spec["id"], fill=(248, 250, 252, 255))
    image.save(destination)


def render(contract_path: Path, output_dir: Path, evidence_dir: Path, placement_path: Path | None = None, before_dir: Path | None = None) -> dict:
    contract = json.loads(contract_path.read_text())
    asset_dir = output_dir / "assets"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    _contact(contract, asset_dir, evidence_dir / "assets-native.png", scale=1)
    _contact(contract, asset_dir, evidence_dir / "assets-preview.png", scale=3)
    placement_file = placement_path or output_dir / "placement.json"
    if placement_file.is_file():
        placements = json.loads(placement_file.read_text())
        placements = placements.get("placements", placements)
        declared = {item["id"] for item in contract["assets"]}
        for item in placements:
            if item.get("id") not in declared:
                raise ValueError(f"placement uses undeclared asset: {item.get('id')}")
            if not all(isinstance(item.get(key), int) for key in ("x", "y")):
                raise ValueError(f"{item['id']} placement coordinates must be integers")
            if item["x"] < 0 or item["y"] < 0:
                raise ValueError(f"{item['id']} placement coordinates must be non-negative")
            if not isinstance(item.get("z", 0), int):
                raise ValueError(f"{item['id']} z must be an integer")
        width = max((item["x"] + Image.open(asset_dir / f"{item['id']}.png").width for item in placements), default=1)
        height = max((item["y"] + Image.open(asset_dir / f"{item['id']}.png").height for item in placements), default=1)
        scene = Image.new("RGBA", (width, height), (31, 41, 55, 255))
        layer = Image.new("RGBA", scene.size, (31, 41, 55, 255))
        layer_draw = ImageDraw.Draw(layer)
        for item in sorted(placements, key=lambda value: (value.get("z", 0), value["y"])):
            asset = Image.open(asset_dir / f"{item['id']}.png").convert("RGBA")
            scene.alpha_composite(asset, (item["x"], item["y"]))
            layer.alpha_composite(asset, (item["x"], item["y"]))
            color = (250, 204, 21, 255) if item.get("z", 0) else (56, 189, 248, 255)
            bounds = (item["x"], item["y"], item["x"] + asset.width - 1, item["y"] + asset.height - 1)
            layer_draw.rectangle(bounds, outline=color)
            layer_draw.text((item["x"] + 1, item["y"] + 1), f"z{item.get('z', 0)}", fill=color)
        scene.save(evidence_dir / "placement-native.png")
        layer.save(evidence_dir / "layer-native.png")
    if before_dir and before_dir.is_dir():
        pairs = []
        for spec in contract["assets"]:
            old, new = before_dir / f"{spec['id']}.png", asset_dir / f"{spec['id']}.png"
            if old.is_file() and new.is_file():
                old_image, new_image = Image.open(old).convert("RGBA"), Image.open(new).convert("RGBA")
                width, height = max(old_image.width, new_image.width), max(old_image.height, new_image.height)
                pair = Image.new("RGBA", (width * 2, height), (0, 0, 0, 0)); pair.alpha_composite(old_image, (0, 0)); pair.alpha_composite(new_image, (width, 0)); pairs.append(pair)
        if pairs:
            comparison = Image.new("RGBA", (max(p.width for p in pairs), sum(p.height for p in pairs)), (15, 23, 42, 255))
            y = 0
            for pair in pairs: comparison.alpha_composite(pair, (0, y)); y += pair.height
            comparison.save(evidence_dir / "comparison-native.png")
    return {"format": "tileforge-qa-surface-v1", "status": "PASS", "evidence_dir": str(evidence_dir)}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--contract", type=Path, required=True); parser.add_argument("--outdir", type=Path, required=True); parser.add_argument("--evidence-dir", type=Path, required=True); parser.add_argument("--placement", type=Path); parser.add_argument("--before-dir", type=Path)
    args = parser.parse_args(); print(json.dumps(render(args.contract, args.outdir, args.evidence_dir, args.placement, args.before_dir)))


if __name__ == "__main__": main()
