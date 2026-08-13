from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_map import validate_map  # noqa: E402


def map_fixture() -> dict:
    width, height = 40, 28
    return {
        "width": width, "height": height,
        "collision": ["#" * width] + ["#" + "." * (width - 2) + "#" for _ in range(height - 2)] + ["#" * width],
        "entry": {"x": 2, "y": 2},
        "seat_zones": [{"id": "communal", "access": [{"x": 20, "y": 14}]}, {"id": "solo", "access": [{"x": 34, "y": 22}]}],
        "objects": [{"id": "chair/down", "x": 20, "y": 13, "w": 1, "h": 1, "layer": "furniture"}],
        "lighting": [{"id": "lamp", "x": 20, "y": 12, "layer": "lighting"}],
        "character_instances": [{"kind": "spawn", "x": 2, "y": 2}, {"kind": "seat-anchor", "x": 20, "y": 14}],
    }


def main() -> None:
    valid = map_fixture()
    validate_map(valid, asset_ids={"chair/down"})
    blocked = map_fixture()
    blocked["collision"][14] = "#" * 40
    try:
        validate_map(blocked, asset_ids={"chair/down"})
    except AssertionError as error:
        assert "unreachable" in str(error)
    else:
        raise AssertionError("unreachable seating zone was accepted")
    invalid_character = map_fixture()
    invalid_character["character_instances"][0]["kind"] = "raster-detected"
    try:
        validate_map(invalid_character, asset_ids={"chair/down"})
    except AssertionError as error:
        assert "explicit spawn/seat-anchor" in str(error)
    else:
        raise AssertionError("implicit raster character placement was accepted")
    print("tileforge map tests passed")


if __name__ == "__main__":
    main()
