"""Floors repeat exactly and representative opaque boundaries compose cleanly."""

from __future__ import annotations

import tempfile
from pathlib import Path

from PIL import Image

from test_tileforge_structure import build


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        _, output = build(Path(temporary))
        for path in sorted((output / "assets").glob("floor-*.png")):
            image = Image.open(path).convert("RGBA")
            assert [image.getpixel((0, y)) for y in range(image.height)] == [image.getpixel((image.width - 1, y)) for y in range(image.height)]
            assert [image.getpixel((x, 0)) for x in range(image.width)] == [image.getpixel((x, image.height - 1)) for x in range(image.width)]
        wall = Image.open(output / "assets" / "wall-north.png").convert("RGBA")
        left = Image.open(output / "assets" / "wall-corner-left.png").convert("RGBA")
        right = Image.open(output / "assets" / "wall-corner-right.png").convert("RGBA")
        strip = Image.new("RGBA", (left.width + wall.width + right.width, max(left.height, wall.height, right.height)))
        strip.paste(left, (0, 0), left)
        strip.paste(wall, (left.width, 0), wall)
        strip.paste(right, (left.width + wall.width, 0), right)
        assert strip.getchannel("A").getbbox() is not None
    print("tileforge seam and boundary tests passed")


if __name__ == "__main__":
    main()
