---
name: jstack-schedule-claude
description: Run or schedule a headless Claude Code session from any harness (Claude Code, Hermes, Codex). Use when Jono says /jstack-schedule-claude, "schedule a claude run", "run a claude prompt", "every day at 3am have claude do X", "kick off claude in <dir>", "launch claude headless", "send this to claude", or "continue claude session <id>". Two modes — run now (on demand) or schedule (registers a Hermes cron job that fires the prompt on a timer). It collects working directory, prompt, model, and session (fresh or existing); when scheduling it also asks whether the job is one-shot or recurring and when. Always runs claude with --dangerously-skip-permissions (autonomous), pins --session-id so runs are resumable, scheduled runs detach so they survive the cron timeout (40 min+ ok), and they report a start + a result message to the Hermes home channel. Invoke bare to be asked everything, or in natural language and it asks only for what is missing.
---

# jstack-schedule-claude

Spawn a non-interactive Claude Code run (`claude -p`) — now or on a schedule — fully autonomous
(`--dangerously-skip-permissions`), in a chosen directory, against a chosen model, in a fresh or
existing session. Deterministic scripts do the work; this skill's job is to **collect the inputs**
(asking only for what is missing) then call the right script.

- **Run now** → `scripts/run_claude.sh` (foreground or `--background`).
- **Schedule** → `scripts/schedule_claude.sh` (registers a Hermes cron job, `no_agent` mode).

