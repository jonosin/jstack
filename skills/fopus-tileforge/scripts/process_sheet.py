"""Crop declared cells, remove chroma, resize exactly, and emit individual assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


def _chroma(pixel: tuple[int, int, int, int], tolerance: int) -> bool:
    red, green, blue, _ = pixel
    near_key = max(abs(red - 255), abs(green), abs(blue - 255)) <= tolerance
    ratio = red / max(1, blue)
    magenta_dominant = red > 35 and blue > 35 and 0.55 < ratio < 1.8 and red > green * 1.35 and blue > green * 1.35
    return near_key or magenta_dominant


def _light_overlay(size: tuple[int, int]) -> Image.Image:
    """Construct an exact reusable amber light mask without source-cell debris."""
    width, height = size
    center_x, center_y = (width - 1) / 2, (height - 1) / 2
    radius = max(1.0, min(width, height) / 2 - 2)
    output = []
    for index in range(width * height):
        x, y = index % width, index // width
        distance = (((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5) / radius
        if distance >= 1:
            output.append((255, 184, 64, 0))
        else:
            alpha = round((1 - distance) * 150)
            output.append((255, 202 if distance < 0.45 else 174, 72 if distance < 0.45 else 48, alpha))
    image = Image.new("RGBA", size)
    image.putdata(output)
    return image


def _clean(image: Image.Image, tolerance: int, transparent: bool) -> Image.Image:
    rgba = image.convert("RGBA")
    rgba.putdata([(r, g, b, 0) if _chroma((r, g, b, a), tolerance) else (r, g, b, a)
                  for r, g, b, a in rgba.get_flattened_data()])
    return rgba


def _make_seamless(image: Image.Image) -> Image.Image:
    """Preserve the authored tile while making its repeat boundary exact."""
    pixels = image.load()
    for x in range(image.width):
        pixels[x, image.height - 1] = pixels[x, 0]
    for y in range(image.height):
        pixels[image.width - 1, y] = pixels[0, y]
    return image


def _apply_shared_palette(canvases: list[Image.Image], limit: int) -> list[Image.Image]:
    if not 1 <= limit <= 256:
        raise ValueError("palette limit must be between 1 and 256")
    opaque = [pixel[:3] for canvas in canvases for pixel in canvas.get_flattened_data() if pixel[3]]
    if len(set(opaque)) <= limit:
        return canvases
    sample = Image.new("RGB", (len(opaque), 1))
    sample.putdata(opaque)
    palette = sample.quantize(colors=limit, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    results = []
    for canvas in canvases:
        alpha = canvas.getchannel("A")
        quantized = canvas.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE).convert("RGBA")
        quantized.putalpha(alpha)
        results.append(quantized)
    return results


def process(
    contract_path: Path,
    sources: dict[str, Path],
    output_dir: Path,
    *,
    tolerance: int,
    palette: int | None = None,
) -> dict:
    contract = json.loads(contract_path.read_text())
    source_spec = contract["source"]
    opened: dict[str, Image.Image] = {}
    for family in {asset["family"] for asset in contract["assets"]}:
        if family not in sources:
            raise ValueError(f"missing source family: {family}")
        opened[family] = Image.open(sources[family]).convert("RGBA")
    asset_dir = output_dir / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    prepared: list[tuple[dict, Image.Image]] = []
    for asset in contract["assets"]:
        column, row = asset["cell"]
        family_image = opened[asset["family"]]
        left = round(column * family_image.width / source_spec["columns"])
        right = round((column + 1) * family_image.width / source_spec["columns"])
        top = round(row * family_image.height / source_spec["rows"])
        bottom = round((row + 1) * family_image.height / source_spec["rows"])
        cell_width, cell_height = right - left, bottom - top
        inset = max(3, round(min(cell_width, cell_height) * 0.02))
        cell = opened[asset["family"]].crop(
            (left + inset, top + inset,
             right - inset, bottom - inset)
        )
        cell = _clean(cell, tolerance, asset["transparent"])
        bbox = cell.getchannel("A").getbbox()
        if bbox is None:
            raise ValueError(f"{asset['id']} contains no accepted pixels")
        content = cell.crop(bbox)
        if asset.get("transform") == "rotate90":
            content = content.transpose(Image.Transpose.ROTATE_270)
        elif asset.get("transform") == "rotate270":
            content = content.transpose(Image.Transpose.ROTATE_90)
        target = tuple(asset["size"])
        safe_target = (max(1, target[0] - 2), max(1, target[1] - 2)) if asset["transparent"] else target
        content.thumbnail(safe_target, Image.Resampling.NEAREST)
        canvas = Image.new("RGBA", target, (0, 0, 0, 0))
        x = max(1, min(target[0] - content.width - 1, asset["anchor"][0] - content.width // 2)) if asset["transparent"] else 0
        y = target[1] - content.height - 1 if asset["transparent"] else 0
        canvas.alpha_composite(content, (x, y))
        if not asset["transparent"]:
            canvas = content.resize(target, Image.Resampling.NEAREST)
            canvas.putalpha(Image.new("L", target, 255))
            if asset["id"].startswith("floor-"):
                canvas = _make_seamless(canvas)
        elif asset["id"].startswith("light-warm-"):
            canvas = _light_overlay(target)
        prepared.append((asset, canvas))
    normalized = _apply_shared_palette([canvas for _, canvas in prepared], palette) if palette else [
        canvas for _, canvas in prepared
    ]
    records = []
    for (asset, _), canvas in zip(prepared, normalized):
        path = asset_dir / f"{asset['id']}.png"
        canvas.save(path)
        opaque = canvas.getchannel("A").getbbox()
        records.append({"id": asset["id"], "file": f"assets/{path.name}",
                        "opaque_extent": list(opaque) if opaque else None})
    for image in opened.values():
        image.close()
    result = {
        "format": "tileforge-processed-v1",
        "contract": contract_path.name,
        "style_profile": contract["style_profile"],
        "tile_size": contract["tile_size"],
        "chroma_tolerance": tolerance,
        "assets": records,
    }
    if palette is not None:
        result["palette_limit"] = palette
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "processed.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def _sources(values: list[str]) -> dict[str, Path]:
    parsed = {}
    for value in values:
        family, separator, path = value.partition("=")
        if not separator or not family or not path:
            raise ValueError("--source must be FAMILY=PATH")
        parsed[family] = Path(path)
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--source", action="append", default=[], required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--tolerance", type=int, default=128)
    parser.add_argument("--palette", type=int, help="Apply one shared opaque palette to the package.")
    args = parser.parse_args()
    process(args.contract, _sources(args.source), args.outdir, tolerance=args.tolerance, palette=args.palette)
    print(f"processed {len(args.source)} source families into {args.outdir}")


if __name__ == "__main__":
    main()
