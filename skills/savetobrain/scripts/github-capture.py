#!/usr/bin/env python3
"""Fail-closed GitHub repository-guide-v2 collector for savetobrain."""
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
    if parsed.scheme == "https" and parsed.netloc.lower() == "github.com" and not parsed.query and not parsed.fragment:
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
    if not path.isprintable() or "\r" in path or "\n" in path or not safe_path(path):
        raise CaptureError(f"unsafe --source-ref path: {path}")
    description = description.strip() if separator else "Upstream reference selected for this guide."
    if not description or not description.isprintable() or "\r" in description or "\n" in description or len(description) > 300:
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
            modes[path] = (bits[0], bits[1])
    return modes


def validate_checked_out_refs(repo_dir, refs):
    modes = tree_modes(repo_dir)
    for path, _ in refs:
        target = repo_dir / path
        parts = Path(path).parts
        parents = [str(Path(*parts[:index])) for index in range(1, len(parts))]
        if any(modes.get(parent, (None, None))[0] == "120000" or (repo_dir / parent).is_symlink() for parent in parents):
            raise CaptureError(f"source reference traverses a tracked symlink: {path}")
        mode, object_type = modes.get(path, (None, None))
        if mode == "120000" or target.is_symlink():
            raise CaptureError(f"source reference is a symlink: {path}")
        if (mode, object_type) not in {("100644", "blob"), ("100755", "blob")}:
            raise CaptureError(f"source reference is not an exact tracked regular blob: {path}")
        if not target.is_file():
            raise CaptureError(f"source reference is missing or not a regular file: {path}")


def validate_collected(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise CaptureError("--date must be a valid YYYY-MM-DD date")
    try:
        date.fromisoformat(value)
    except ValueError as error:
        raise CaptureError("--date must be a valid YYYY-MM-DD date") from error


def validate_printable_line(value, option, max_chars):
    if not value.strip() or len(value) > max_chars or not value.isprintable() or "\r" in value or "\n" in value:
        raise CaptureError(f"{option} must be one printable nonblank line of at most {max_chars} characters")


def collect(repository, source_ref_values, guide, guide_by, out_dir, collected, prepared):
    repository = normalize_repository(repository)
    validate_collected(collected)
    validate_printable_line(guide_by, "--guide-by", 120)
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
        return finalize(repository, commit, guide, source_ref_values, out_dir, collected, guide_by, prepared)


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


def prepared_header(value, target):
    """Return the exact fixed raw-v2 header authorized for one target."""
    try:
        prepared = json.loads(Path(value).read_text(encoding="utf-8")) if Path(value).is_file() else json.loads(value)
    except (OSError, json.JSONDecodeError) as error:
        raise CaptureError(f"invalid --prepared JSON: {error}") from error
    required = ("schema", "id", "title", "captured", "source_type", "source", "role")
    frontmatter = prepared.get("frontmatter") if isinstance(prepared, dict) else None
    if (not isinstance(frontmatter, dict) or set(frontmatter) != set(required)
            or prepared.get("raw_id") != frontmatter.get("id")
            or prepared.get("target") != target
            or frontmatter.get("schema") != "sb.raw/v2"
            or frontmatter.get("source_type") != "github"
            or frontmatter.get("source") != prepared.get("normalized_source")):
        raise CaptureError("--prepared must authorize this GitHub raw-v2 target")
    return "---\n" + "\n".join(f"{key}: {yaml_quote(frontmatter[key])}" for key in required) + "\n---\n"


def existing_capture(out_dir, repository, commit):
    if not out_dir.is_dir():
        return None
    for candidate in sorted(out_dir.glob("*-github-*-guide-v2.md")):
        text = candidate.read_text(encoding="utf-8", errors="replace")
        if (re.search(rf"^Repository: {re.escape(repository)}$", text, re.MULTILINE)
                and re.search(rf"^Commit: {re.escape(commit)}$", text, re.MULTILINE)
                and f"Capture format: {CAPTURE_FORMAT}" in text):
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
    if re.search(r"^(?: {4}|\t)\S", content, re.MULTILINE):
        raise CaptureError("guide must not contain indented code blocks")
    required = ("Purpose", "System", "Use", "Constraints")
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", content, re.MULTILINE))
    headings = [match.group(1) for match in matches]
    if headings != list(required):
        raise CaptureError("guide must contain exactly these level-two sections: " + ", ".join(required))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        section = content[match.end():end]
        body = re.sub(r"^#{1,6}\s+.*$", "", section, flags=re.MULTILINE).strip()
        if not body:
            raise CaptureError(f"guide section {match.group(1)} must contain nonblank prose or a list")
        first_payload = next((line.strip() for line in section.splitlines() if line.strip()), "")
        if first_payload.startswith(("{", "[")):
            raise CaptureError(f"guide section {match.group(1)} must not contain archive-shaped JSON payloads")
        for candidate in re.finditer(r"^[ \t]*[\[{]", section, re.MULTILINE):
            try:
                json.JSONDecoder().raw_decode(section[candidate.start():].lstrip())
            except json.JSONDecodeError:
                continue
            raise CaptureError(f"guide section {match.group(1)} must not contain archive-shaped JSON payloads")
    return content.rstrip()


def finalize(repository, commit, guide, source_ref_values, out_dir, collected, guide_by, prepared):
    repository = normalize_repository(repository)
    validate_collected(collected)
    if not re.fullmatch(r"[0-9a-fA-F]{40}", commit):
        raise CaptureError("commit must be exactly one 40-character hexadecimal SHA")
    validate_printable_line(guide_by, "--guide-by", 120)
    refs = source_refs(source_ref_values)
    content_guide = guide_text(guide)
    out = Path(out_dir)
    filename = f"{collected}-github-{repository.replace('/', '-')}-{commit[:7]}-guide-v2.md"
    destination = out / filename
    header = prepared_header(prepared, f"raw/{filename}")
    prior_capture = existing_capture(out, repository, commit)
    if prior_capture:
        return prior_capture
    if destination.exists():
        raise CaptureError(f"seven-character SHA collision or provenance mismatch at existing destination: {destination}")
    parts = [
        header, f"# Repository guide: {repository}\n",
        f"Repository: {repository}\n", f"Commit: {commit}\n",
        f"Capture format: {CAPTURE_FORMAT}\n", f"Guide by: {guide_by}\n\n",
        content_guide + "\n", "## Where to go deeper\n",
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
            if existing_capture(out, repository, commit) == destination:
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
        command.add_argument("--prepared", required=True, help="capture prepare JSON object or file")
        command.add_argument("--out-dir", default=None)
        command.add_argument("--date", dest="collected", default=date.today().isoformat())
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        if args.command == "normalize":
            print(normalize_repository(args.source))
            return 0
        out_dir = args.out_dir or str(Path(config_value("SECOND_BRAIN_PATH", "~/second-brain")).expanduser() / "raw")
        if args.command == "collect":
            result = collect(args.repository, args.source_ref, args.guide, args.guide_by, out_dir, args.collected, args.prepared)
        else:
            if not args.commit:
                raise CaptureError("finalize requires --commit")
            result = finalize(args.repository, args.commit, args.guide, args.source_ref, out_dir, args.collected, args.guide_by, args.prepared)
        print(result)
        return 0
    except CaptureError as error:
        print(f"github capture failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
