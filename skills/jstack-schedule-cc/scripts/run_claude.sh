#!/usr/bin/env bash
# jstack-schedule-cc — deterministic launcher for headless Claude Code (`claude -p`).
# ALWAYS runs with -p and --dangerously-skip-permissions (autonomous, no prompts).
#
# Usage:
#   run_claude.sh --dir <path> --model <model> (--prompt "<text>" | --prompt-file <path>)
#                 [--session <existing-uuid> | --fresh [uuid]] [--background]
#                 [--notify <target>] [--label <name>]
#   run_claude.sh --list --dir <path>     # list recent resumable sessions for a dir
#   run_claude.sh --help
#
# Session modes (mutually exclusive):
#   (default)        fresh session, new generated uuid
#   --fresh [uuid]   fresh session; pin a specific uuid if given
#   --session <id>   resume / send another message to an EXISTING session (claude -r <id>)
#
# --notify <target>  on completion, post a result report (status/when/model/dir/session/
#                    exit + result tail) via `hermes send -t <target>` (e.g. "discord" =
#                    Hermes home channel). Used by scheduled runs to report back.
# --label <name>     human label used in the notification subject.
#
# Always-on flags: -p (headless) and --dangerously-skip-permissions.
# Override the binary with CLAUDE_BIN; defaults to ~/.local/bin/claude.
# Background-task wait ceiling: claude -p kills background tasks that are still
# running N ms after the final turn ends (stock default 600000 = 10 min — too short
# for runs that delegate to background subagents). This launcher raises it to 2 h;
# tune via JSTACK_SC_BG_WAIT_MS (env or ~/.jstack/config.env) or export
# CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS directly. 0 = wait indefinitely.
set -uo pipefail

CLAUDE="${CLAUDE_BIN:-$HOME/.local/bin/claude}"
HERMES_PY="${HERMES_PY:-$HOME/.hermes/hermes-agent/venv/bin/python}"
LOGDIR="$HOME/.hermes/logs/jstack-schedule-cc"

die() { printf 'ERROR: %s\n' "$1" >&2; exit 1; }

DIR="" MODEL="claude-sonnet-4-6" PROMPT="" PROMPT_FILE="" SESSION="" FRESH="" FRESH_ID="" LIST="" BACKGROUND="" NOTIFY="" LABEL="" CLEANUP_FILES=""

while [ $# -gt 0 ]; do
  case "$1" in
    --dir)         DIR="${2:-}"; shift 2;;
    --model)       MODEL="${2:-}"; shift 2;;
    --prompt)      PROMPT="${2:-}"; shift 2;;
    --prompt-file) PROMPT_FILE="${2:-}"; shift 2;;
    --session)     SESSION="${2:-}"; shift 2;;
    --fresh)       FRESH=1
                   if [ $# -ge 2 ] && [ "${2#--}" = "$2" ]; then FRESH_ID="$2"; shift 2; else shift 1; fi;;
    --notify)      NOTIFY="${2:-}"; shift 2;;
    --label)       LABEL="${2:-}"; shift 2;;
    --cleanup-files) CLEANUP_FILES="${2:-}"; shift 2;;   # space-separated paths to rm on completion (one-shot self-clean)
    --list)        LIST=1; shift 1;;
    --background|--bg) BACKGROUND=1; shift 1;;
    -h|--help)     grep '^#' "$0" | grep -v '^#!' | sed 's/^# \{0,1\}//'; exit 0;;
    *)             die "unknown arg: $1 (use --help)";;
  esac
done

[ -x "$CLAUDE" ] || die "claude binary not found/executable at $CLAUDE (set CLAUDE_BIN)"

# Encode a project dir the way Claude Code names its transcript folder: every '/' -> '-'.
# Best-effort helper for --list (unusual chars in a path may not match exactly).
proj_dir() { printf '%s' "$HOME/.claude/projects/$(printf '%s' "$1" | sed 's#/#-#g')"; }

