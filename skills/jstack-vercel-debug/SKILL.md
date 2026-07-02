---
name: jstack-vercel-debug
description: >-
  Diagnose and fix the recurring "I just ran `vercel login`, but `vercel
  whoami` / `vercel deploy` still fails" scenario. Use when Jono hits Vercel
  CLI auth errors ("specified token is not valid", "missing_scope",
  "Provide --scope or --team explicitly") even right after logging in, on
  any new Vercel-deploying project. Deterministic: runs a fixed diagnostic
  checklist (stale VERCEL_TOKEN env var, outdated CLI with a broken --scope
  flag, missing default team scope), reports exactly what's wrong, and can
  apply the one safe automatic fix (CLI upgrade).
---

# jstack-vercel-debug

Jono keeps hitting this: he runs `vercel login`, it reports success, and then
`vercel whoami` (or `vercel deploy`) still fails. This is never actually a
broken login — it's one of three specific, previously-diagnosed causes below.
Run the diagnostic script instead of re-debugging from scratch each time.

## Run it

```bash
python3 ~/jstack/skills/jstack-vercel-debug/scripts/vercel_doctor.py
# to also apply the one safe auto-fix (CLI upgrade):
python3 ~/jstack/skills/jstack-vercel-debug/scripts/vercel_doctor.py --fix
```

## The three root causes it checks, in order (found live on 2026-07-01)

1. **A stale `VERCEL_TOKEN` env var silently overrides the CLI login.**
   If `VERCEL_TOKEN` is set anywhere in the shell environment (exported in a
   profile, or leaked from some other project's `.env`), the Vercel CLI uses
   it instead of the session `vercel login` just created, and `vercel whoami`
   fails with `Error: The specified token is not valid. Use vercel login to
   generate a new token.` — even though the login itself worked fine. The
   script checks `os.environ`, greps common shell profiles
   (`.zshrc`/`.zprofile`/`.bashrc`/`.bash_profile`/`.profile`) for an
   `export VERCEL_TOKEN=...` line, and reports where it's coming from. It
   does not edit your shell profile for you — remove that line yourself, or
   `unset VERCEL_TOKEN` for the current session. Any script that shells out
   to `vercel` should strip this env var for its own subprocess calls (this
   was the pattern used in the now-removed `jstack-sba-diagram-deploy`
   skill's `_vercel_env()` helper — recreate that pattern in any future
   Vercel-deploying skill).

2. **An outdated CLI (< v54) has a broken `--scope`/`--team` flag.** On an
   account with no default team, `vercel deploy` / `vercel link` fails
   non-interactively with a `missing_scope` JSON error — **even when
   `--scope <team>` is passed explicitly**. Confirmed broken on CLI v50.17.1,
   confirmed fixed on v54.18.x. The script detects the installed version and,
   with `--fix`, runs `npm i -g vercel@latest`.

3. **No default team scope set, one team available.** Even on a current CLI,
   an account belonging to exactly one team with no default scope still
   needs `--scope <team-name>` passed explicitly to `deploy`/`link` in
   non-interactive mode. The script triggers the `missing_scope` error
   on purpose (via a harmless `vercel deploy` in `/tmp`) to read the
   `choices` list Vercel returns, and reports the team name to use. It does
   not deploy or link anything real — `/tmp` has no linked project, so the
   probe deploy always fails at the scope-check step before touching real
   infrastructure.

## What `--fix` does vs. doesn't do

- **Does:** `npm i -g vercel@latest` if the installed CLI predates the known
  fix.
- **Does not:** edit shell profiles, run `vercel login`, or touch
  `~/Library/Application Support/com.vercel.cli/auth.json`. Login and
  profile edits stay manual — this script only diagnoses and reports on
  those, since removing an env var export from a shell profile is a config
  change Jono should review before it happens.

## Reading the output

The script prints a flat report, one finding per line, each followed by a
`->` line explaining the fix when something's wrong. A clean account (no
stale token, current CLI, `vercel whoami` succeeds) prints three "good"
lines and nothing else.

## Next skills

| Next | When |
|------|------|
| standalone | Any future skill that deploys to Vercel should run this diagnostic first if `vercel whoami` fails, rather than re-debugging from scratch. |
