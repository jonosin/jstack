#!/usr/bin/env python3
"""savetobrain-from-cc transcript extractor.

Reuses the jstack transcript extractor's JSONL parsing, noise filtering, ANSI
stripping, and markdown rendering verbatim — only the project mapping and
output convention differ. This is a thin wrapper, not a parallel parser.

Default behaviour: write the rendered transcript to
`raw/personal/drops/YYYY-MM-DD-claude-session-<slug>.md` so it shows up
immediately as pending raw for `/brainwork` to ingest.

Flags:
  --staging     Write to raw/personal/scratch/claude-transcripts/ instead.
  --full        Force full extraction, ignore saved state.
  --since ISO   Extract only entries with timestamp > ISO.
  --out PATH    Override the output markdown path.

State (.state.json) always lives in the staging dir so incremental
re-extraction works regardless of where the drop was written.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import os
import pathlib
import sys


def _jstack_cfg(key: str, default: str = "") -> str:
    """Resolve a config value: env var > ~/.jstack/config.env > default."""
    val = os.environ.get(key)
    if val:
        return val
    cfg = pathlib.Path.home() / ".jstack" / "config.env"
    if cfg.exists():
        for line in cfg.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == key:
                return v.strip().strip('"').strip("'")
    return default


def _resolve_extractor() -> pathlib.Path:
    """Locate the canonical transcript extractor (the jstack skill ships one)."""
    override = os.environ.get("JSTACK_EXTRACTOR")
    if override:
        return pathlib.Path(override).expanduser()
    return (
        pathlib.Path(__file__).resolve().parent.parent.parent
        / "jstack" / "scripts" / "extract_claude_session.py"
    )


# Reuse the canonical extraction logic from the jstack skill's extractor.
SOURCE = _resolve_extractor()
_spec = importlib.util.spec_from_file_location("jstack_extractor", SOURCE)
if _spec is None or _spec.loader is None or not SOURCE.exists():  # pragma: no cover
    print(f"ERROR: cannot load extractor at {SOURCE}", file=sys.stderr)
    print("       set JSTACK_EXTRACTOR or install the jstack skill alongside this one.", file=sys.stderr)
    raise SystemExit(2)
src = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(src)

# Second-brain project topology (configurable; see ~/.jstack/config.env).
VAULT_ROOT = pathlib.Path(
    _jstack_cfg("SECOND_BRAIN_PATH", str(pathlib.Path.home() / "second-brain"))
).expanduser()
CLAUDE_PROJECTS_ROOT = pathlib.Path(
    _jstack_cfg("CLAUDE_PROJECTS_DIR", str(pathlib.Path.home() / ".claude" / "projects"))
).expanduser()
_VAULT_SLUG = "-" + str(VAULT_ROOT.resolve()).lstrip("/").replace("/", "-")
CLAUDE_PROJECT = CLAUDE_PROJECTS_ROOT / _VAULT_SLUG
STAGING_DIR = VAULT_ROOT / "raw/personal/scratch/claude-transcripts"
DROPS_DIR = VAULT_ROOT / "raw/personal/drops"


def derive_slug(session_id: str, source_path: pathlib.Path) -> str:
    """Return a stable slug for the drop filename."""
    short = session_id.split("-")[0] if "-" in session_id else session_id[:8]
    mtime = dt.datetime.fromtimestamp(source_path.stat().st_mtime, dt.timezone.utc)
    return f"claude-session-{short}-{mtime.date().isoformat()}"


def default_drop_path(session_id: str, source_path: pathlib.Path) -> pathlib.Path:
    today = dt.date.today().isoformat()
    slug = derive_slug(session_id, source_path)
    return DROPS_DIR / f"{today}-{slug}.md"


def render_drop(
    session_id: str,
    source_path: pathlib.Path,
    entries: list[dict],
    counts: dict,
) -> str:
    """Wrap the canonical transcript with raw-drop frontmatter.

    Frontmatter matches `skills/llm-wiki/references/raw-template.md` so
    `/brainwork` can ingest it via Standard Ingest or Personal Ingest
    depending on where it lands.
    """
    extracted_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    title = f"Claude Code session {session_id[:8]}"
    fm = "\n".join([
        "---",
        f'title: "{title}"',
        f'source: "claude-code://session/{session_id}"',
        f'author: "{session_id[:8]}"',
        "published: Unknown",
        f"collected: {extracted_at[:10]}",
        "tags: [claude-code, session-transcript, drops]",
        "---",
        "",
    ])
    body = src.render_markdown(session_id, source_path, entries, counts)
    return fm + body


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Extract a Claude Code session transcript as a raw drop for "
            "the second brain."
        )
    )
    p.add_argument("session_id", help="Claude Code session ID, without .jsonl")
    p.add_argument("--full", action="store_true", help="Force full extraction, ignore state.")
    p.add_argument("--since", type=str, default=None, help="ISO timestamp filter (UTC).")
    p.add_argument(
        "--staging",
        action="store_true",
        help="Write to raw/personal/scratch/claude-transcripts/ instead of drops/.",
    )
    p.add_argument("--out", type=pathlib.Path, default=None, help="Override output markdown path.")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    source_path = CLAUDE_PROJECT / f"{args.session_id}.jsonl"
    if not source_path.exists():
        print(f"ERROR: Claude session JSONL not found: {source_path}", file=sys.stderr)
        return 2

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    state_path = STAGING_DIR / f"{args.session_id}.state.json"

    # Resolve start line + incremental flag (mirrors source's mode logic).
    start_line = 0
    is_incremental = False
    if args.full:
        pass
    elif args.since:
        state = src.load_state(state_path)
        if state and "last_jsonl_line" in state:
            start_line = state["last_jsonl_line"]
            is_incremental = True
    else:
        state = src.load_state(state_path)
        if state and "last_jsonl_line" in state:
            start_line = state["last_jsonl_line"]
            is_incremental = True

    entries, counts = src.parse_entries(source_path, start_line=start_line)
    if not entries:
        print("No new entries found. Session unchanged.")
        return 0

    if args.since:
        before = len(entries)
        entries = [e for e in entries if e["timestamp"] > args.since]
        if not entries:
            print(f"No entries found after {args.since}.")
            return 0
        if before != len(entries):
            print(f"Timestamp filter dropped {before - len(entries)} entries.")

    # Pick output path.
    if args.out:
        out_path = args.out
    elif args.staging:
        out_path = STAGING_DIR / f"{args.session_id}.clean.md"
    else:
        out_path = default_drop_path(args.session_id, source_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    md = render_drop(args.session_id, source_path, entries, counts)
    out_path.write_text(md, encoding="utf-8")

    # Persist state (in staging dir, regardless of where the drop went).
    prev = src.load_state(state_path) or {}
    state = {
        "session_id": args.session_id,
        "last_jsonl_line": counts.get("last_jsonl_line", start_line),
        "entries_count": prev.get("entries_count", 0) + len(entries),
        "user_turns": prev.get("user_turns", 0) + counts["included_user_turns"],
        "assistant_turns": prev.get("assistant_turns", 0) + counts["included_assistant_turns"],
        "last_extracted_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    src.save_state(state_path, state)

    label = "Incremental" if is_incremental else "Full"
    print(f"Wrote ({label}): {out_path}")
    print(f"Included user turns: {counts['included_user_turns']}")
    print(f"Included assistant turns: {counts['included_assistant_turns']}")
    print(f"Skipped noise/meta entries: {counts['skipped_noise_turns']}")
    if is_incremental:
        print(
            "Cumulative session: "
            f"{state['entries_count']} entries, "
            f"{state['user_turns']} user / {state['assistant_turns']} assistant turns"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
