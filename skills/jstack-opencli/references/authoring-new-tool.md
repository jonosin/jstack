# Authoring a new OpenCLI tool (convert a website into a CLI)

Read this when Jono wants a NEW site turned into `opencli <site> <command>` tools. Goal: a working,
tested adapter in `~/builds/OpenCLI` that **defaults to the CDP bypass** (logged-in Brave on :9222),
not the extension. The repo's own `AGENTS.md` and its bundled `opencli-adapter-author` skill are the
deeper sources; this file is the jstack-opinionated checklist.

## Table of contents
1. Transport rule (the non-negotiable)
2. Where the code lives
3. The adapter file model
4. Workflow: recon → discover → implement → verify
5. Build & register
6. Test
7. Guardrails

## 1. Transport rule (the non-negotiable)

The adapter NEVER chooses the transport — `~/builds/OpenCLI/src/runtime.ts` (`getBrowserFactory`)
does: `OPENCLI_CDP_ENDPOINT` set → `CDPBridge` (Brave over CDP); unset → `BrowserBridge` (extension).
So "default to the bypass" = always author, run, and test with that env var set. Use the wrapper
`scripts/opencli-cdp.sh` (it sets `OPENCLI_CDP_ENDPOINT=http://localhost:9222` and preflights). Do
NOT write adapter code that assumes the extension, and do NOT document the extension as the primary
path for a new tool.

## 2. Where the code lives

- **Iterate privately first:** `~/.opencli/clis/<site>/<command>.js` — loads at runtime, no build.
  Fastest loop while discovering the API/shape.
- **Promote to the repo:** `~/builds/OpenCLI/clis/<site>/<command>.js` — public, registers on
  `npm run build`.
- Per-site memory (endpoints, field maps, notes, fixtures): `~/.opencli/sites/<site>/`.

## 3. The adapter file model

Every command calls `cli({...})` imported from `@jackwener/opencli/registry` (errors from
`@jackwener/opencli/errors`). No third-party imports.

Browser-backed (the common case — reuses the logged-in session):
```js
// clis/<site>/<command>.js
import { cli, Strategy } from "@jackwener/opencli/registry";
import { AuthRequiredError, EmptyResultError } from "@jackwener/opencli/errors";

cli({
  site: "<site>",
  name: "<command>",
  strategy: Strategy.UI,        // or COOKIE / INTERCEPT, per your strategy note
  browser: true,
  args: [/* positional + option specs */],
  columns: [/* output column keys, in order */],
  // browser:true → signature is (page, args). (browser:false → (args) only.)
  func: async (page, args) => {
    // authenticated fetch INSIDE the page context (carries session cookies + CSRF):
    //   const rows = await page.evaluate(fetchJsonScript(url, headers));
    // map → return array of objects whose keys EXACTLY match `columns` (order included).
    // throw AuthRequiredError / EmptyResultError etc — never silently `return []`.
  },
});
```
Reference implementation to copy: `~/builds/OpenCLI/clis/linkedin/salesnav-inbox.js` (does a paginated
authenticated `salesApiMessagingThreads` fetch and emits `thread_id`/`thread_url` rows).

Pipeline / PUBLIC (no browser): `browser: false`, `func: async (args) => rows` — see
`clis/hackernews/top.js`.

Gotchas:
- `func` signature flips with `browser`: `(page, args)` vs `(args)`. Swapping silently makes external
  args `undefined`.
- Intermediate parsing object keys must NOT collide with any `columns` entry.

## 4. Workflow: recon → discover → implement → verify

Use the repo's bundled `opencli-adapter-author` skill for the full procedure. Condensed:
1. Preflight Brave on :9222 (`brave-cdp` skill if needed).
2. Recon: `opencli-cdp.sh browser analyze <url>` — classifies the site (SPA/JSON-XHR, SSR-inline,
   JSONP, token-auth, streaming).
3. Discover the data source (network XHR → page state → bundle → token → intercept). Validate the
   endpoint with a direct authenticated fetch (200 + non-empty JSON).
4. Write a one-line strategy note (which strategy class + why + evidence) before coding.
5. Implement the adapter (§3), iterating at `~/.opencli/clis/<site>/`.
6. Verify against the live logged-in session via the wrapper.

## 5. Build & register

```bash
cd ~/builds/OpenCLI && npm run build      # scans clis/** for cli({...}) and regenerates cli-manifest.json
```
Adding a `clis/<site>/<command>.js` that calls `cli({...})` auto-registers — never hand-edit
`cli-manifest.json`. A file that fails to import fails the build (manifest not written).

## 6. Test

```bash
npx vitest run --project adapter clis/<site>/<command>.test.js
```
Adapter tests live beside the command (`clis/<site>/<command>.test.js`); JSDOM fixtures go in
`clis/<site>/__fixtures__/<command>.html` (committed). Transient fetch samples →
`~/.opencli/sites/<site>/fixtures/` (never the repo tree). Assert on real output shape — alias/enum
mapping, column presence, error paths — not just "didn't crash."

## 7. Guardrails

- Read-only by default. Never click send/compose/connect or anything that posts/sends through a
  driven logged-in session unless Jono explicitly asks.
- Never echo cookies, CSRF tokens, or private bodies into output or tests; use synthetic fixtures.
- Keep new work scoped to the new adapter + its test + the regenerated manifest.
