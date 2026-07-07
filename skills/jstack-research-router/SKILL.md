---
name: jstack-research-router
description: >-
  Route research requests through Exa, Tavily, Jina, GitHub, xAI, and Apify lanes with local
  credential loading. Use when the user asks to research, look something up, discover or compare
  options, find sources, search repos/code, or check current facts — invoke at the START of any
  research, discovery, comparison, current-facts lookup, repo-finding, or source-collection
  request, before choosing a search tool.
---

# jstack Research Router

Use this skill at the start of any research, discovery, current-facts, comparison,
repo-finding, source-collection, or "look this up" request. It chooses the leanest
research lane before searching.

Do not save research into the second brain unless Jono explicitly asks to save/capture
it. Research output can be offered for saving afterward.

## Setup

Source local credentials before using authenticated lanes. Never print secrets.

```bash
export PATH="$HOME/.local/bin:$PATH"
set -a
. "$HOME/.hermes/.env" 2>/dev/null
. "$HOME/second-brain/.env" 2>/dev/null
. "$HOME/.config/last30days/.env" 2>/dev/null
set +a
```

`APIFY_API_TOKEN` should be set on this machine in `~/.hermes/.env` (Jono may call
this `.hermes.env`). If an Apify command says the token is missing, source that file
again or inspect the variable name without echoing the value.

Quick non-secret verification:

```bash
[ -n "${APIFY_API_TOKEN:-}" ] && echo "APIFY_API_TOKEN present"
```

## Routing Table

| Intent | Use | Command / tool |
|---|---|---|
| Semantic discovery, "find things like X," obscure sources, similar companies/tools/repos | Exa CLI first | `exa-search "<query>" 10 auto` |
| Ordinary web lookup with links/snippets | Tavily CLI first | `tvly search "<query>" --max-results 5` |
| Deep cited multi-source research | Tavily CLI | `tvly research "<topic>" --model pro -o report.md` |
| Pull/crawl/map/extract site content | Tavily CLI first | `tvly extract <url>` / `tvly crawl <url>` / `tvly map <url>` |
| Clean Markdown from one page when extraction is noisy | Jina Reader | `jina-reader <url>` or `curl -L "https://r.jina.ai/http://https://example.com/page"` |
| Search + fetch through Jina | Jina Reader | `curl -L "https://s.jina.ai/<url-encoded-query>"` |
| GitHub repo discovery | `gh` | `gh search repos "<terms>" --sort stars --limit 8 --json fullName,stargazersCount,description,updatedAt` |
| GitHub code discovery | `gh` | `gh search code "<symbol or phrase>" --limit 10` |
| X/Twitter posts and current reactions | xAI X Search | Hermes native `x_search`, or xAI Responses API with `$XAI_API_KEY` |
| Reddit threads/comments at scale, public Reddit 403s, bulk pulls | Apify `trudax/reddit-scraper-lite` | run-sync actor with `$APIFY_API_TOKEN` |
| Authenticated JS SPA extraction | Brave CDP | Use `brave-cdp` and extract DOM from the logged-in browser session |
| Save findings into second brain | second-brain workflow | Follow `~/second-brain/SKILL.md`; explicit confirmation required |

## Lane Notes

### Exa

Use for fuzzy discovery and finding sources similar to a seed.

```bash
exa-search "<query>" 10 auto
```

### Tavily

Use for ordinary search, extraction, crawl/map, and deep cited reports.

```bash
tvly search "<query>" --max-results 5
tvly research "<topic>" --model pro -o report.md
tvly extract <url>
tvly crawl <url>
tvly map <url>
```

If `tvly research --model pro` hits plan limits, stop retrying that command. Switch
remaining discovery to Exa and reserve Tavily for lightweight `extract` calls.

### Jina Reader

Use as a clean Markdown fallback.

```bash
jina-reader https://example.com/page
curl -L "https://r.jina.ai/http://https://example.com/page"
curl -L "https://s.jina.ai/your+search+query"
```

### GitHub

Use `gh` for GitHub-native discovery. Prefer repos with meaningful stars and recent
activity unless the code itself is the evidence.

```bash
gh search repos "<key terms>" --sort stars --limit 8 \
  --json fullName,stargazersCount,description,updatedAt

gh search code "<symbol or phrase>" --limit 10
```

### X / Twitter

Use Hermes native `x_search` when available. In raw shell/Codex/Claude, call the xAI
Responses API with `$XAI_API_KEY`, loaded from `~/.hermes/.env`.

Treat filtered X answers with no citations or URL annotations as unsourced.

### Reddit at Scale via Apify

Use when Reddit blocks public access, when comments matter, or when you need bulk
posts/comments. Actor: `trudax/reddit-scraper-lite`
(`https://apify.com/trudax/reddit-scraper-lite`). It is pay-per-result and uses
`APIFY_API_TOKEN`.

The token should already be in `~/.hermes/.env`; source Setup first. Do not paste the
token into chat or commit it into a skill.

Run-sync example:

```bash
curl -sS "https://api.apify.com/v2/acts/trudax~reddit-scraper-lite/run-sync-get-dataset-items?token=$APIFY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "searches": ["grey market peptides Thailand"],
    "sort": "relevance",
    "time": "month",
    "maxItems": 50,
    "maxComments": 20,
    "proxy": {"useApifyProxy": true}
  }'
```

Actor URL paths use `~`, not `/`, in actor ids: `trudax~reddit-scraper-lite`.
Confirm input fields against the actor input schema when behavior changes. Cite the
original Reddit thread URLs in the final answer.

## Rules

- Prefer explicit CLI tools over generic web tools when available.
- Multi-lane requests (e.g. web + GitHub + X/Reddit): run independent lanes in parallel —
  send the independent calls (or subagent launches) in one message, covering every lane the
  request needs, not just the first.
- Use Exa first for semantic discovery.
- Use Tavily first for ordinary lookup, source collection, pricing checks, and extraction.
- Use Jina as the clean extraction fallback.
- Use `gh` for GitHub-native discovery.
- Use xAI X Search for current X/Twitter discussion, but require citations for filtered claims.
- Use Apify with `$APIFY_API_TOKEN` for Reddit at scale or when Reddit blocks public access.
- Cite URLs back to Jono.
- Keep secrets in local env files, never in committed skill text.
- Second-brain writes require explicit save/capture confirmation.

## Next skills

| Next | When |
|------|------|
| `/jstack-last30days` | Jono wants current social/forum sentiment across Reddit, X, YouTube, TikTok, HN, GitHub, or Polymarket rather than a general research pass. |
| `/jstack-savetobrain` | Jono explicitly asks to save/capture the research result into the second brain. |
| `/jstack-brainwork` | Saved raw research should be compiled into wiki canon. |
