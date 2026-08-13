"""Contract-driven source provenance, quality, and visual evidence checks."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prepare_sources import prepare  # noqa: E402
from process_sheet import process  # noqa: E402
from render_qa_surface import render  # noqa: E402
from validate_evidence import validate as validate_evidence  # noqa: E402
from validate_quality import validate as validate_quality  # noqa: E402


def contract(path: Path) -> Path:
    payload = {
        "format": "tileforge-contract-v1", "name": "quality-proof", "style_profile": "proof", "tile_size": 16,
        "source": {"cell_width": 32, "cell_height": 32, "columns": 2, "rows": 1, "chroma_key": "#ff00ff"},
        "required_orientation_sets": [],
        "qa": {"require_provenance": True, "unique_source_hashes": True, "allowed_transforms": ["none"], "binary_alpha": True, "palette_limit": 4},
        "assets": [
            {"id": "table-left", "family": "furniture", "cell": [0, 0], "size": [16, 16], "anchor": [8, 15], "collision": [0, 0, 0, 0], "layer": "object", "transparent": True, "qa": {"expected_axis": "horizontal", "min_bbox_ratio": 0.1, "geometry_group": "table", "independent_variants_group": "table"}},
            {"id": "table-right", "family": "furniture", "cell": [1, 0], "size": [16, 16], "anchor": [8, 15], "collision": [0, 0, 0, 0], "layer": "object", "transparent": True, "qa": {"expected_axis": "horizontal", "min_bbox_ratio": 0.1, "geometry_group": "table", "independent_variants_group": "table"}}
        ]
    }
    path.write_text(json.dumps(payload))
    return path


def source(path: Path, color: tuple[int, int, int]) -> Path:
    image = Image.new("RGBA", (24, 10), (0, 0, 0, 0))
    for x in range(24):
        shade = tuple(min(255, channel + (x % 6) * 3) for channel in color)
        for y in range(10):
            image.putpixel((x, y), (*shade, 255))
    image.save(path)
    return path


def main() -> None:
    with tempfile.TemporaryDirectory() as raw:
        directory = Path(raw); contract_path = contract(directory / "contract.json")
        sources = {"table-left": source(directory / "left.png", (70, 50, 30)), "table-right": source(directory / "right.png", (100, 70, 40))}
        oversized = source(directory / "oversized.png", (120, 80, 50))
        Image.open(oversized).resize((64, 40), Image.Resampling.NEAREST).save(oversized)
        try:
            prepare(contract_path, {**sources, "table-left": oversized}, directory / "rejected-sheets")
        except ValueError as error:
            assert "source_fit=contain-nearest" in str(error)
        else:
            raise AssertionError("source preparation silently resized an oversized image")
        resize_payload = json.loads(contract_path.read_text())
        resize_payload["qa"]["allowed_transforms"].append("contain-nearest")
        resize_payload["assets"][0]["processing"] = {"source_fit": "contain-nearest"}
        resize_contract = directory / "resize-contract.json"
        resize_contract.write_text(json.dumps(resize_payload))
        resized = prepare(resize_contract, {**sources, "table-left": oversized}, directory / "resized-sheets")
        assert resized["assets"][0]["transform"] == "contain-nearest"
        undersized = source(directory / "undersized.png", (130, 90, 60))
        Image.open(undersized).resize((8, 4), Image.Resampling.NEAREST).save(undersized)
        upscaled_dir = directory / "upscaled-sheets"
        prepare(resize_contract, {**sources, "table-left": undersized}, upscaled_dir)
        cell = Image.open(upscaled_dir / "furniture.png").convert("RGB").crop((0, 0, 32, 32))
        painted = [(x, y) for y in range(32) for x in range(32) if cell.getpixel((x, y)) != (255, 0, 255)]
        assert max(x for x, _ in painted) - min(x for x, _ in painted) + 1 > 8
        sheets = directory / "sheets"; prepare(contract_path, sources, sheets)
        output = directory / "output"; process(
            contract_path, {"furniture": sheets / "furniture.png"}, output, tolerance=128, palette=4
        )
        (output / "source-provenance.json").write_bytes((sheets / "source-provenance.json").read_bytes())
        quality = validate_quality(contract_path, output)
        assert quality["status"] == "PASS" and len(quality["assets"]) == 2 and quality["palette_colors"] <= 4
        null_semantics_payload = json.loads(contract_path.read_text())
        null_semantics_payload["assets"][0]["visual_semantics"] = None
        null_semantics_contract = directory / "null-semantics-contract.json"
        null_semantics_contract.write_text(json.dumps(null_semantics_payload))
        null_semantics_quality = validate_quality(null_semantics_contract, output)
        assert null_semantics_quality["status"] == "PASS"
        assert null_semantics_quality["assets"][0]["visual_semantics"] is None
        semantics_payload = json.loads(contract_path.read_text())
        semantics_payload["assets"][0]["seat"] = {"facing": "up", "anchor": [8, 8]}
        semantics_payload["assets"][0]["visual_semantics"] = {
            "kind": "chair",
            "expected_backrest_side": "north",
            "backrest_attachment": "rear-seat-edge",
        }
        semantics_contract = directory / "semantics-contract.json"
        semantics_contract.write_text(json.dumps(semantics_payload))
        chair_quality = validate_quality(semantics_contract, output)
        assert chair_quality["status"] == "PASS"
        assert chair_quality["assets"][0]["visual_semantics"] == semantics_payload["assets"][0]["visual_semantics"]
        assert chair_quality["assets"][0]["visual_orientation_certified"] is False
        semantics_payload["assets"][0]["seat"]["facing"] = "diagonal"
        semantics_contract.write_text(json.dumps(semantics_payload))
        try:
            validate_quality(semantics_contract, output)
        except AssertionError as error:
            assert "cardinal seat.facing" in str(error)
        else:
            raise AssertionError("quality gate accepted a chair without cardinal gameplay-facing metadata")
        right_path = output / "assets" / "table-right.png"
        original_right = right_path.read_bytes()
        right_path.write_bytes((output / "assets" / "table-left.png").read_bytes())
        try:
            validate_quality(contract_path, output)
        except AssertionError as error:
            assert "duplicate or raster derivative" in str(error)
        else:
            raise AssertionError("quality gate accepted a copied directional variant")
        right_path.write_bytes(original_right)
        evidence = directory / "evidence"; render(contract_path, output, evidence)
        assert Image.open(evidence / "assets-native.png").width < Image.open(evidence / "assets-preview.png").width
        (evidence / "visual-review.json").write_text(json.dumps({"independent": True, "reviewer": "cold-review", "counts": {"Critical": 0, "Important": 0, "Minor": 0}}))
        evidence_report = validate_evidence(evidence)
        assert evidence_report["status"] == "PASS" and evidence_report["images"][0]["sha256"]
        accepted_contextual_check = {
            "asset_id": "chair-near-table",
            "kind": "contextual-orientation",
            "accepted_calibration_map": "calibration-map.png",
            "station_relationship": "chair pulled from the near table edge",
            "user_accepted": True,
            "isolated_after_acceptance": True,
            "recreated_relationship": "chair pulled from the near table edge",
            "verdict": "accepted",
        }
        contextual_review = {
            "independent": True,
            "reviewer": "cold-review",
            "counts": {"Critical": 0, "Important": 0, "Minor": 0},
            "semantic_checks": [accepted_contextual_check],
        }
        reviewer_placeholder_review = {**contextual_review, "reviewer": "<reviewer-or-task-id>"}
        (evidence / "visual-review.json").write_text(json.dumps(reviewer_placeholder_review))
        try:
            validate_evidence(evidence)
        except AssertionError as error:
            assert "reviewer placeholder" in str(error)
        else:
            raise AssertionError("evidence gate accepted an unresolved reviewer placeholder")
        embedded_reviewer_placeholder_review = {**contextual_review, "reviewer": "reviewer <task-id>"}
        (evidence / "visual-review.json").write_text(json.dumps(embedded_reviewer_placeholder_review))
        try:
            validate_evidence(evidence)
        except AssertionError as error:
            assert "reviewer placeholder" in str(error)
        else:
            raise AssertionError("evidence gate accepted an embedded reviewer placeholder")
        asset_placeholder_review = {**contextual_review, "semantic_checks": [{
            **accepted_contextual_check,
            "asset_id": "<directional-furniture-id>",
        }]}
        (evidence / "visual-review.json").write_text(json.dumps(asset_placeholder_review))
        try:
            validate_evidence(evidence)
        except AssertionError as error:
            assert "asset ID placeholder" in str(error)
        else:
            raise AssertionError("evidence gate accepted an unresolved asset ID placeholder")
        embedded_relationship_placeholder_review = {**contextual_review, "semantic_checks": [{
            **accepted_contextual_check,
            "station_relationship": "chair <near-table-edge>",
        }]}
        (evidence / "visual-review.json").write_text(json.dumps(embedded_relationship_placeholder_review))
        try:
            validate_evidence(evidence)
        except AssertionError as error:
            assert "unresolved template placeholder" in str(error)
        else:
            raise AssertionError("evidence gate accepted an embedded relationship placeholder")
        template_review = json.loads((ROOT / "references" / "visual-review-template.json").read_text())
        (evidence / "visual-review.json").write_text(json.dumps(template_review))
        try:
            validate_evidence(evidence)
        except AssertionError as error:
            assert "reviewer placeholder" in str(error) or "user acceptance" in str(error)
        else:
            raise AssertionError("evidence gate accepted the untouched visual-review template")
        for invalid, message in [
            ({"user_accepted": False}, "user acceptance"),
            ({"isolated_after_acceptance": False}, "isolation after acceptance"),
            ({"accepted_calibration_map": ""}, "accepted calibration map"),
            ({"station_relationship": ""}, "station relationship"),
            ({"recreated_relationship": ""}, "recreated relationship"),
            ({"accepted_calibration_map": "<path-or-id>"}, "unresolved template placeholder"),
            ({"verdict": "not-reviewed"}, "accepted verdict"),
        ]:
            contextual_review["semantic_checks"] = [{**accepted_contextual_check, **invalid}]
            (evidence / "visual-review.json").write_text(json.dumps(contextual_review))
            try:
                validate_evidence(evidence)
            except AssertionError as error:
                assert message in str(error)
            else:
                raise AssertionError(f"evidence gate accepted contextual orientation without {message}")
        contextual_review["semantic_checks"] = [accepted_contextual_check]
        (evidence / "visual-review.json").write_text(json.dumps(contextual_review))
        assert validate_evidence(evidence)["status"] == "PASS"
        (evidence / "visual-review.json").write_text(json.dumps({"independent": True, "reviewer": "cold-review", "counts": {"Critical": 0, "Important": 1, "Minor": 0}}))
        try:
            validate_evidence(evidence)
        except AssertionError as error:
            assert "important" in str(error)
        else:
            raise AssertionError("evidence gate accepted an important finding")
    print("tileforge quality tests passed")


if __name__ == "__main__":
    main()
