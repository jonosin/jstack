"""Build contract-aligned source sheets from separately supplied asset images."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


def _pairs(values: list[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        asset_id, separator, raw_path = value.partition("=")
        if not separator or not asset_id or not raw_path:
            raise ValueError("--asset must be ASSET_ID=PATH")
        if asset_id in result:
            raise ValueError(f"duplicate --asset: {asset_id}")
        result[asset_id] = Path(raw_path)
    return result


def prepare(contract_path: Path, sources: dict[str, Path], output_dir: Path) -> dict:
    contract = json.loads(contract_path.read_text())
    declared = {asset["id"]: asset for asset in contract["assets"]}
    unknown, missing = set(sources) - set(declared), set(declared) - set(sources)
    if unknown:
        raise ValueError(f"undeclared asset IDs: {sorted(unknown)}")
    if missing:
        raise ValueError(f"missing asset IDs: {sorted(missing)}")
    spec = contract["source"]
    width, height = spec["columns"] * spec["cell_width"], spec["rows"] * spec["cell_height"]
    sheets: dict[str, Image.Image] = {}
    shared_palette = {(255, 0, 255)}
    records = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for asset in contract["assets"]:
        source = sources[asset["id"]]
        if not source.is_file():
            raise ValueError(f"source does not exist: {source}")
        family = asset["family"]
        sheet = sheets.setdefault(family, Image.new("RGBA", (width, height), (255, 0, 255, 255)))
        with Image.open(source) as raw:
            image = raw.convert("RGBA")
        shared_palette.update(pixel[:3] for pixel in image.get_flattened_data() if pixel[3])
        column, row = asset["cell"]
        x, y = column * spec["cell_width"], row * spec["cell_height"]
        processing = asset.get("processing", {})
        transform = "none"
        source_fit = processing.get("source_fit", "native")
        if source_fit == "contain-nearest":
            padding = int(processing.get("source_padding", 3))
            target = (spec["cell_width"] - padding * 2, spec["cell_height"] - padding * 2)
            if min(target) < 1:
                raise ValueError(f"{asset['id']} source padding leaves no drawable area")
            scale = min(target[0] / image.width, target[1] / image.height)
            resized = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
            if resized != image.size:
                image = image.resize(resized, Image.Resampling.NEAREST)
                transform = "contain-nearest"
        elif source_fit != "native":
            raise ValueError(f"{asset['id']} has unsupported source_fit: {source_fit}")
        elif image.width > spec["cell_width"] or image.height > spec["cell_height"]:
            if source_fit == "native":
                raise ValueError(
                    f"{asset['id']} exceeds its source cell; declare "
                    "processing.source_fit=contain-nearest to resize it"
                )
        align = processing.get("source_align", "center")
        left = x + (spec["cell_width"] - image.width) // 2
        if align == "center":
            top = y + (spec["cell_height"] - image.height) // 2
        elif align == "bottom-center":
            top = y + spec["cell_height"] - image.height
        else:
            raise ValueError(f"{asset['id']} has unsupported source_align: {align}")
        sheet.alpha_composite(image, (left, top))
        records.append({"id": asset["id"], "family": family, "source": str(source),
                        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "transform": transform})
    for family, sheet in sheets.items():
        sheet.save(output_dir / f"{family}.png")
    payload = {"format": "tileforge-source-provenance-v1", "contract": contract_path.name,
               "shared_palette": ["#%02x%02x%02x" % color for color in sorted(shared_palette)], "assets": records}
    (output_dir / "source-provenance.json").write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--asset", action="append", required=True, default=[])
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.contract, _pairs(args.asset), args.outdir)
    print(f"prepared {len(result['assets'])} assets in {args.outdir}")


if __name__ == "__main__":
    main()
