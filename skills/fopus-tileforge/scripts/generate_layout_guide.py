"""Generate one fixed-cell guide for a declared source family."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw


def generate(contract_path: Path, family: str, output: Path) -> None:
    contract = json.loads(contract_path.read_text())
    source = contract["source"]
    width = source["cell_width"] * source["columns"]
    height = source["cell_height"] * source["rows"]
    assets = [asset for asset in contract["assets"] if asset["family"] == family]
    if not assets:
        raise ValueError(f"unknown or empty family: {family}")
    # Crop cells remain completely free of guide marks. The sidecar legend
    # avoids changing the declared art-grid geometry.
    image = Image.new("RGB", (width, height), (255, 0, 255))
    draw = ImageDraw.Draw(image)
    for asset in assets:
        column, row = asset["cell"]
        left, top = column * source["cell_width"], row * source["cell_height"]
        right, bottom = left + source["cell_width"] - 1, top + source["cell_height"] - 1
        draw.rectangle((left, top, right, bottom), fill=(255, 0, 255))
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    output.with_suffix(".labels.txt").write_text("\n".join(
        f"[{asset['cell'][0]},{asset['cell'][1]}] {asset['id']}" for asset in assets
    ) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--family", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    generate(args.contract, args.family, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