Canonical scripts live at `~/jstack/skills/jstack-schedule-claude/scripts/` (symlinked into every
harness — call them at that path). Works from Claude Code, Hermes, or Codex — all just shell out.
From Claude Code the typical use is **schedule** (handing a run off to Hermes' always-on cron);
run-now from Claude Code is rarely useful since you could just run the prompt yourself.

> Deterministic scripts are the single source of truth. Never hand-assemble a `claude` or
> `hermes cron` command inline — always call the scripts. They hard-fail on any missing required
> input and tell you exactly what to ask for.

## Collecting inputs — bare vs natural language

**Determine the mode first:**
- "schedule", "every", "daily", "at 3am", "cron", any time/interval → **SCHEDULE**
- "now", "run it", "kick off", no time given → **RUN NOW**
- ambiguous → ask: "run it now, or schedule it?"

**If invoked bare (no arguments):** ask the user for everything the mode needs.
- SCHEDULE: ask **one-shot or recurring**, **when**, **model**, and the **prompt**. (Working
  directory defaults to the current directory — state the default and let them override. Session
  defaults to fresh.)
- RUN NOW: ask **working directory**, **model**, and the **prompt**.

**Always ask/confirm one-shot vs recurring explicitly — never infer it silently.** Then translate
the "when" into the schedule string:
- one-shot (the common case): "in 2 hours" → `2h`, "in 30 min" → `30m`, "tomorrow 9am" / "at 3pm" →
  an ISO **local** timestamp `YYYY-MM-DDTHH:MM:SS` (compute the date yourself).
- recurring: `every 2h`, or a cron expr like `0 9 * * *`.

Echo the resolved schedule back before registering (e.g. "one-shot — fires once ~2h from now, then
auto-cleans" or "recurring — every day at 9am"). If the user only gave a time without saying whether
it repeats, ask; most jobs are one-shot.

**If invoked with natural language** (e.g. "schedule a claude run in ~/jstack every day at 3am on
opus to tidy the brain"): extract whatever was provided and **ask only for the missing required
items**. Never guess the prompt, the schedule, or the model.

**Required before executing:**
| Mode | Required | Defaults |
|------|----------|----------|
| Run now  | working dir · prompt · model | session = fresh |
| Schedule | one-shot-or-recurring · when · prompt · model | dir = current dir · session = fresh · deliver = home channel |

Always ask the model explicitly (don't silently accept the script's sonnet default). Common ids:
`claude-opus-4-8` (most capable, priciest), `claude-sonnet-4-6` (balanced), `claude-haiku-4-5`
(cheap/fast). For long or pasted prompts, write the text to a temp file and pass `--prompt-file`.

## Mode A — Run now

```bash
~/jstack/skills/jstack-schedule-claude/scripts/run_claude.sh \
  --dir "<working-dir>" --model "<model-id>" --prompt "<prompt text>"
```

- Existing session (follow-up message): add `--session "<uuid>"`.
- Long prompt: `--prompt-file /tmp/claude-prompt.txt`.
- Don't block the turn on a long autonomous run: add `--background` (returns a pid + log path).
- List resumable sessions for a dir: `run_claude.sh --list --dir "<dir>"`.

## Mode B — Schedule (registers a Hermes cron job)

```bash
# one-shot (the common case): fire once, 2 hours from now
~/jstack/skills/jstack-schedule-claude/scripts/schedule_claude.sh \
  --schedule "2h" \
  --dir "<working-dir>" --model "<model-id>" \
  --prompt-file /tmp/claude-prompt.txt \
  --name "<short job name>"
```

- **Schedule forms** (one-shot vs recurring is auto-detected):
  - one-shot: `"30m"` / `"2h"` / `"1d"` (that far from now), or ISO `"2026-06-22T09:00:00"` (at a time)
  - recurring: `"every 2h"`, or cron `"0 9 * * *"`
  - **One-shots self-clean** — the job entry auto-removes after it fires, and the wrapper + prompt
    file delete themselves when the run completes. Don't pass `--repeat 1` by hand; it's automatic.
- Append to one long-running thread instead of a fresh session each fire: `--session "<uuid>"`.
- Delivery defaults to the **Hermes home channel** (bare `discord`); override with `--deliver <target>`
  (e.g. `discord:#ops`).
- Manage: `schedule_claude.sh --list` · `schedule_claude.sh --unschedule <job-id>` · or
  `hermes cron run|pause|remove <job-id>`.

## How a scheduled run behaves (important)

The Hermes cron scheduler kills a `no_agent` script after ~120 s. So the generated wrapper does
**not** run Claude inline — it **detaches** the run (`nohup`, fds redirected) and returns in
milliseconds. That means:

- **Long runs are fine** — a 40 min+ autonomous `/goal` keeps going after the 120 s cron cap and
  does not block other cron jobs. It survives a gateway restart (it reparents to launchd); it only
  pauses if the laptop sleeps.
- **Two messages per run** land in the delivery channel: a "🟢 started" line (when it fired, job
  name, model, dir) and, on completion, a "✅ done / ❌ exit N" report (model, dir, session id,
  exit code, and a tail of the result).
- **Watch a run live** by tailing the detached log printed at schedule time:
  `tail -f ~/.hermes/logs/jstack-schedule-claude/jsc-<slug>.detached.log`.

### Background-task wait ceiling (why runs can die "incomplete")

Headless `claude -p` has a shutdown guard interactive sessions don't: once the model's final
turn ends, it waits at most `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` for still-running
**background tasks** (background subagents, background bash), then **kills them and exits** —
stock default 600 s. A run that delegates a long task to a background subagent and ends its
turn to wait (the normal `/goal` + `/loop` pattern) gets truncated at +10 min, exits 0 with no
result text, and looks "done" while the real work was killed mid-flight.

`run_claude.sh` therefore raises the ceiling to **2 h** for every launch. Tune it with
`JSTACK_SC_BG_WAIT_MS` (env → `~/.jstack/config.env` → default `7200000`); `0` = wait forever
(avoid: a leftover dev server then keeps the run alive indefinitely and the result never posts).

- A result report of **"⚠️ bg-capped (incomplete)"** means the ceiling still fired: background
  work was terminated and the session has pending task notifications queued. `claude --resume
  <session-id>` delivers them and the session picks up where it was killed.
- This is a `claude -p` behavior, **not** a `--resume` limitation — resuming a bg-capped
  session and watching it continue is the recovery working as designed.

## Monitoring vs `/resume` while a run is in progress

If a session is **still running** and you want to check on it, **tail the log — do not `/resume`.**

- `claude --resume <id>` starts a *separate* process; it does **not** signal or stop the running
  detached run (no kill). So resuming will not halt the work.
- But two processes writing the same session transcript concurrently is unsafe (interleaved/corrupt
  state). So while it's live: watch the detached log (above) or the per-session log
  `~/.hermes/logs/jstack-schedule-claude/<session-id>.log`.
- **Resume only after it finishes** — the "✅ done" message (and exit line in the log) tells you when.
  Then `cd <dir> && claude --resume <session-id>` to inspect or continue interactively.

## Reporting back to the user

- **When scheduling:** give a **brief** confirmation only — job name, directory, schedule, model,
  job id. **Do not echo the full prompt** back; it has already been saved.
- **When running now (foreground):** report the session id, dir, model, fresh/existing, log path,
  result / exit code, and the follow-up command to message the same session.

## Notes / guardrails

- `--dangerously-skip-permissions` is intentional and always on (autonomous, no questions) — it is
  appended unconditionally by `run_claude.sh`. Only point runs at directories Jono owns.
- `--session` (resume) and `--fresh` are mutually exclusive; the launcher rejects both.
- Cost follows the model — confirm before scheduling a long `/goal` loop on Opus.
- **Goal prompts must clean up their background processes.** The headless process cannot exit
  while a tracked background task (dev server, watcher) is still alive — it idles until the
  wait ceiling (2 h) before reporting. Prompts that start servers should say "kill any
  background processes you started before finishing" (verify with a curl/log check instead of
  leaving the server running as a stop condition).
- Scheduled runs fire from the always-on Hermes gateway, so they don't depend on the macOS crontab
  (no Full Disk Access wall) and survive sleep/restart.

## Next skills

| Next | When |
|------|------|
| `continue-claude-session` | Jono wants a finished run's *transcript* pulled into Hermes/Codex as Markdown to catch up, not to launch a new run. |

Otherwise standalone — no required next step.
