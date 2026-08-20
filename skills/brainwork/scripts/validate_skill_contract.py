"""Validate the brainwork document contract without touching the vault."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [ROOT / "SKILL.md", *sorted((ROOT / "references").glob("*.md"))]

# These patterns identify the retired ingest/source-card and private-library paths.
FORBIDDEN = (
    "ingest-runbook",
    "pending-raw-triage",
    "raw/clips",
    "raw/drops",
    "cache.keys()",
    "source card for every",
    "source-card-by-default",
    "graphify --wiki",
    "import graphify",
    "from graphify",
)


def numbered_steps_without_done_when(text: str) -> list[str]:
    lines = text.splitlines()
    failures: list[str] = []
    step_indexes = [
        index
        for index, line in enumerate(lines)
        if re.match(r"^\s*(?:\d+\.|\d+\))\s+", line)
    ]
    for position, index in enumerate(step_indexes):
        end = step_indexes[position + 1] if position + 1 < len(step_indexes) else len(lines)
        window = "\n".join(lines[index:end]).lower()
        if "done when:" not in window:
            failures.append(lines[index].strip())
    return failures


def validate() -> None:
    missing = [str(path) for path in DOCS if not path.exists()]
    assert not missing, f"missing owned documents: {missing}"
    for path in DOCS:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        assert not any(token in lowered for token in FORBIDDEN), f"legacy text in {path}"
        failures = numbered_steps_without_done_when(text)
        assert not failures, f"steps without adjacent Done when in {path}: {failures}"
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    compile_runbook = (ROOT / "references/compile-runbook.md").read_text(encoding="utf-8")
    assert "name: brainwork" in skill
    assert "description:" in skill
    frontmatter = skill.split("---", 2)[1].lower()
    assert "savetobrain" not in frontmatter
    assert "querybrain" not in frontmatter
    assert "wrapper-contract.md" in skill
    assert "compile-runbook.md" in skill
    assert "migration-runbook.md" in skill
    assert "maintenance-runbook.md" in skill
    normalized_compile = " ".join(compile_runbook.split())
    for required in (
        "Group related selected records",
        "60,000-token estimated input cap",
        "one fresh Luna/max extraction subagent for each group",
        "join and end one before starting the next",
        "one fresh Luna/max integration subagent",
        "main compile session reviews each group",
    ):
        assert required in normalized_compile, f"missing compile worker contract: {required}"
    print("brainwork skill contract passed")


if __name__ == "__main__":
    validate()
