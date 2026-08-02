"""Validate explicit Tileforge proof-map data without inferring gameplay from pixels."""

from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path


def _reachable(collision: list[str], start: tuple[int, int]) -> set[tuple[int, int]]:
    width, height = len(collision[0]), len(collision)
    seen = {start}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < width and 0 <= ny < height and collision[ny][nx] == "." and (nx, ny) not in seen:
                seen.add((nx, ny))
                queue.append((nx, ny))
    return seen


def validate_map(data: dict, *, asset_ids: set[str]) -> None:
    width, height = data["width"], data["height"]
    assert width >= 40 and height >= 28, "proof map must be at least 40x28 logical cells"
    collision = data["collision"]
    assert len(collision) == height and all(len(row) == width for row in collision), "collision dimensions disagree with map"
    assert all(set(row) <= {".", "#"} for row in collision), "collision uses only explicit walk/block cells"
    entry = data["entry"]
    start = (entry["x"], entry["y"])
    assert collision[start[1]][start[0]] == ".", "entry must be walkable"
    for obj in data.get("objects", []):
        assert obj["id"] in asset_ids, f"unknown asset ID: {obj['id']}"
        assert 0 <= obj["x"] and 0 <= obj["y"] and obj["x"] + obj["w"] <= width and obj["y"] + obj["h"] <= height, f"{obj['id']} is out of map bounds"
    for character in data.get("character_instances", []):
        assert character.get("kind") in {"spawn", "seat-anchor"}, "characters must use explicit spawn/seat-anchor instances"
        assert 0 <= character.get("x", -1) < width and 0 <= character.get("y", -1) < height, "character instance is out of map bounds"
    assert all(light.get("layer") == "lighting" for light in data.get("lighting", [])), "lighting must stay in its own layer"
    reachable = _reachable(collision, start)
    for zone in data["seat_zones"]:
        for access in zone["access"]:
            point = (access["x"], access["y"])
            assert point in reachable, f"seating zone {zone['id']} is unreachable"
            x, y = point
            clear = {(nx, ny) for nx in (x, x + 1) for ny in (y, y + 1)}
            assert clear <= reachable, f"seating zone {zone['id']} lacks 2x2 circulation clearance"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument("--asset-manifest", type=Path, required=True)
    args = parser.parse_args()
    map_data = json.loads(args.map.read_text())
    assets = json.loads(args.asset_manifest.read_text())["assets"]
    validate_map(map_data, asset_ids={asset["id"] for asset in assets})
    print(f"validated {args.map}")


if __name__ == "__main__":
    main()
