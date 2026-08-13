"""Machine-readable proof that every seat is cardinal and sets are complete."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDINAL = {"up", "down", "left", "right"}


def main() -> None:
    contract = json.loads((ROOT / "references" / "contracts" / "warm-cardinal-study-hall.json").read_text())
    seats = [asset for asset in contract["assets"] if "seat" in asset]
    assert seats
    assert all(asset["seat"]["facing"] in CARDINAL for asset in seats)
    assert not any(any(token in asset["seat"]["facing"] for token in ("diagonal", "north-east", "south-west")) for asset in seats)
    for orientation_set in contract["required_orientation_sets"]:
        prefix = orientation_set["prefix"]
        actual = {asset["seat"]["facing"] for asset in seats if asset["id"].startswith(prefix + "-")}
        assert actual == CARDINAL, f"{prefix} does not provide exactly four cardinal variants"
    print("tileforge cardinal seating tests passed")


if __name__ == "__main__":
    main()
