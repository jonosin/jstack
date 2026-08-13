#!/usr/bin/env python3
"""Extract a clean user/assistant transcript from a Claude Code JSONL session."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
from typing import Any


def project_hash_from_path(dir_path: str | pathlib.Path) -> str:
    """Convert a filesystem path to a Claude Code project hash."""
    abs_path = str(pathlib.Path(dir_path).resolve())
    return abs_path.replace("/", "-")


CLAUDE_PROJECTS_ROOT = pathlib.Path.home() / ".claude" / "projects"


def find_claude_project_dir(dir_path: str | None = None) -> pathlib.Path | None:
    """Find the Claude Code project directory for a given working directory."""
    if dir_path is None:
        dir_path = os.getcwd()
    hash_name = project_hash_from_path(dir_path)
    candidate = CLAUDE_PROJECTS_ROOT / hash_name
    if candidate.exists():
        return candidate
    # Try partial match — Claude Code sometimes uses a variant hash
    for child in CLAUDE_PROJECTS_ROOT.iterdir():
        if child.is_dir() and hash_name in child.name:
            return child
    return None


def find_session_jsonl(session_id: str) -> pathlib.Path | None:
    """Search ALL Claude project directories for a session JSONL file.
    
    This is a global fallback that doesn't depend on CWD or project-dir mapping.
    """
    if not CLAUDE_PROJECTS_ROOT.exists():
        return None
    for project_dir in sorted(CLAUDE_PROJECTS_ROOT.iterdir(), reverse=True):
        if not project_dir.is_dir():
            continue
        candidate = project_dir / f"{session_id}.jsonl"
        if candidate.exists():
            return candidate
    return None


def resolve_session_jsonl(
    session_id: str,
    claude_projects_dir: pathlib.Path | None,
    project_dir: pathlib.Path | None = None,
) -> pathlib.Path | None:
    """Try multiple strategies to resolve a session JSONL path.
    
    Strategy order:
    1. Explicit --claude-projects-dir (direct file or subdirectory search)
    2. --project-dir or CWD-derived project dir via find_claude_project_dir
    3. Global scan of all ~/.claude/projects/* directories
    """
    # Strategy 1: explicit --claude-projects-dir
    if claude_projects_dir is not None:
        direct = claude_projects_dir / f"{session_id}.jsonl"
        if direct.exists():
            return direct
        # Maybe they passed the root projects/ dir — search subdirectories
        try:
            for child in sorted(claude_projects_dir.iterdir(), reverse=True):
                if not child.is_dir():
                    continue
                candidate = child / f"{session_id}.jsonl"
                if candidate.exists():
                    return candidate
        except PermissionError:
            pass

    # Strategy 2: derive from --project-dir or CWD
    resolved_project = find_claude_project_dir(str(project_dir) if project_dir else None)
    if resolved_project is not None:
        candidate = resolved_project / f"{session_id}.jsonl"
        if candidate.exists():
            return candidate

    # Strategy 3: global scan of all project directories
    return find_session_jsonl(session_id)


NOISE_PREFIXES = (
    "<command-name>",
    "<command-message>",
    "<command-args>",
    "<local-command-caveat>",
    "<local-command-stdout>",
    "<task-notification>",
)


NOISE_EXACT = {
    "[Request interrupted by user]",
}


ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def normalize_text(text: str) -> str:
    lines = [line.rstrip() for line in strip_ansi(text).splitlines()]
    return "\n".join(lines).strip()


def is_noise_text(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if stripped in NOISE_EXACT:
        return True
    return any(stripped.startswith(prefix) for prefix in NOISE_PREFIXES)


def extract_text(content: Any) -> str:
    if isinstance(content, str):
        return normalize_text(content)

    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for block in content:
        if isinstance(block, str):
            text = normalize_text(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            text = normalize_text(block.get("text", ""))
        else:
            text = ""

        if text:
            parts.append(text)

    return normalize_text("\n\n".join(parts))


def parse_entries(path: pathlib.Path) -> tuple[list[dict[str, str]], dict[str, int]]:
    entries: list[dict[str, str]] = []
    counts = {
        "raw_lines": 0,
        "raw_user_messages": 0,
        "raw_assistant_messages": 0,
        "included_user_turns": 0,
        "included_assistant_turns": 0,
        "skipped_noise_turns": 0,
    }

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            counts["raw_lines"] += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                counts["skipped_noise_turns"] += 1
                continue

            if obj.get("isMeta"):
                counts["skipped_noise_turns"] += 1
                continue

            message = obj.get("message")
            if not isinstance(message, dict):
                counts["skipped_noise_turns"] += 1
                continue

            role = message.get("role")
            if role not in {"user", "assistant"}:
                counts["skipped_noise_turns"] += 1
                continue

            counts[f"raw_{role}_messages"] += 1

            text = extract_text(message.get("content"))
            if is_noise_text(text):
                counts["skipped_noise_turns"] += 1
                continue

            timestamp = obj.get("timestamp") or "timestamp-missing"
            entries.append(
                {
                    "timestamp": str(timestamp),
                    "role": role,
                    "text": text,
                    "line": str(line_number),
                }
            )
            counts[f"included_{role}_turns"] += 1

    entries.sort(key=lambda item: item["timestamp"])
    return entries, counts


def render_markdown(
    session_id: str,
    source_path: pathlib.Path,
    entries: list[dict[str, str]],
    counts: dict[str, int],
) -> str:
    extracted_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    lines = [
        "# Claude Code Session Transcript",
        "",
        f"- Session ID: `{session_id}`",
        f"- Source JSONL: `{source_path}`",
        f"- Extracted at: `{extracted_at}`",
        f"- Included user turns: {counts['included_user_turns']}",
        f"- Included assistant turns: {counts['included_assistant_turns']}",
        f"- Skipped noise/meta entries: {counts['skipped_noise_turns']}",
        "",
        "---",
        "",
    ]

    for entry in entries:
        role = "User" if entry["role"] == "user" else "Assistant"
        lines.extend(
            [
                f"## {entry['timestamp']} — {role}",
                "",
                entry["text"],
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract a clean Markdown transcript from a Claude Code JSONL session."
    )
    parser.add_argument("session_id", help="Claude Code session ID, without .jsonl")
    parser.add_argument(
        "--project-dir",
        type=pathlib.Path,
        help="Working directory to derive the Claude project hash from. Defaults to PWD.",
    )
    parser.add_argument(
        "--claude-projects-dir",
        type=pathlib.Path,
        help="Explicit path to a Claude Code project directory containing the JSONL.",
    )
    parser.add_argument(
        "--out",
        type=pathlib.Path,
        help="Output Markdown path. Defaults to ~/.jstack/transcripts/<session-id>.clean.md",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    source_path = resolve_session_jsonl(
        args.session_id, args.claude_projects_dir, args.project_dir
    )

    if source_path is None:
        print(
            f"ERROR: Claude session JSONL not found for session {args.session_id}. "
            "Use --claude-projects-dir to point to a specific project directory, "
            "or --project-dir to derive the project hash from a working directory.",
            file=sys.stderr,
        )
        return 2

    out_path = args.out
    if out_path is None:
        out_dir = pathlib.Path.home() / ".jstack" / "transcripts"
        out_path = out_dir / f"{args.session_id}.clean.md"

    entries, counts = parse_entries(source_path)
    if not entries:
        print(f"ERROR: No user/assistant text entries extracted from: {source_path}", file=sys.stderr)
        return 3

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_markdown(args.session_id, source_path, entries, counts),
        encoding="utf-8",
    )

    print(f"Wrote: {out_path}")
    print(f"Included user turns: {counts['included_user_turns']}")
    print(f"Included assistant turns: {counts['included_assistant_turns']}")
    print(f"Skipped noise/meta entries: {counts['skipped_noise_turns']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
