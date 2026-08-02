#!/usr/bin/env python3
"""Fail-closed GitHub repository-guide-v2 collector for jstack-savetobrain."""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


MAX_SOURCE_REFS = 12
MAX_GUIDE_CHARS = 16_000
CAPTURE_FORMAT = "repository-guide-v2"
EXCLUDED_PARTS = {
    ".git", ".cache", ".gradle", ".mypy_cache", ".next", ".pytest_cache", ".tox",
    ".venv", "__pycache__", "build", "coverage", "dist", "node_modules", "out",
    "generated", "target", "tmp", "vendor", "venv",
}
SECRET_RE = re.compile(r"(^|/)(?:\.env(?:\..*)?|.*(?:credential|secret|password|token|key).*?)(?:$|/)", re.I)
SECRET_FILENAMES = {".netrc", ".npmrc", "id_rsa", "private.pem"}
BINARY_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip", ".gz", ".tar", ".7z", ".mp3", ".mp4", ".mov", ".woff", ".woff2", ".ttf", ".ico", ".exe", ".dylib", ".so"}


class CaptureError(RuntimeError):
    pass


def config_value(key, default):
    if os.environ.get(key):
        return os.environ[key]
    cfg = Path.home() / ".jstack" / "config.env"
    if cfg.exists():
        for line in cfg.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                name, value = line.split("=", 1)
                if name.strip() == key:
                    return value.strip().strip('"').strip("'")
    return default


def normalize_repository(source):
    source = source.strip()
    if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", source):
        return source
    parsed = urlparse(source)
    if parsed.scheme in {"http", "https"} and parsed.netloc.lower() == "github.com" and not parsed.query and not parsed.fragment:
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) == 2 and re.fullmatch(r"[A-Za-z0-9_.-]+", parts[0]) and re.fullmatch(r"[A-Za-z0-9_.-]+(?:\.git)?", parts[1]):
            return f"{parts[0]}/{parts[1].removesuffix('.git')}"
    raise CaptureError("source must be a GitHub repository URL or owner/repo slug")


def safe_path(relative):
    path = Path(relative)
    return (not path.is_absolute() and ".." not in path.parts and bool(path.name)
            and not any(part in EXCLUDED_PARTS for part in path.parts)
            and path.name.lower() not in SECRET_FILENAMES
            and not SECRET_RE.search(relative)
            and path.suffix.lower() not in BINARY_EXTENSIONS)