# --- list mode ---------------------------------------------------------------
if [ -n "$LIST" ]; then
  [ -n "$DIR" ] || die "--list requires --dir"
  PD="$(proj_dir "$DIR")"
  [ -d "$PD" ] || { echo "(no sessions yet for $DIR)"; exit 0; }
  echo "Recent resumable sessions for $DIR:"
  ls -t "$PD"/*.jsonl 2>/dev/null | head -10 | while read -r f; do
    id="$(basename "$f" .jsonl)"
    ts="$(date -r "$f" '+%Y-%m-%d %H:%M')"
    printf '  %s   %s\n' "$ts" "$id"
  done
  exit 0
fi

# --- run-mode validation -----------------------------------------------------
[ -n "$DIR" ] || die "--dir is required"
[ -d "$DIR" ] || die "working directory does not exist: $DIR"
if [ -n "$PROMPT_FILE" ]; then
  [ -f "$PROMPT_FILE" ] || die "--prompt-file not found: $PROMPT_FILE"
  PROMPT="$(cat "$PROMPT_FILE")"
fi
[ -n "$PROMPT" ] || die "a prompt is required (--prompt \"...\" or --prompt-file <path>)"
[ -n "$MODEL" ]  || die "--model is required"

# --- background-task wait ceiling (print mode) --------------------------------
# After the final turn ends, `claude -p` waits for still-running background tasks
# (background subagents, background bash) at most CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS,
# then KILLS them and exits. The stock default (600000 = 10 min) truncates long
# autonomous runs that delegate work to background subagents — a subagent that needs
# >10 min after the orchestrator's turn ends gets terminated mid-flight.
# Resolution: caller-exported env var > JSTACK_SC_BG_WAIT_MS (env or
# ~/.jstack/config.env) > 7200000 (2 h). 0 = wait indefinitely (risky: a leftover
# dev server keeps the run alive forever, so the completion notify never fires).
if [ -z "${CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS:-}" ]; then
  BGW="${JSTACK_SC_BG_WAIT_MS:-}"
  if [ -z "$BGW" ] && [ -f "$HOME/.jstack/config.env" ]; then
    BGW="$(sed -n 's/^JSTACK_SC_BG_WAIT_MS=//p' "$HOME/.jstack/config.env" | tail -1)"
  fi
  CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS="${BGW:-7200000}"
fi
export CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS

# --- resolve session ---------------------------------------------------------
if [ -n "$SESSION" ] && [ -n "$FRESH" ]; then
  die "choose ONE: --session <id> (resume existing) or --fresh (new). Not both."
fi
SESSION_ARGS=()
if [ -n "$SESSION" ]; then
  MODE="resume existing session"
  SID="$SESSION"
  SESSION_ARGS=(-r "$SID")
else
  MODE="fresh session"
  if [ -n "$FRESH_ID" ]; then SID="$FRESH_ID"; else SID="$(uuidgen | tr 'A-Z' 'a-z')"; fi
  SESSION_ARGS=(--session-id "$SID")
fi

mkdir -p "$LOGDIR"
LOG="$LOGDIR/$SID.log"

# --- header ------------------------------------------------------------------
{
  echo "=================================================================="
  echo "jstack-schedule-cc  @ $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "  dir     : $DIR"
  echo "  model   : $MODEL"
  echo "  mode    : $MODE"
  echo "  session : $SID"
  echo "  flags   : -p --dangerously-skip-permissions --model $MODEL ${SESSION_ARGS[*]}"
  echo "  bg-wait : ${CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS}ms ceiling for background tasks after final turn (0 = forever)"
  echo "=================================================================="
} | tee -a "$LOG"

run() {
  cd "$DIR" || die "cannot cd into $DIR"
  "$CLAUDE" -p "$PROMPT" \
    --model "$MODEL" \
    "${SESSION_ARGS[@]}" \
    --dangerously-skip-permissions 2>&1
}

# Humanize a duration in seconds -> "1h 5m 3s" / "5m 3s" / "3s".
human_elapsed() {
  local s="$1" h m
  h=$(( s / 3600 )); m=$(( (s % 3600) / 60 )); s=$(( s % 60 ))
  local out=""
  [ "$h" -gt 0 ] && out="${h}h "
  { [ "$h" -gt 0 ] || [ "$m" -gt 0 ]; } && out="${out}${m}m "
  printf '%s%ss' "$out" "$s"
}

# Post a completion report to Hermes (used by scheduled/detached runs). $1=rc $2=outfile
notify_home() {
  [ -n "$NOTIFY" ] || return 0
  [ -x "$HERMES_PY" ] || { echo "(notify skipped: hermes python not found at $HERMES_PY)" >>"$LOG"; return 0; }
  local rc="$1" out="$2" status subj elapsed capped=""
  elapsed="$(human_elapsed "$(( $(date +%s) - ${RUN_START:-$(date +%s)} ))")"
  grep -q 'Background tasks still running after' "$out" 2>/dev/null && capped=1
  if [ "$rc" -ne 0 ]; then status="❌ exit $rc"
  elif [ -n "$capped" ]; then status="⚠️ bg-capped (incomplete)"
  else status="✅ done"; fi
  subj="$status · ${LABEL:-claude run} · ${elapsed} · $(date '+%Y-%m-%d %H:%M %Z')"
  {
    echo "model: $MODEL · dir: $DIR"
    echo "session: $SID"
    echo "resume:  cd \"$DIR\" && claude --resume $SID"
    echo "exit: $rc · elapsed: $elapsed · log: $LOG"
    [ -n "$capped" ] && echo "⚠️ hit the background-task wait ceiling (${CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS}ms): background work was killed mid-flight and the run is INCOMPLETE. Resume the session to continue it — pending task notifications are still queued."
    echo
    echo "----- result (tail) -----"
    tail -c 1500 "$out" 2>/dev/null
  } | "$HERMES_PY" -m hermes_cli.main send -t "$NOTIFY" -s "$subj" -q >>"$LOG" 2>&1 \
    || echo "(notify: hermes send failed — see log)" >>"$LOG"
}

# Run once, capture output to a temp file, log it, return claude's exit code via global RC.
run_capture() {
  local out="$1"
  RUN_START="$(date +%s)"
  run >"$out" 2>&1
  RC=$?
  {
    echo "------------------------------------------------------------------"
    echo "[exit $RC]  session=$SID  ·  elapsed $(human_elapsed "$(( $(date +%s) - RUN_START ))")  @ $(date '+%Y-%m-%d %H:%M:%S')"
  } >>"$out"
}

# --- background mode ---------------------------------------------------------
if [ -n "$BACKGROUND" ]; then
  (
    TMPOUT="$(mktemp -t jsc-out.XXXXXX)"
    run_capture "$TMPOUT"
    cat "$TMPOUT" >>"$LOG"
    notify_home "$RC" "$TMPOUT"
    rm -f "$TMPOUT"
    [ -n "$CLEANUP_FILES" ] && rm -f $CLEANUP_FILES 2>/dev/null
  ) &
  PID=$!
  echo "Launched in background. pid=$PID"
  echo "  log     : $LOG"
  echo "  session : $SID"
  [ -n "$NOTIFY" ] && echo "  notify  : $NOTIFY (on completion)"
  echo "Resume later:  (cd \"$DIR\" && \"$CLAUDE\" --resume $SID)"
  exit 0
fi

# --- foreground --------------------------------------------------------------
TMPOUT="$(mktemp -t jsc-out.XXXXXX)"
run_capture "$TMPOUT"
tee -a "$LOG" < "$TMPOUT"          # show + persist
echo "Send another message to THIS session:" | tee -a "$LOG"
echo "  $0 --dir \"$DIR\" --model \"$MODEL\" --session $SID --prompt \"...\"" | tee -a "$LOG"
echo "Open it interactively:  (cd \"$DIR\" && \"$CLAUDE\" --resume $SID)" | tee -a "$LOG"
notify_home "$RC" "$TMPOUT"
rm -f "$TMPOUT"
[ -n "$CLEANUP_FILES" ] && rm -f $CLEANUP_FILES 2>/dev/null   # one-shot self-clean: remove wrapper + prompt
exit "$RC"
