"""End-to-end structural proof for the declared multi-family contract."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from package_assets import package  # noqa: E402
from process_sheet import process  # noqa: E402
from validate_output import validate  # noqa: E402


def make_sources(directory: Path, contract_path: Path) -> dict[str, Path]:
    contract = json.loads(contract_path.read_text())
    spec = contract["source"]
    size = (spec["columns"] * 32, spec["rows"] * 32)
    paths = {}
    for family_index, family in enumerate(sorted({asset["family"] for asset in contract["assets"]})):
        image = Image.new("RGB", size, (255, 0, 255))
        draw = ImageDraw.Draw(image)
        for index, asset in enumerate(a for a in contract["assets"] if a["family"] == family):
            column, row = asset["cell"]
            left, top = column * 32 + 5, row * 32 + 5
            color = (60 + family_index * 40, 80 + index % 5 * 20, 30)
            draw.rectangle((left, top, left + 20, top + 20), fill=color)
        path = directory / f"{family}.png"
        image.save(path)
        paths[family] = path
    return paths


def build(directory: Path) -> tuple[Path, Path]:
    contract = ROOT / "references" / "contracts" / "warm-cardinal-study-hall.json"
    output = directory / "output"
    sources = make_sources(directory, contract)
    process(contract, sources, output, tolerance=128)
    package(contract, output / "assets", output)
    validate(contract, output)
    return contract, output


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        contract, output = build(Path(temporary))
        declared = json.loads(contract.read_text())
        metadata = json.loads((output / "metadata.json").read_text())
        report = json.loads((output / "validation-report.json").read_text())
        assert len(metadata["assets"]) == len(declared["assets"])
        assert report["status"] == "PASS"
        assert report["asset_count"] == len(declared["assets"])
        assert {asset["id"] for asset in metadata["assets"]} == {asset["id"] for asset in declared["assets"]}
    print("tileforge structural tests passed")


if __name__ == "__main__":
    main()
