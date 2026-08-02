#!/usr/bin/env python3
"""jstack-cc-find — natural-language search over Claude Code sessions.

Reuses the jstack transcript extractor's JSONL parser, noise filter, and text
extractor verbatim. Adds a tiny BM25 ranker and a CWD → Claude project
mapper, then prints ranked sessions with copy-pasteable resume commands.

Output: top-N matches (default 5) sorted by BM25 score, each with
  - session id
  - last activity timestamp
  - first user turn preview
  - score
  - `claude --resume <id> --dangerously-skip-permissions` line

Examples:
  find_claude_session.py "product hunt UGC LinkedIn leads"
  find_claude_session.py "pricing page copy" --project second-brain --top 3
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import math
import os
import pathlib
import re
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
    # Sibling skill: <skills>/jstack/scripts/extract_claude_session.py
    sibling = (
        pathlib.Path(__file__).resolve().parent.parent.parent
        / "jstack" / "scripts" / "extract_claude_session.py"
    )
    return sibling


# Reuse the canonical extractor (parse_entries, extract_text, is_noise_text, etc.).
SOURCE = _resolve_extractor()
_spec = importlib.util.spec_from_file_location("jstack_extractor", SOURCE)
if _spec is None or _spec.loader is None or not SOURCE.exists():  # pragma: no cover
    print(f"ERROR: cannot load extractor at {SOURCE}", file=sys.stderr)
    print("       set JSTACK_EXTRACTOR or install the jstack skill alongside this one.", file=sys.stderr)
    raise SystemExit(2)
src = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(src)

CLAUDE_PROJECTS_ROOT = pathlib.Path(
    _jstack_cfg("CLAUDE_PROJECTS_DIR", str(pathlib.Path.home() / ".claude" / "projects"))
).expanduser()

# Optional friendly aliases (slug → friendly name). Empty by default; auto-detect
# from CWD covers the common case, and --claude-dir handles anything else. Users
# can hardcode their own frequently-used projects here if they like.
DEFAULT_PROJECTS: dict[str, str] = {}

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
    "have", "i", "in", "is", "it", "its", "of", "on", "or", "that", "the",
    "this", "to", "was", "were", "will", "with", "you", "your", "we", "our",
    "they", "their", "them", "but", "not", "if", "do", "did", "can", "could",
    "would", "should", "about", "any", "all", "some", "so", "than", "then",
    "there", "what", "when", "where", "which", "who", "how", "my", "me",
    "am", "just", "like", "very",
}

WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]+")


def tokenize(text: str) -> list[str]:
    """Lowercase + tokenize + drop stopwords. Keep short tokens (>= 2 chars)."""
    tokens: list[str] = []
    for match in WORD_RE.finditer(text.lower()):
        t = match.group(0)
        if len(t) < 2:
            continue
        if t in STOPWORDS:
            continue
        tokens.append(t)
    return tokens


def slug_from_path(absolute: pathlib.Path) -> str:
    """`/home/user/second-brain` → `-home-user-second-brain`."""
    return "-" + str(absolute).lstrip("/").replace("/", "-")


def project_for_cwd(cwd: pathlib.Path) -> str | None:
    slug = slug_from_path(cwd.resolve())
    if (CLAUDE_PROJECTS_ROOT / slug).is_dir():
        return slug
    return None


def load_session_corpus(claude_dir: pathlib.Path) -> list[dict]:
    """Read every JSONL, parse entries, return one record per session."""
    records: list[dict] = []
    for path in sorted(claude_dir.glob("*.jsonl")):
        try:
            entries, _counts = src.parse_entries(path)
        except Exception as exc:  # pragma: no cover
            print(f"WARN: failed to parse {path.name}: {exc}", file=sys.stderr)
            continue
        if not entries:
            continue

        # Concatenate every entry's text. Cap to keep memory bounded.
        full_text = "\n".join(e["text"] for e in entries)
        if len(full_text) > 1_500_000:
            full_text = full_text[:1_500_000]

        # First user turn (after the noise filter) — best "title" signal.
        first_user = next((e["text"] for e in entries if e["role"] == "user"), "")
        first_user = first_user.replace("\n", " ").strip()[:280]

        last_ts = entries[-1]["timestamp"]
        records.append({
            "session_id": path.stem,
            "tokens": tokenize(full_text),
            "first_user": first_user,
            "last_ts": last_ts,
            "turns": len(entries),
        })
    return records


def rank(
    query: str,
    records: list[dict],
    *,
    boost_first_user: float = 3.0,
) -> list[dict]:
    """Return records sorted by BM25 score, descending. Empty list if no hits."""
    if not records:
        return []
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    n_docs = len(records)
    doc_tokens = [r["tokens"] for r in records]
    doc_lengths = [len(t) for t in doc_tokens]
    avg_dl = sum(doc_lengths) / n_docs
    k1, b = 1.5, 0.75

    # Document frequency per term.
    df: dict[str, int] = {}
    for tokens in doc_tokens:
        seen = set(tokens)
        for t in seen:
            df[t] = df.get(t, 0) + 1

    scored: list[dict] = []
    for idx, record in enumerate(records):
        tokens = doc_tokens[idx]
        if not tokens:
            continue
        dl = doc_lengths[idx]
        tf: dict[str, int] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        s = 0.0
        for qt in query_tokens:
            f = tf.get(qt, 0)
            if f == 0:
                continue
            idf = math.log(1 + (n_docs - df.get(qt, 0) + 0.5) / (df.get(qt, 0) + 0.5))
            denom = f + k1 * (1 - b + b * dl / max(avg_dl, 1))
            s += idf * (f * (k1 + 1)) / denom
        if s > 0:
            # Boost when query terms appear in the first user turn — strong topic signal.
            first_user_tokens = set(tokenize(record["first_user"]))
            if first_user_tokens & set(query_tokens):
                s *= boost_first_user
            scored.append({"record": record, "score": s})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def render(
    scored: list[dict],
    *,
    top: int,
    resume_flags: list[str],
) -> str:
    lines: list[str] = []
    if not scored:
        return "No matches."
    for rank_idx, item in enumerate(scored[:top], 1):
        rec = item["record"]
        sid = rec["session_id"]
        flags = " ".join(resume_flags)
        resume_line = f"claude --resume {sid} {flags}".rstrip()
        ts = rec["last_ts"]
        # Compact ISO date
        date = ts[:10] if ts and len(ts) >= 10 else "?"
        first = rec["first_user"] or "(no user turn)"
        lines.append(
            f"\n{rank_idx}. {sid}\n"
            f"   Date: {date}   Turns: {rec['turns']}   Score: {item['score']:.2f}\n"
            f"   First turn: {first}\n"
            f"\n"
            f"   {resume_line}"
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Search Claude Code sessions with a natural-language query."
    )
    p.add_argument("query", help="Natural-language query, e.g. 'product hunt UGC leads'.")
    p.add_argument(
        "--project",
        help="Claude project slug (e.g. second-brain). Default: auto-detect from CWD.",
    )
    p.add_argument("--claude-dir", type=pathlib.Path, help="Override the Claude project dir.")
    p.add_argument("--top", type=int, default=5, help="Number of results to return (default 5).")
    p.add_argument(
        "--resume-flags",
        default="--dangerously-skip-permissions",
        help="Flags to append to `claude --resume <id>`. Default: --dangerously-skip-permissions",
    )
    p.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    if args.claude_dir:
        claude_dir = args.claude_dir
    elif args.project:
        friendly_to_slug = {v: k for k, v in DEFAULT_PROJECTS.items()}
        if args.project in DEFAULT_PROJECTS:
            slug = args.project  # already a slug (e.g. -home-user-...)
        elif args.project in friendly_to_slug:
            slug = friendly_to_slug[args.project]  # friendly name → slug
        else:
            print(f"ERROR: unknown project '{args.project}'", file=sys.stderr)
            print(f"       known (by friendly name): {sorted(friendly_to_slug)}", file=sys.stderr)
            print(f"       or pass --claude-dir <path>", file=sys.stderr)
            return 2
        claude_dir = CLAUDE_PROJECTS_ROOT / slug
    else:
        slug = project_for_cwd(pathlib.Path.cwd())
        if not slug:
            print(
                "ERROR: cannot auto-detect Claude project from CWD. "
                "Pass --project <name> or --claude-dir <path>.",
                file=sys.stderr,
            )
            return 2
        claude_dir = CLAUDE_PROJECTS_ROOT / slug

    if not claude_dir.is_dir():
        print(f"ERROR: Claude project dir not found: {claude_dir}", file=sys.stderr)
        return 2

    corpus = load_session_corpus(claude_dir)
    scored = rank(args.query, corpus)
    flags = args.resume_flags.split() if args.resume_flags else []

    if args.json:
        out = [
            {
                "session_id": item["record"]["session_id"],
                "score": item["score"],
                "last_ts": item["record"]["last_ts"],
                "turns": item["record"]["turns"],
                "first_user": item["record"]["first_user"],
                "resume_command": f"claude --resume {item['record']['session_id']} " + " ".join(flags),
            }
            for item in scored[: args.top]
        ]
        print(json.dumps(out, indent=2))
        return 0

    print(f'Query: "{args.query}"')
    print(f"Project: {claude_dir.name}   Sessions: {len(corpus)}")
    print(render(scored, top=args.top, resume_flags=flags))
    if not scored:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
