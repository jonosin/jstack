"""Transparent packaged assets retain empty one-pixel borders."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from PIL import Image

from test_tileforge_structure import build


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        _, output = build(Path(temporary))
        metadata = json.loads((output / "metadata.json").read_text())
        atlas = Image.open(output / "tileforge-atlas.png").convert("RGBA")
        for asset in (item for item in metadata["assets"] if item["transparent"]):
            x, y, width, height = asset["atlas_rect"]
            alpha = atlas.crop((x, y, x + width, y + height)).getchannel("A")
            assert alpha.getbbox() is not None
            assert not any(alpha.getpixel((column, 0)) or alpha.getpixel((column, height - 1)) for column in range(width))
            assert not any(alpha.getpixel((0, row)) or alpha.getpixel((width - 1, row)) for row in range(height))
    print("tileforge alpha tests passed")


if __name__ == "__main__":
    main()
