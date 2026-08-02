#!/usr/bin/env python3
"""Offline contract tests for the repository-guide-v2 GitHub collector."""
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("github-capture.py")
SHA_A = "0123456789abcdef0123456789abcdef01234567"
SHA_B = "fedcba9876543210fedcba9876543210fedcba98"
SHA_COLLISION = "0123456fffffffffffffffffffffffffffffffff"


def load_module():
    spec = importlib.util.spec_from_file_location("github_capture", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GitHubCaptureContractTests(unittest.TestCase):
    """Each test protects an observable v2 guide or safety contract."""

    def run_cli(self, *args):
        return subprocess.run(["python3", str(SCRIPT), *args], text=True, capture_output=True)

    def guide_args(self, guide, out_dir, *, repository="acme/widget", commit=SHA_A, date="2026-08-02", source_refs=()):
        args = [
            "finalize", "--repository", repository, "--commit", commit,
            "--guide", str(guide), "--guide-by", "codex/gpt-5.6-terra",
            "--out-dir", str(out_dir), "--date", date,
        ]
        for source_ref in source_refs:
            args.extend(["--source-ref", source_ref])
        return args

    def make_guide(self, root):
        guide = root / "guide.md"
        guide.write_text(
            "## Purpose\n\nA widget service for test fixtures.\n\n"
            "## System\n\nThe CLI coordinates the local fixture store.\n\n"
            "## Use\n\nFollow the upstream setup instructions.\n\n"
            "## Constraints\n\nKeep credentials outside the repository.\n"
        )
        return guide

    def test_normalizes_only_github_repository_roots(self):
        for source in ("https://github.com/acme/widget.git", "https://github.com/acme/widget/", "acme/widget"):
            result = self.run_cli("normalize", source)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "acme/widget")
        for source in (
            "https://gitlab.com/acme/widget", "https://github.com/acme/widget/issues",
            "https://github.com/acme/widget?tab=readme", "https://github.com/acme/widget#readme",
            "https://user@github.com/acme/widget", "https://github.com:443/acme/widget",
        ):
            result = self.run_cli("normalize", source)
            self.assertNotEqual(result.returncode, 0, source)
            self.assertIn("GitHub repository", result.stderr)

    def test_finalize_writes_compact_v2_guide_with_provenance_and_source_references(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            guide = self.make_guide(root)
            out_dir = root / "raw" / "clips"
            result = self.run_cli(*self.guide_args(guide, out_dir, source_refs=("README.md", "docs/setup.md", "AGENTS.md")))
            self.assertEqual(result.returncode, 0, result.stderr)
            clip = Path(result.stdout.strip())
            text = clip.read_text()
            self.assertEqual(clip.name, "2026-08-02-github-acme-widget-0123456-guide-v2.md")
            self.assertIn("capture_format: repository-guide-v2", text)
            self.assertIn("repository: acme/widget", text)
            self.assertIn(f"commit: {SHA_A}", text)
            self.assertIn("## Purpose", text)
            self.assertIn("## System", text)
            self.assertIn("## Use", text)
            self.assertIn("## Constraints", text)
            self.assertIn("## Where to go deeper", text)
            self.assertIn("- `README.md`", text)
            self.assertIn("- `docs/setup.md`", text)
            self.assertNotIn("## Repository metadata", text)
            self.assertNotIn("## Bounded tree", text)
            self.assertNotIn("```", text)

    def test_finalize_dedupes_only_same_repository_commit_and_format(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            guide = self.make_guide(root)
            out_dir = root / "clips"
            args = self.guide_args(guide, out_dir, source_refs=("README.md",))
            first = self.run_cli(*args)
            self.assertEqual(first.returncode, 0, first.stderr)
            clip = Path(first.stdout.strip())
            second = self.run_cli(*self.guide_args(guide, out_dir, date="2026-08-03", source_refs=("README.md",)))
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(Path(second.stdout.strip()), clip)
            changed = self.run_cli(*self.guide_args(guide, out_dir, commit=SHA_B, source_refs=("README.md",)))
            self.assertEqual(changed.returncode, 0, changed.stderr)
            self.assertEqual(Path(changed.stdout.strip()).name, "2026-08-02-github-acme-widget-fedcba9-guide-v2.md")
            self.assertEqual(len(list(out_dir.glob("*.md"))), 2)

    def test_legacy_capture_does_not_dedupe_a_v2_guide(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            guide = self.make_guide(root)
            out_dir = root / "clips"
            out_dir.mkdir()
            (out_dir / "2026-08-02-github-acme-widget-0123456.md").write_text(
                f"---\nrepository: acme/widget\ncommit: {SHA_A}\n---\nlegacy\n"
            )
            result = self.run_cli(*self.guide_args(guide, out_dir, source_refs=("README.md",)))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((out_dir / "2026-08-02-github-acme-widget-0123456-guide-v2.md").exists())

    def test_rejects_blank_guide_and_unsafe_source_references_without_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            blank = root / "blank.md"
            blank.write_text("  \n")
            out_dir = root / "clips"
            result = self.run_cli(*self.guide_args(blank, out_dir))
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(out_dir.exists())
            guide = self.make_guide(root)
            for source_ref in (".env", "private.pem", "image.png", "../README.md"):
                with self.subTest(source_ref=source_ref):
                    result = self.run_cli(*self.guide_args(guide, out_dir, source_refs=(source_ref,)))
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("unsafe --source-ref", result.stderr)
                    self.assertFalse(out_dir.exists())

    def test_rejects_guide_missing_required_orientation_sections_without_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            guide = root / "incomplete.md"
            guide.write_text("## Purpose\n\nA widget service.\n")
            out_dir = root / "clips"
            result = self.run_cli(*self.guide_args(guide, out_dir, source_refs=("README.md",)))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("System", result.stderr)
            self.assertFalse(out_dir.exists())

    def test_rejects_extra_or_empty_level_two_guide_sections_without_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            out_dir = root / "clips"
            for name, content in {
                "extra": (
                    "## Purpose\n\nA widget service.\n\n## System\n\nA CLI.\n\n"
                    "## Use\n\nFollow setup.\n\n## Constraints\n\nNo secrets.\n\n"
                    "## Repository metadata\n\nDo not archive this.\n"
                ),
                "empty": (
                    "## Purpose\n\nA widget service.\n\n## System\n\n\n"
                    "## Use\n\nFollow setup.\n\n## Constraints\n\nNo secrets.\n"
                ),
            }.items():
                with self.subTest(name=name):
                    guide = root / f"{name}.md"
                    guide.write_text(content)
                    result = self.run_cli(*self.guide_args(guide, out_dir, source_refs=("README.md",)))
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(out_dir.exists())

    def test_rejects_missing_source_reference_without_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            guide = self.make_guide(root)
            out_dir = root / "clips"
            result = self.run_cli(*self.guide_args(guide, out_dir))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("at least one", result.stderr)
            self.assertFalse(out_dir.exists())

    def test_collect_uses_authenticated_gh_clone_and_rejects_symlink_source_ref(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            guide = self.make_guide(root)
            out_dir = root / "clips"
            calls = []

            def fake_run(command, cwd=None):
                calls.append(command)
                if command[:3] == ["gh", "repo", "clone"]:
                    repo_dir = Path(command[4])
                    repo_dir.mkdir()
                    (repo_dir / "README.md").write_text("readme")
                    return ""
                if command[:3] == ["git", "rev-parse", "HEAD"]:
                    return SHA_A + "\n"
                if command[:3] == ["git", "ls-tree", "-rl"]:
                    return f"120000 blob deadbeef 9\tREADME.md\n"
                if command[:3] == ["gh", "api", "repos/acme/widget"]:
                    return '{"default_branch": "main"}'
                return ""

            with mock.patch.object(module, "run", side_effect=fake_run):
                with self.assertRaisesRegex(module.CaptureError, "symlink"):
                    module.collect("acme/widget", ["README.md"], guide, "codex/gpt-5.6-terra", out_dir, "2026-08-02")
            self.assertIn(["gh", "auth", "status"], calls)
            self.assertTrue(any(call[:3] == ["gh", "repo", "clone"] for call in calls))
            self.assertFalse(out_dir.exists())

    def test_atomic_no_clobber_preserves_concurrent_v2_capture(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            guide = self.make_guide(root)
            out_dir = root / "clips"
            destination = out_dir / "2026-08-02-github-acme-widget-0123456-guide-v2.md"
            rival = f"---\nrepository: acme/widget\ncommit: {SHA_COLLISION}\ncapture_format: repository-guide-v2\n---\nrival\n"

            def concurrent_writer(*_args):
                out_dir.mkdir(parents=True, exist_ok=True)
                destination.write_text(rival)
                return None

            with mock.patch.object(module, "existing_capture", side_effect=concurrent_writer):
                with self.assertRaisesRegex(module.CaptureError, "seven-character SHA collision"):
                    module.finalize("acme/widget", SHA_A, guide, ["README.md"], out_dir, "2026-08-02", "codex/gpt-5.6-terra")
            self.assertEqual(destination.read_text(), rival)
            self.assertFalse(any(out_dir.glob("*.tmp")))


if __name__ == "__main__":
    unittest.main()