def run(command, cwd=None):
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        raise CaptureError(f"command failed: {' '.join(command[:3])}: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout


def parse_source_ref(value):
    path, separator, description = value.partition("::")
    path = path.strip()
    if not safe_path(path):
        raise CaptureError(f"unsafe --source-ref path: {path}")
    description = description.strip() if separator else "Upstream reference selected for this guide."
    if not description or "\n" in description or len(description) > 300:
        raise CaptureError("--source-ref description must be one nonblank line of at most 300 characters")
    return path, description


def source_refs(values):
    if not values:
        raise CaptureError("at least one --source-ref is required")
    if len(values) > MAX_SOURCE_REFS:
        raise CaptureError(f"at most {MAX_SOURCE_REFS} --source-ref values are allowed")
    refs = [parse_source_ref(value) for value in values]
    if len({path for path, _ in refs}) != len(refs):
        raise CaptureError("--source-ref paths must be unique")
    return refs


def tree_modes(repo_dir):
    modes = {}
    for line in run(["git", "ls-tree", "-rl", "HEAD"], cwd=repo_dir).splitlines():
        if "\t" not in line:
            continue
        descriptor, path = line.split("\t", 1)
        bits = descriptor.split()
        if len(bits) >= 2:
            modes[path] = bits[0]
    return modes


def validate_checked_out_refs(repo_dir, refs):
    modes = tree_modes(repo_dir)
    for path, _ in refs:
        target = repo_dir / path
        if modes.get(path) == "120000" or target.is_symlink():
            raise CaptureError(f"source reference is a symlink: {path}")
        if not target.is_file():
            raise CaptureError(f"source reference is missing or not a regular file: {path}")


def collect(repository, source_ref_values, guide, guide_by, out_dir, collected):
    repository = normalize_repository(repository)
    refs = source_refs(source_ref_values)
    if not shutil.which("gh"):
        raise CaptureError("gh CLI is required")
    run(["gh", "auth", "status"])
    with tempfile.TemporaryDirectory(prefix="jstack-github-") as temp:
        repo_dir = Path(temp) / "repo"
        run(["gh", "repo", "clone", repository, str(repo_dir), "--", "--depth", "1"])
        commit = run(["git", "rev-parse", "HEAD"], cwd=repo_dir).strip()
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise CaptureError("clone did not resolve a full commit SHA")
        validate_checked_out_refs(repo_dir, refs)
        return finalize(repository, commit, guide, source_ref_values, out_dir, collected, guide_by)


def yaml_quote(value):
    return json.dumps(str(value), ensure_ascii=False)


def frontmatter_scalars(path):
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    values = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        raw_value = raw_value.strip()
        if raw_value.startswith('"'):
            try:
                values[key.strip()] = json.loads(raw_value)
                continue
            except json.JSONDecodeError:
                pass
        values[key.strip()] = raw_value
    return values


def existing_capture(out_dir, repository, commit):
    if not out_dir.is_dir():
        return None
    for candidate in sorted(out_dir.glob("*-github-*-guide-v2.md")):
        provenance = frontmatter_scalars(candidate)
        if (provenance.get("repository") == repository and provenance.get("commit") == commit
                and provenance.get("capture_format") == CAPTURE_FORMAT):
            return candidate
    return None


def guide_text(guide):
    path = Path(guide)
    if not path.is_file() or path.is_symlink():
        raise CaptureError("guide must be a real readable file")
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise CaptureError(f"invalid guide: {error}") from error
    if not content.strip() or not re.search(r"^#{1,6}\s+\S", content, re.MULTILINE):
        raise CaptureError("guide must be nonblank and contain at least one Markdown section")
    if len(content) > MAX_GUIDE_CHARS:
        raise CaptureError(f"guide exceeds compact {MAX_GUIDE_CHARS}-character limit")
    if "```" in content:
        raise CaptureError("guide must not contain fenced code blocks")
    required = ("Purpose", "System", "Use", "Constraints")
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", content, re.MULTILINE))
    headings = [match.group(1) for match in matches]
    if headings != list(required):
        raise CaptureError("guide must contain exactly these level-two sections: " + ", ".join(required))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        body = re.sub(r"^#{1,6}\s+.*$", "", content[match.end():end], flags=re.MULTILINE).strip()
        if not body:
            raise CaptureError(f"guide section {match.group(1)} must contain nonblank prose or a list")
    return content.rstrip()


def finalize(repository, commit, guide, source_ref_values, out_dir, collected, guide_by):
    repository = normalize_repository(repository)
    if not re.fullmatch(r"[0-9a-fA-F]{40}", commit):
        raise CaptureError("commit must be exactly one 40-character hexadecimal SHA")
    if not guide_by.strip():
        raise CaptureError("--guide-by must identify the actual harness/model")
    refs = source_refs(source_ref_values)
    content_guide = guide_text(guide)
    out = Path(out_dir)
    filename = f"{collected}-github-{repository.replace('/', '-')}-{commit[:7]}-guide-v2.md"
    destination = out / filename
    if destination.exists():
        provenance = frontmatter_scalars(destination)
        if (provenance.get("repository") == repository and provenance.get("commit") == commit
                and provenance.get("capture_format") == CAPTURE_FORMAT):
            return destination
        raise CaptureError(f"seven-character SHA collision or provenance mismatch at existing destination: {destination}")
    prior_capture = existing_capture(out, repository, commit)
    if prior_capture:
        return prior_capture
    parts = [
        "---", f"title: {yaml_quote('GitHub repository guide: ' + repository)}",
        f"source: {yaml_quote('https://github.com/' + repository)}", f"collected: {collected}",
        "tags: [github, repository]", "source_type: github-repository",
        f"capture_format: {CAPTURE_FORMAT}", f"repository: {repository}", f"commit: {commit}",
        f"guide_by: {yaml_quote(guide_by)}", "---\n",
        f"# Repository guide: {repository}\n", content_guide + "\n", "## Where to go deeper\n",
    ]
    for path, description in refs:
        parts.append(f"- `{path}` — {description}")
    content = "\n".join(parts) + "\n"
    out_existed, temporary = out.exists(), None
    try:
        out.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=out, prefix=f".{filename}.", suffix=".tmp", delete=False) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.chmod(temporary, 0o644)
        try:
            os.link(temporary, destination)
        except FileExistsError as error:
            provenance = frontmatter_scalars(destination)
            if (provenance.get("repository") == repository and provenance.get("commit") == commit
                    and provenance.get("capture_format") == CAPTURE_FORMAT):
                return destination
            raise CaptureError(f"seven-character SHA collision or provenance mismatch at existing destination: {destination}") from error
    except OSError as error:
        raise CaptureError(f"could not write capture: {error}") from error
    finally:
        try:
            if temporary is not None and temporary.exists():
                temporary.unlink()
            if not out_existed and out.is_dir() and not any(out.iterdir()):
                out.rmdir()
        except OSError:
            pass
    return destination


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Capture a GitHub repository as an immutable compact guide")
    commands = parser.add_subparsers(dest="command", required=True)
    normalize = commands.add_parser("normalize")
    normalize.add_argument("source")
    for name in ("collect", "finalize"):
        command = commands.add_parser(name)
        command.add_argument("--repository", required=True)
        command.add_argument("--commit")
        command.add_argument("--guide", required=True, help="Agent-authored compact repository guide")
        command.add_argument("--guide-by", required=True, help="Actual harness/model producing the guide")
        command.add_argument("--source-ref", action="append", default=[], help="path :: one-line description")
        command.add_argument("--out-dir", default=None)
        command.add_argument("--date", dest="collected", default=date.today().isoformat())
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        if args.command == "normalize":
            print(normalize_repository(args.source))
            return 0
        out_dir = args.out_dir or str(Path(config_value("SECOND_BRAIN_PATH", "~/second-brain")).expanduser() / "raw" / "clips")
        if args.command == "collect":
            result = collect(args.repository, args.source_ref, args.guide, args.guide_by, out_dir, args.collected)
        else:
            if not args.commit:
                raise CaptureError("finalize requires --commit")
            result = finalize(args.repository, args.commit, args.guide, args.source_ref, out_dir, args.collected, args.guide_by)
        print(result)
        return 0
    except CaptureError as error:
        print(f"github capture failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
