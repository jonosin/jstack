---
title: CDP browser setup for send_batch.js
---

# CDP browser setup

`send_batch.js` drives your real LinkedIn account via Chrome DevTools Protocol (CDP). You must launch Brave or Chrome with remote debugging enabled and be logged into LinkedIn Sales Navigator.

## Step 1: quit and relaunch the browser with CDP

**Brave (macOS):**
```bash
/Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser \
  --remote-debugging-port=9222 \
  --profile-directory="Default"
```

**Chrome (macOS):**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --profile-directory="Default"
```

Open a new terminal first to run the command; the browser must be fully quit before relaunching (Cmd+Q, not just closing the window).

## Step 2: log in and open Sales Navigator

In the CDP browser window:
1. Log into linkedin.com with your sending account.
2. Navigate to linkedin.com/sales and open any Sales Navigator search or lead page. Leave this tab open.

## Step 3: verify CDP is active

```bash
curl -s localhost:9222/json/version
```

Expected: a JSON object with `"Browser"`, `"webSocketDebuggerUrl"`, etc. If you get `connection refused`, the browser was not launched with the flag.

If you use a non-default port, set:
```bash
export CDP_URL=http://localhost:<PORT>
```

## Risks and safe operation

This drives your **real** LinkedIn account.

- **InMail credits are spent** on every credit-required send (openProfile=False leads are free).
- **Rate limits and account restriction** are real. LinkedIn monitors unusual send velocity.
- `send_batch.js` auto-halts and saves a screenshot to `<DIR>/cdp-shots/` on any restriction language or unverified send. The queue is fully resumable.
- **ALWAYS canary first**: run with a batch size of 3 and inspect `batch_result.json` before sending larger batches.
- Pause between batches (~20 sends). Do not send more than ~50 per day unless your account has high trust.

## Recommended workflow

```bash
# 1. canary
LINKEDIN_SEND_DIR=/path/to/campaign node scripts/send_batch.js 3

# 2. inspect result
cat /path/to/campaign/batch_result.json

# 3. if clean, continue in batches of ~20
LINKEDIN_SEND_DIR=/path/to/campaign node scripts/send_batch.js 20
```
