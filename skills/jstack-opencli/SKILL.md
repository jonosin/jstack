---
name: jstack-opencli
description: >-
  Convert any website into a CLI and run Browser Use on Jono's logged-in Brave session via the local
  OpenCLI build at ~/builds/OpenCLI — defaulting to the extension-free CDP bypass (Brave on port
  9222), never the Browser Bridge extension. Use when Jono says /jstack-opencli, "use opencli", "run
  an opencli command", "turn this website into a CLI", "make an opencli tool/adapter for a site",
  "scrape/extract a site from my logged-in session", "drive my Brave session headlessly", or wants to
  run/author OpenCLI commands against a logged-in browser without the Chrome extension. Routes to the
  OpenCLI repo, runs commands through the CDP-bypass wrapper, and mandates that any NEW tool defaults
  to the bypass too.
---

# jstack-opencli

Front door to the local **OpenCLI** build (`~/builds/OpenCLI`). OpenCLI turns any website (plus
Electron apps and external CLIs) into a uniform `opencli <site> <command>` surface that reuses a
logged-in browser session — read, extract, automate, no re-auth, zero runtime LLM tokens, pipeable
JSON. This skill makes that repeatable AND enforces one opinion:

> **Default to the CDP bypass — attach to Jono's logged-in Brave on port 9222 — never the Browser
> Bridge extension.** OpenCLI picks the transport in `src/runtime.ts`: `OPENCLI_CDP_ENDPOINT` set →
> CDP; unset → extension. So the rule is simply: always run with that env var set. The
> `scripts/opencli-cdp.sh` wrapper does this for you (preflights :9222, sets the env var, runs the
> command).

The repo's own map is `~/builds/OpenCLI/AGENTS.md` — read it for repo internals beyond this skill.

## Run an existing command (the default path)

Always go through the wrapper so the bypass is enforced and :9222 is preflighted:

```bash
~/.claude/skills/jstack-opencli/scripts/opencli-cdp.sh <site> <command> [args] -f json
```

Examples:

```bash
# discover every registered command first — never hard-code the adapter list
opencli-cdp.sh list -f json

# read a logged-in surface (uses the Brave session's cookies over CDP)
opencli-cdp.sh linkedin salesnav-inbox --filter inmail-accepted --limit 5 -f json
opencli-cdp.sh youtube transcript "https://www.youtube.com/watch?v=..." -f json
opencli-cdp.sh reddit hot --limit 10 -f json
```

Rules:
- Always pass `-f json` for machine output.
- Use `opencli-cdp.sh list -f json` (or `<site> <command> --help`) to discover commands/flags at
  runtime — adapters change; don't assume.
- `PUBLIC`-strategy adapters (hackernews, arxiv, npm, wikipedia, ...) need no browser at all, but
  running them through the wrapper is harmless.

### Preflight / troubleshooting

- The wrapper checks `curl -fsS http://localhost:9222/json/version`. If it exits **69**, Brave isn't
  exposing CDP — launch it with `--remote-debugging-port=9222 --remote-allow-origins="*"`, or use the
  **`brave-cdp`** skill / `brave-cdp-relaunch`. Then retry.
- `opencli doctor` only validates the **extension** path; it is NOT a valid check for the bypass.
  Ignore its result when running via CDP.
- Multiple matching tabs? Set `OPENCLI_CDP_TARGET="<substring of tab title/url>"` to pin one.
- Exit **1** = opencli binary not found → `cd ~/builds/OpenCLI && npm run build`.
- If site commands suddenly use the extension despite the env var, the bypass gate may have been lost:
  it's a **local patch** (`if (process.env.OPENCLI_CDP_ENDPOINT) return CDPBridge;` in
  `~/builds/OpenCLI/src/runtime.ts` `getBrowserFactory`) that is NOT in upstream and is dropped by a
  re-clone / `git checkout` / upstream merge. Re-apply it (see `~/builds/OpenCLI/AGENTS.md` → Transport).
- Never echo cookies, CSRF tokens, or private message bodies into output. Never click
  send/compose/connect through a driven session unless Jono explicitly asks.

## Make a new tool (convert a new website into a CLI)

When Jono wants a new site turned into commands, author it in the OpenCLI repo and **make it default
to the CDP bypass too**. Full procedure: **`references/authoring-new-tool.md`**. The essentials:

1. Use the repo's bundled **`opencli-adapter-author`** skill (`~/builds/OpenCLI/skills/`) for the
   recon → API-discovery → implement → verify workflow.
2. Drop the command at `~/builds/OpenCLI/clis/<site>/<command>.js` (or iterate at
   `~/.opencli/clis/<site>/<command>.js` — runtime, no build). Browser-backed adapters declare
   `browser: true, func: async (page, args) => rows` and do authenticated `page.evaluate(...)`
   fetches; pattern reference is `clis/linkedin/salesnav-inbox.js`.
3. The adapter does NOT choose transport — `src/runtime.ts` does. So author/run/test the new tool
   with `OPENCLI_CDP_ENDPOINT` set (i.e. through `opencli-cdp.sh`), so it exercises the logged-in
   Brave session, not the extension.
4. `cd ~/builds/OpenCLI && npm run build` auto-registers any `clis/**` file calling `cli({...})`.
5. Test: `npx vitest run --project adapter clis/<site>/<command>.test.js`.

## What this skill owns vs. routes to

- **Owns:** the CDP-bypass-by-default policy + the `opencli-cdp.sh` wrapper + routing to the repo.
- **Routes to:** `~/builds/OpenCLI/AGENTS.md` (repo internals), the repo's `opencli-adapter-author` /
  `opencli-usage` / `opencli-autofix` skills (authoring & repair), and the `brave-cdp` skill (getting
  Brave onto :9222).
- **Specialized sibling:** `jstack-linkedin-salesnav` already wraps the LinkedIn Sales Navigator
  reply-checking / lead flows on top of OpenCLI — prefer it for those.
