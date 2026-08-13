"""Validate optional image-quality requirements declared by a Tileforge contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


def _ratio(box: tuple[int, int, int, int] | None, size: tuple[int, int]) -> float:
    if not box:
        return 0.0
    return round(((box[2] - box[0]) * (box[3] - box[1])) / (size[0] * size[1]), 4)


def validate(contract_path: Path, output_dir: Path, provenance_path: Path | None = None) -> dict:
    contract = json.loads(contract_path.read_text())
    qa = contract.get("qa", {})
    provenance_path = provenance_path or output_dir / "source-provenance.json"
    provenance = json.loads(provenance_path.read_text()) if provenance_path.is_file() else {"assets": []}
    source_items = provenance.get("assets", [])
    assert len({item["id"] for item in source_items}) == len(source_items), "duplicate provenance IDs"
    source_records = {item["id"]: item for item in source_items}
    assets = []
    images: dict[str, Image.Image] = {}
    hashes: dict[str, str] = {}
    cardinal_facing = {"up", "down", "left", "right"}
    for spec in contract["assets"]:
        path = output_dir / "assets" / f"{spec['id']}.png"
        if not path.is_file():
            raise AssertionError(f"missing processed asset: {spec['id']}")
        with Image.open(path) as raw:
            image = raw.convert("RGBA")
        assert image.size == tuple(spec["size"]), f"{spec['id']} dimensions disagree with contract"
        images[spec["id"]] = image
        alpha = image.getchannel("A")
        alpha_values = set(alpha.get_flattened_data())
        box = alpha.getbbox()
        item_qa = spec.get("qa", {})
        visual_semantics = spec.get("visual_semantics") or {}
        if visual_semantics.get("kind") == "chair":
            seat = spec.get("seat", {})
            facing = seat.get("facing")
            assert facing in cardinal_facing, f"{spec['id']} chair requires cardinal seat.facing"
        expected_axis = item_qa.get("expected_axis")
        opaque_width = box[2] - box[0] if box else 0
        opaque_height = box[3] - box[1] if box else 0
        axis_tolerance = int(item_qa.get("axis_tolerance", 0))
        if expected_axis == "horizontal":
            assert opaque_width > opaque_height + axis_tolerance, f"{spec['id']} expected horizontal painted axis"
        elif expected_axis == "vertical":
            assert opaque_height > opaque_width + axis_tolerance, f"{spec['id']} expected vertical painted axis"
        elif expected_axis == "square":
            assert abs(opaque_width - opaque_height) <= axis_tolerance, f"{spec['id']} expected square painted bounds"
        elif expected_axis is not None:
            raise AssertionError(f"{spec['id']} has unsupported expected_axis: {expected_axis}")
        min_ratio = item_qa.get("min_bbox_ratio")
        bbox_ratio = _ratio(box, image.size)
        if min_ratio is not None:
            assert bbox_ratio >= min_ratio, f"{spec['id']} opaque bbox ratio below minimum"
        if item_qa.get("binary_alpha", qa.get("binary_alpha", False)):
            assert alpha_values <= {0, 255}, f"{spec['id']} contains partial alpha"
        source = source_records.get(spec["id"])
        if qa.get("require_provenance", False):
            assert source, f"{spec['id']} missing provenance"
        if source:
            allowed_transforms = item_qa.get("allowed_transforms", qa.get("allowed_transforms", ["none"]))
            assert source.get("transform") in allowed_transforms, f"{spec['id']} has disallowed transform"
            digest = source.get("sha256")
            assert isinstance(digest, str) and len(digest) == 64, f"{spec['id']} has invalid source hash"
            source_path = Path(source.get("source", ""))
            if source_path.is_file():
                assert hashlib.sha256(source_path.read_bytes()).hexdigest() == digest, f"{spec['id']} source hash disagrees"
            hashes[spec["id"]] = digest
        expected_box = item_qa.get("expected_opaque_bbox")
        if expected_box is not None:
            assert list(box) == expected_box, f"{spec['id']} opaque bbox disagrees"
        assets.append({"id": spec["id"], "size": list(image.size), "opaque_bbox": list(box) if box else None,
                       "bbox_ratio": bbox_ratio, "alpha_values": sorted(alpha_values),
                       "opaque_colors": len({pixel[:3] for pixel in image.get_flattened_data() if pixel[3]}),
                       "source_sha256": source.get("sha256") if source else None,
                       "transform": source.get("transform") if source else None,
                       "visual_semantics": visual_semantics or None,
                       "visual_orientation_certified": False if visual_semantics.get("kind") == "chair" else None,
                       "geometry_group": item_qa.get("geometry_group"),
                       "independent_variants_group": item_qa.get("independent_variants_group")})
    if qa.get("unique_source_hashes", False):
        assert len(set(hashes.values())) == len(hashes), "source hashes must be unique"
    groups: dict[str, list[dict]] = {}
    for item in assets:
        if item["geometry_group"]:
            groups.setdefault(item["geometry_group"], []).append(item)
    for group, members in groups.items():
        tolerance = max(
            int(next(spec for spec in contract["assets"] if spec["id"] == item["id"]).get("qa", {}).get("geometry_tolerance", 0))
            for item in members
        )
        reference = members[0]["opaque_bbox"]
        assert reference, f"geometry group {group} contains an empty asset"
        reference_size = (reference[2] - reference[0], reference[3] - reference[1])
        for item in members[1:]:
            box = item["opaque_bbox"]
            assert box, f"geometry group {group} contains an empty asset"
            size = (box[2] - box[0], box[3] - box[1])
            assert all(abs(a - b) <= tolerance for a, b in zip(size, reference_size)), (
                f"geometry group {group} has inconsistent painted bounds"
            )
    variant_groups: dict[str, list[str]] = {}
    for item in assets:
        if item["independent_variants_group"]:
            variant_groups.setdefault(item["independent_variants_group"], []).append(item["id"])
    for group, members in variant_groups.items():
        for index, source_id in enumerate(members):
            source_image = images[source_id]
            derivatives = [
                source_image,
                source_image.transpose(Image.Transpose.ROTATE_90),
                source_image.transpose(Image.Transpose.ROTATE_270),
                source_image.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
                source_image.transpose(Image.Transpose.FLIP_TOP_BOTTOM),
            ]
            for target_id in members[index + 1:]:
                target = images[target_id]
                assert not any(
                    candidate.size == target.size and candidate.tobytes() == target.tobytes()
                    for candidate in derivatives
                ), f"{target_id} is a duplicate or raster derivative of {source_id} in {group}"
    palette_limit = qa.get("palette_limit")
    palette = {
        pixel[:3]
        for image in images.values()
        for pixel in image.get_flattened_data()
        if pixel[3]
    }
    if palette_limit is not None:
        assert len(palette) <= palette_limit, "package palette exceeds limit"
    report = {"format": "tileforge-qa-v1", "status": "PASS", "palette_colors": len(palette), "assets": assets,
              "checks": ["provenance", "unique-source-hashes", "allowed-transforms", "binary-alpha", "palette-limit", "asset-geometry"]}
    (output_dir / "qa-report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--provenance", type=Path)
    args = parser.parse_args()
    print(f"quality validated {len(validate(args.contract, args.outdir, args.provenance)['assets'])} assets")


if __name__ == "__main__":
    main()
