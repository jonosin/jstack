#!/usr/bin/env python3
"""Behavior checks for the satellite-to-brain docs-index link workflow."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from shutil import copy2
from pathlib import Path


SCRIPT = Path(__file__).with_name("docs_index.py")
NEW_VENTURE = Path(__file__).with_name("new_venture.py")
NEW_BUILD = Path(__file__).with_name("new_build.py")
SB = Path.home() / "second-brain" / "tools" / "sb.py"


class BrainLinkTests(unittest.TestCase):
    def make_fixture(self, root: Path) -> tuple[Path, Path, Path]:
        ventures = root / "ventures"
        repo = ventures / "example-venture"
        docs = repo / "docs"
        docs.mkdir(parents=True)
        (docs / "index.md").write_text("# docs/ — file registry (generated)\n")
        brain = root / "second-brain"
        (brain / "wiki" / "personal" / "ventures").mkdir(parents=True)
        return repo, brain, brain / "wiki" / "personal" / "ventures" / "example-venture.docs-index"

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args], text=True, capture_output=True
        )

    def test_brain_link_creates_relative_symlink_and_lint_accepts_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, brain, link = self.make_fixture(Path(tmp))

            created = self.run_cli("brain-link", "--write", "--repo", str(repo), "--brain", str(brain))
            self.assertEqual(created.returncode, 0, created.stderr)
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.resolve(), (repo / "docs" / "index.md").resolve())
            self.assertFalse(link.readlink().is_absolute())

            checked = self.run_cli("brain-link-lint", "--repo", str(repo), "--brain", str(brain))
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

    def test_brain_link_lint_rejects_a_copied_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, brain, link = self.make_fixture(Path(tmp))
            link.write_text((repo / "docs" / "index.md").read_text())

            checked = self.run_cli("brain-link-lint", "--repo", str(repo), "--brain", str(brain))
            self.assertNotEqual(checked.returncode, 0)
            self.assertIn("must be a symlink", checked.stdout)

    def test_explicit_slug_overrides_human_readable_repo_name_everywhere(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, brain, _link = self.make_fixture(root)
            renamed_repo = repo.parent / "Fopus StudyWorld"
            repo.rename(renamed_repo)
            docs = renamed_repo / "docs"
            link = brain / "wiki" / "personal" / "builds" / "fopus-studyworld.docs-index"
            (brain / "wiki" / "personal" / "builds").mkdir()

            indexed = self.run_cli(
                "index", "--write", "--repo", str(renamed_repo), "--slug", "fopus-studyworld",
                "--satellite-kind", "build",
            )
            self.assertEqual(indexed.returncode, 0, indexed.stdout + indexed.stderr)
            output = (docs / "index.md").read_text()
            self.assertIn("builds/fopus-studyworld.docs-index", output)
            self.assertNotIn("builds/Fopus StudyWorld.docs-index", output)

            created = self.run_cli(
                "brain-link", "--write", "--repo", str(renamed_repo), "--slug", "fopus-studyworld",
                "--satellite-kind", "build", "--brain", str(brain),
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.resolve(), (docs / "index.md").resolve())

            checked = self.run_cli(
                "brain-link-lint", "--repo", str(renamed_repo), "--slug", "fopus-studyworld",
                "--satellite-kind", "build", "--brain", str(brain),
            )
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

    def test_index_uses_strategy_as_canonical_and_preserves_legacy_zones(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, _brain, _link = self.make_fixture(Path(tmp))
            docs = repo / "docs"
            fixtures = {
                "strategy/2026-07-21-market-wedge.md": ("Market wedge", "accepted"),
                "build/2026-07-21-sync-architecture.md": ("Sync architecture", "draft"),
                "superpowers/adr/0001-legacy-routing.md": ("Legacy routing", "accepted"),
                "superpowers/specs/2026-07-01-legacy-plan.md": ("Legacy plan", "archived"),
            }
            for relative, (title, status) in fixtures.items():
                path = docs / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    f'---\ntitle: "{title}"\nsummary: "A durable artifact for test coverage."\n'
                    f"status: {status}\n---\n\n# {title}\n"
                )

            indexed = self.run_cli("index", "--write", "--repo", str(repo))
            self.assertEqual(indexed.returncode, 0, indexed.stdout + indexed.stderr)
            linted = self.run_cli("lint", "--repo", str(repo))
            self.assertEqual(linted.returncode, 0, linted.stdout + linted.stderr)
            output = (docs / "index.md").read_text()
            self.assertIn("## Strategy — `strategy/`", output)
            self.assertIn("## Legacy build material — `build/` (preserved)", output)
            self.assertIn("## Legacy planning material — `superpowers/` (preserved)", output)

    def test_legacy_docs_are_discoverable_without_blocking_canonical_lint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, _brain, _link = self.make_fixture(Path(tmp))
            docs = repo / "docs"
            strategy = docs / "strategy" / "2026-07-23-current-architecture.md"
            strategy.parent.mkdir(parents=True)
            strategy.write_text(
                '---\ntitle: "Current architecture"\nsummary: "The current architecture rationale."\n'
                "status: accepted\n---\n\n# Current architecture\n"
            )
            legacy = docs / "build" / "old-notes.md"
            legacy.parent.mkdir(parents=True)
            legacy.write_text("# Old notes\n\nHistorical material without frontmatter.\n")

            indexed = self.run_cli("index", "--write", "--repo", str(repo))
            self.assertEqual(indexed.returncode, 0, indexed.stdout + indexed.stderr)
            linted = self.run_cli("lint", "--repo", str(repo))
            self.assertEqual(linted.returncode, 0, linted.stdout + linted.stderr)
            self.assertIn("WARN build/old-notes.md", linted.stdout)

    def test_new_venture_scaffold_wires_the_brain_visible_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brain = root / "second-brain"
            (brain / "wiki" / "maps").mkdir(parents=True)
            (brain / "wiki" / "personal" / "ventures").mkdir(parents=True)
            (brain / "tools").mkdir()
            (brain / "AGENTS.md").write_text("# test brain\n")
            (brain / "wiki" / "index.md").write_text("# index\n")
            (brain / "wiki" / "log.md").write_text("# log\n")
            (brain / "wiki" / "maps" / "satellites.md").write_text(
                "| Satellite repo | Knowledge-home page | BRAIN.md | Generated decision index |\n"
                "|---|---|---|---|\n"
                "| `~/ventures/existing` | `wiki/personal/ventures/existing.md` | yes | — |\n"
            )
            copy2(SB, brain / "tools" / "sb.py")

            run = subprocess.run(
                [sys.executable, str(NEW_VENTURE), "--name", "Example Venture", "--slug",
                 "example-venture", "--desc", "Test venture.", "--ventures-base", str(root / "ventures"),
                 "--brain", str(brain), "--no-git"],
                text=True, capture_output=True,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            link = brain / "wiki" / "personal" / "ventures" / "example-venture.docs-index"
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.resolve(), (root / "ventures" / "example-venture" / "docs" / "index.md").resolve())
            docs = root / "ventures" / "example-venture" / "docs"
            self.assertTrue((docs / "strategy" / ".gitkeep").exists())
            self.assertFalse((docs / "build").exists())
            self.assertFalse((docs / "scratch").exists())
            self.assertFalse((docs / "superpowers").exists())

    def test_new_build_scaffold_wires_docs_layout_and_build_index_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brain = root / "second-brain"
            (brain / "wiki" / "maps").mkdir(parents=True)
            (brain / "wiki" / "personal" / "builds").mkdir(parents=True)
            (brain / "tools").mkdir()
            (brain / "AGENTS.md").write_text("# test brain\n")
            (brain / "wiki" / "index.md").write_text("# index\n")
            (brain / "wiki" / "log.md").write_text("# log\n")
            (brain / "wiki" / "maps" / "satellites.md").write_text(
                "| Satellite repo | Knowledge-home page | BRAIN.md | Generated decision index |\n"
                "|---|---|---|---|\n"
                "| `~/builds/existing` | `wiki/personal/builds/existing.md` | yes | — |\n"
            )
            copy2(SB, brain / "tools" / "sb.py")

            run = subprocess.run(
                [sys.executable, str(NEW_BUILD), "--name", "Example Build", "--slug",
                 "example-build", "--desc", "Test build.", "--builds-base", str(root / "builds"),
                 "--brain", str(brain), "--no-git"],
                text=True, capture_output=True,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            repo = root / "builds" / "example-build"
            docs = repo / "docs"
            link = brain / "wiki" / "personal" / "builds" / "example-build.docs-index"
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.resolve(), (docs / "index.md").resolve())
            self.assertTrue((docs / "strategy" / ".gitkeep").exists())
            self.assertFalse((docs / "build").exists())
            self.assertFalse((docs / "scratch").exists())
            self.assertTrue((repo / ".scratch" / ".gitkeep").exists())
            self.assertTrue((docs / "AGENTS.md").is_file())
            self.assertTrue((docs / "CLAUDE.md").is_symlink())
            self.assertFalse((docs / "superpowers").exists())
            indexed = self.run_cli("lint", "--repo", str(repo), "--satellite-kind", "build")
            self.assertEqual(indexed.returncode, 0, indexed.stdout + indexed.stderr)


if __name__ == "__main__":
    unittest.main()
