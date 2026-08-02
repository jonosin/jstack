---
name: jstack-linkedin-salesnav
description: Use when extracting or enriching LinkedIn Sales Navigator leads from an already-open Sales Navigator people search tab via the local OpenCLI build, including requests like "extract 100 leads from the current Sales Nav tab" or "pull enriched Sales Navigator profiles".
---

# jstack-linkedin-salesnav

Use this skill for LinkedIn Sales Navigator extraction through the local OpenCLI build at `~/builds/OpenCLI`, attached to Jono's already-running Brave session over CDP on port `9222`.

## Assumptions

- Brave is running with Chrome DevTools Protocol on `http://localhost:9222`.
- A LinkedIn Sales Navigator **people search results** tab is already open in Brave when extracting leads from the current search.
- The user is logged into LinkedIn and has Sales Navigator access.
- Browser Bridge is **not required** for this workflow. Default to CDP, not the Browser Bridge extension.

Before any Sales Nav command, preflight CDP:

```bash
curl -sf http://localhost:9222/json/version >/dev/null
```

If that fails, use the Brave CDP recovery path from the `brave-cdp` skill (`brave-cdp-relaunch` or `~/.claude/skills/brave-cdp/references/brave-cdp-relaunch.sh`) and retry the preflight. Do not ask the user to install/connect Browser Bridge for this workflow.

If no Sales Navigator search results tab is open, pause and tell the user to open the tab where the results are shown.

## Required OpenCLI CDP Environment

Prefix OpenCLI Sales Navigator commands with:

```bash
OPENCLI_CDP_ENDPOINT=http://localhost:9222 OPENCLI_CDP_TARGET='sales'
```

For current-search extraction, prefer the narrower target:

```bash
OPENCLI_CDP_ENDPOINT=http://localhost:9222 OPENCLI_CDP_TARGET='sales/search'
```

`OPENCLI_CDP_TARGET` is a target-selection hint for the open Brave tab. Use `sales/search` for people-search extraction, `sales/inbox` or `sales` for inbox/thread work.

## Extract Leads From The Current Tab

Run:

```bash
OPENCLI_CDP_ENDPOINT=http://localhost:9222 OPENCLI_CDP_TARGET='sales/search' \
  ~/jstack/skills/jstack-linkedin-salesnav/scripts/salesnav-current-search.sh --limit 100 --out /tmp/salesnav-leads.json
```

This calls:

```bash
OPENCLI_CDP_ENDPOINT=http://localhost:9222 OPENCLI_CDP_TARGET='sales/search' \
  node ~/builds/OpenCLI/dist/src/main.js linkedin salesnav-current-search --limit 100 --delay-ms 250 -f json
```

The OpenCLI command reads either the `query=` payload or the `savedSearchId=` from the open Sales Navigator tab, pages through `salesApiLeadSearch` with `start` offsets, and enriches each row through `salesApiProfiles`. It does not click the Sales Navigator UI pagination controls. Saved-search tabs use LinkedIn's `q=savedSearchId&savedSearchId=...` API form; treat them as first-class current-search tabs.

Output rows include:

- identity: `firstName`, `lastName`, `name`, `publicIdentifier`, `linkedinUrl`, `id`, `objectUrn`, `entityUrn`
- opener fuel: `headline`, `about`, `industry`, `skills`
- role history: `currentPosition`, `positions`, `experience`, `educations`, `education`
- reachability: `inmailRestriction`, `openProfile`, `openLink`, `premium`, `openToWork`
- extra sections when Sales Nav exposes them: `contactInfo`, `certifications`, `projects`, `organizations`, `publications`, `languages`, `patents`, `courses`

Use `--slim` only when the user wants search-card rows without per-profile enrichment.

## Pull One Profile

For a single lead URL or recipient URN:

```bash
OPENCLI_CDP_ENDPOINT=http://localhost:9222 OPENCLI_CDP_TARGET='sales' \
  node ~/builds/OpenCLI/dist/src/main.js linkedin salesnav-profile "https://www.linkedin.com/sales/lead/PROFILE,NAME_SEARCH,TOKEN" -f json
```

## Check Replies / Fetch Threads

Use the inbox `--filter` aliases to find replies, then `salesnav-thread` to read a conversation.

- Accepted InMail replies (the API enum `INMAIL_ACCEPTED`):

  ```bash
  OPENCLI_CDP_ENDPOINT=http://localhost:9222 OPENCLI_CDP_TARGET='sales' \
    node ~/builds/OpenCLI/dist/src/main.js linkedin salesnav-inbox --filter inmail-accepted --limit 20 -f json
  ```

- Fresh **Unread** replies (the API enum `UNREAD`):

  ```bash
  OPENCLI_CDP_ENDPOINT=http://localhost:9222 OPENCLI_CDP_TARGET='sales' \
    node ~/builds/OpenCLI/dist/src/main.js linkedin salesnav-inbox --filter unread --limit 20 -f json
  ```

Other aliases: `all`, `sent`, `inmail-awaiting-response`, `inmail-declined`, `archived`. `--unread-only` stays as a backward-compatible client-side post-filter.

When the user says "check replies," pick the filter from context: default to `inmail-accepted` for accepted InMail replies and `unread` for fresh unread replies.

Inbox rows carry `thread_url`/`thread_id`. Unless the user only asks for counts, fetch at least one matching thread to read its message history:

```bash
OPENCLI_CDP_ENDPOINT=http://localhost:9222 OPENCLI_CDP_TARGET='sales' \
  node ~/builds/OpenCLI/dist/src/main.js linkedin salesnav-thread "<thread_url_or_id>" -f json
```

Decide how many threads to fetch based on current context and need (one for a quick look, several when the user wants to triage or draft replies across multiple conversations).

## Failure Handling

- CDP preflight fails: run the Brave CDP recovery path (`brave-cdp-relaunch`), then retry. Browser Bridge is not required for this workflow.
- No search tab: tell the user to open the Sales Navigator people search results tab, then rerun.
- Auth/Sales Nav failure: tell the user to log into LinkedIn/Sales Navigator in the controlled browser.
- Partial profile gaps: keep the row. Sales Nav does not expose every public-profile field; do not invent missing follower counts, email addresses, or parsed country fields.

## Next skills

| Next | When |
|------|------|
| `jstack-linkedin-send` | Extracted leads are ready to become a `prospects.csv` and get sent. |
| `brave-cdp` | CDP preflight fails and the recovery/relaunch path is needed. |
