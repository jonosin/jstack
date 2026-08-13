#!/usr/bin/env python3
"""
vercel_doctor.py — deterministic diagnosis + fix for the recurring "I ran
`vercel login`, but `vercel whoami` / `vercel deploy` still fails" scenario.

Root causes this codifies, found and fixed live on 2026-07-01 while wiring up
jstack-sba-diagram-deploy:

  1. A stale VERCEL_TOKEN env var (exported in a shell profile, or left over
     from an old project's .env) silently overrides the CLI's own stored
     login session and breaks auth with an opaque "specified token is not
     valid" error, even though `vercel login` just succeeded. Fix: unset it
     for vercel invocations (or find + remove it from the shell profile).
  2. An outdated Vercel CLI (~v50.x) has a broken --scope/--team flag: when
     the account has no default team, `vercel deploy`/`vercel link` fails
     with a "missing_scope" JSON error EVEN WHEN --scope is passed explicitly.
     Fix: `npm i -g vercel@latest` (fixed as of v54.18.x).
  3. Once on a current CLI, an account with a team but no default scope still
     needs an explicit `--scope <team-name>` on deploy/link. If there's
     exactly one team, this script auto-detects and reports it (the calling
     skill/script can then pass --scope automatically, as
     jstack-sba-diagram-deploy did).

Usage:
    python3 vercel_doctor.py            # diagnose only, print a report
    python3 vercel_doctor.py --fix      # also apply safe, reversible fixes:
                                         #   - upgrade the CLI if outdated
                                         # (never edits shell profiles or
                                         #  auth files; those stay manual)
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

MIN_KNOWN_GOOD_VERSION = (54, 0, 0)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Diagnose and optionally fix vercel CLI auth failures.")
    p.add_argument("--fix", action="store_true", help="Apply safe automatic fixes (CLI upgrade only)")
    return p.parse_args()


def _vercel_env() -> dict:
    env = dict(os.environ)
    env.pop("VERCEL_TOKEN", None)
    env["CI"] = "1"  # suppress interactive spinner banners written straight to the tty
    return env


def check_vercel_installed() -> str | None:
    path = shutil.which("vercel")
    if not path:
        return None
    return path


def get_cli_version() -> tuple[int, int, int] | None:
    result = subprocess.run(["vercel", "--version"], capture_output=True, text=True)
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", result.stdout + result.stderr)
    if not match:
        return None
    return tuple(int(x) for x in match.groups())


def check_stale_token_env() -> bool:
    return "VERCEL_TOKEN" in os.environ


def check_stale_token_in_profiles() -> list[str]:
    hits = []
    for profile in (".zshrc", ".zprofile", ".bashrc", ".bash_profile", ".profile"):
        path = Path.home() / profile
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "VERCEL_TOKEN" in text:
            hits.append(str(path))
    return hits


def whoami(env: dict) -> tuple[bool, str]:
    result = subprocess.run(["vercel", "whoami"], capture_output=True, text=True, env=env)
    ok = result.returncode == 0
    return ok, (result.stdout + result.stderr).strip()


def get_single_team_scope(env: dict) -> str | None:
    result = subprocess.run(
        ["vercel", "deploy", "--yes", "--prod"],
        cwd="/tmp",
        capture_output=True,
        text=True,
        env=env,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )
    output = result.stdout + result.stderr
    try:
        start = output.index("{")
        end = output.rindex("}") + 1
        payload = json.loads(output[start:end])
    except (ValueError, json.JSONDecodeError):
        return None
    if payload.get("reason") != "missing_scope":
        return None
    choices = payload.get("choices") or []
    if len(choices) == 1:
        return choices[0].get("name")
    return None


def main() -> None:
    args = parse_args()
    report = []
    fixes_applied = []

    vercel_path = check_vercel_installed()
    if not vercel_path:
        print("ERROR: `vercel` CLI not found on PATH. Install it first: npm i -g vercel", file=sys.stderr)
        sys.exit(1)
    report.append(f"vercel CLI found at: {vercel_path}")

    version = get_cli_version()
    if version:
        report.append(f"vercel CLI version: {'.'.join(map(str, version))}")
        if version < MIN_KNOWN_GOOD_VERSION:
            report.append(
                f"  -> OUTDATED (< {'.'.join(map(str, MIN_KNOWN_GOOD_VERSION))}). "
                "Known bug in older CLIs: --scope/--team is silently ignored on "
                "`vercel deploy`/`vercel link` when the account has no default "
                "team, always failing with a missing_scope error even with "
                "--scope passed explicitly."
            )
            if args.fix:
                print("Upgrading vercel CLI: npm i -g vercel@latest")
                upgrade = subprocess.run(["npm", "i", "-g", "vercel@latest"], capture_output=True, text=True)
                if upgrade.returncode == 0:
                    fixes_applied.append("Upgraded vercel CLI to latest via npm i -g vercel@latest")
                    version = get_cli_version()
                    report.append(f"  -> upgraded to: {'.'.join(map(str, version)) if version else 'unknown'}")
                else:
                    report.append(f"  -> upgrade FAILED:\n{upgrade.stdout}\n{upgrade.stderr}")

    if check_stale_token_env():
        report.append(
            "FOUND: VERCEL_TOKEN is set in this shell's environment. "
            "This silently overrides the CLI's own `vercel login` session "
            "and causes `vercel whoami` to report \"specified token is not "
            "valid\" even right after a successful login. This script "
            "strips it for its own vercel calls below, but it will still "
            "break plain `vercel ...` commands run directly in this shell."
        )
        profile_hits = check_stale_token_in_profiles()
        if profile_hits:
            report.append(
                "  -> VERCEL_TOKEN is exported in: " + ", ".join(profile_hits) +
                ". Remove that `export VERCEL_TOKEN=...` line yourself (this "
                "script does not edit shell profiles) and open a new shell, "
                "or just `unset VERCEL_TOKEN` for the current session."
            )
        else:
            report.append(
                "  -> not found in common shell profiles; it was likely set "
                "manually in this shell session only. `unset VERCEL_TOKEN` "
                "will clear it for the current session."
            )
    else:
        report.append("VERCEL_TOKEN env var: not set (good)")

    clean_env = _vercel_env()
    ok, output = whoami(clean_env)
    if ok:
        report.append(f"vercel whoami (with VERCEL_TOKEN stripped): OK -> {output}")
    else:
        report.append(f"vercel whoami (with VERCEL_TOKEN stripped): STILL FAILING\n  {output}")
        report.append("  -> run `vercel login` again; if it still fails after that, this is a genuine auth issue beyond the known causes above.")

    if ok:
        scope = get_single_team_scope(clean_env)
        if scope:
            report.append(
                f"Account has no default team scope, but exactly one team is "
                f"available: '{scope}'. Any `vercel deploy`/`vercel link` in a "
                f"non-interactive context needs `--scope {scope}` explicitly."
            )

    print("\n".join(report))
    if fixes_applied:
        print("\nFixes applied:")
        for f in fixes_applied:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
