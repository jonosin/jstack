"""The same captured contract and synthetic sources replay identically."""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

from test_tileforge_structure import build


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    hashes = []
    for _ in range(2):
        with tempfile.TemporaryDirectory() as temporary:
            _, output = build(Path(temporary))
            hashes.append({name: digest(output / name) for name in
                           ("tileforge-atlas.png", "metadata.json", "contact-sheet.png", "validation-report.json")})
    assert hashes[0] == hashes[1]
    print("tileforge replay tests passed")


if __name__ == "__main__":
    main()
