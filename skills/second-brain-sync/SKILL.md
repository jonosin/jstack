---
name: second-brain-sync
description: Synchronize a local second-brain checkout and its Jstack checkout with their configured Git remotes. Use when the user asks to sync, refresh, update, or safely fast-forward a local second brain for retrieval, or to diagnose a blocked second-brain sync.
---

# second-brain-sync

Run one command. Do not replace any step with manual Git commands.

```bash
~/jstack/skills/second-brain-sync/scripts/second-brain-sync
```

Use `--dry-run` to fetch and report what a normal run would change. It does not fast-forward a checkout or rebuild the retrieval overlay.

## Contract

The command reads these values in this order: environment, `~/.jstack/config.env`, then the documented path default.

- `SECOND_BRAIN_PATH`, default `~/second-brain`
- `JSTACK_PATH`, default `~/jstack`
- `SECOND_BRAIN_REMOTE`, required exact `origin` URL
- `JSTACK_REMOTE`, required exact `origin` URL

It stops with exit `4` if a repository is missing, dirty, off `main`, points at a different `origin`, has local-only commits, has diverged history, cannot fetch, or cannot repair the retrieval overlay.

On success it fetches both remotes, fast-forwards only, then checks `python3 tools/sb.py overlay freshness --json`. It runs `overlay update` only when freshness returns exit `3`, then checks freshness again. It never compiles, changes `raw/` or `wiki/`, commits, pushes, resets, cleans, force-checks out, or stashes.

## Report

For exit `0`, report the two commit IDs and the overlay status. For any other exit, report the command output and stop. Do not try another Git recovery path.

## Gotchas

- A dry run still fetches. It changes only local remote-tracking references.
- Configure both expected remote URLs. Missing URLs are a block, not a prompt to trust the current remote.
- If `overlay update` leaves tracked changes, the command blocks. Do not discard those changes automatically.

## Next skills

| Next | When |
|------|------|
| `querybrain` | Retrieval is needed after a successful sync. |

Otherwise standalone.
