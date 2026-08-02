#!/usr/bin/env bash
# jstack-schedule-cc (scheduler) — register a Hermes cron job that runs a headless
# Claude Code prompt on a schedule, via the deterministic run_claude.sh launcher in
# --no-agent mode (Hermes is only the trigger; Claude Code does the work and its result
# is delivered verbatim).
#
# Usage:
#   schedule_claude.sh --schedule "<cron|interval>" --dir <path> --model <model> \
#       (--prompt "<text>" | --prompt-file <path>) \
#       [--session <uuid>] [--name <name>] [--deliver <target>] [--repeat <n>]
#
#   schedule_claude.sh --list                 # list scheduled claude jobs
#   schedule_claude.sh --unschedule <job-id>  # remove a scheduled job
#   schedule_claude.sh --help
#
# Schedule forms:
#   one-shot : "30m" / "2h" / "1d" (fires that far from now), or ISO "2026-06-22T09:00:00" (at a time)
#   recurring: "every 2h", or cron "0 9 * * *"
# One-shots are auto-detected and self-clean: the job entry auto-removes after it fires, and the
# wrapper + prompt file are deleted when the run completes.
# Delivery default: discord (Hermes home channel). Each fire starts a FRESH resumable session
# unless --session pins one to append to. The generated job DETACHES the run so long sessions
# (40 min+) survive the cron script timeout; a start message and a result message are delivered.
#
# Works from any harness (Claude Code or Hermes) — it only shells out to the hermes CLI.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"   # -P resolves symlinks to the canonical repo path
RUN="$SCRIPT_DIR/run_claude.sh"
HSCRIPTS="$HOME/.hermes/scripts"
PY="${HERMES_PY:-$HOME/.hermes/hermes-agent/venv/bin/python}"
hermes() { "$PY" -m hermes_cli.main "$@"; }

die() { printf 'ERROR: %s\n' "$1" >&2; exit 1; }

# Default delivery: the Hermes home channel. Bare "discord" resolves to the home channel
# (no channel id needed), matching `hermes send -t discord`. Override with --deliver / $HERMES_DELIVER.
DELIVER="${HERMES_DELIVER:-discord}"
SCHEDULE="" DIR="" MODEL="claude-sonnet-4-6" PROMPT="" PROMPT_FILE="" SESSION="" NAME="" REPEAT="" LIST="" UNSCHED=""

while [ $# -gt 0 ]; do
  case "$1" in
    --schedule)    SCHEDULE="${2:-}"; shift 2;;
    --dir)         DIR="${2:-}"; shift 2;;
    --model)       MODEL="${2:-}"; shift 2;;
    --prompt)      PROMPT="${2:-}"; shift 2;;
    --prompt-file) PROMPT_FILE="${2:-}"; shift 2;;
    --session)     SESSION="${2:-}"; shift 2;;
    --name)        NAME="${2:-}"; shift 2;;
    --deliver)     DELIVER="${2:-}"; shift 2;;
    --repeat)      REPEAT="${2:-}"; shift 2;;
    --list)        LIST=1; shift 1;;
    --unschedule)  UNSCHED="${2:-}"; shift 2;;
    -h|--help)     grep '^#' "$0" | grep -v '^#!' | sed 's/^# \{0,1\}//'; exit 0;;
    *)             die "unknown arg: $1 (use --help)";;
  esac
done

[ -x "$PY" ] || die "hermes python not found at $PY (set HERMES_PY)"

# --- management modes --------------------------------------------------------
if [ -n "$LIST" ]; then
  echo "Scheduled claude jobs (name contains 'jstack-schedule-cc'):"
  hermes cron list 2>&1 | grep -iE 'jstack-schedule-cc|jsc-' || echo "(none)"
  exit 0
fi
if [ -n "$UNSCHED" ]; then
  hermes cron remove "$UNSCHED" 2>&1
  exit $?
fi

# --- validate required -------------------------------------------------------
[ -n "$SCHEDULE" ] || die "--schedule is required (e.g. \"0 3 * * *\", \"every 2h\", \"30m\")"
[ -n "$DIR" ]      || die "--dir is required"
[ -d "$DIR" ]      || die "working directory does not exist: $DIR"
[ -x "$RUN" ]      || die "launcher not found/executable: $RUN"
if [ -n "$PROMPT_FILE" ]; then
  [ -f "$PROMPT_FILE" ] || die "--prompt-file not found: $PROMPT_FILE"
  PROMPT="$(cat "$PROMPT_FILE")"
fi
[ -n "$PROMPT" ] || die "a prompt is required (--prompt \"...\" or --prompt-file <path>)"
[ -n "$MODEL" ]  || die "--model is required"

# --- slug + materialize the prompt ------------------------------------------
mkdir -p "$HSCRIPTS"
if [ -n "$NAME" ]; then
  SLUG="$(printf '%s' "$NAME" | tr 'A-Z' 'a-z' | tr -cs 'a-z0-9' '-' | sed 's/^-//; s/-$//')"
fi
[ -n "${SLUG:-}" ] || SLUG="claude-$(date +%Y%m%d-%H%M%S)"
JOBNAME="${NAME:-jstack-schedule-cc:$SLUG}"
PROMPTFILE="$HSCRIPTS/jsc-$SLUG.prompt.txt"
WRAPPER="$HSCRIPTS/jsc-$SLUG.sh"
DETDIR="$HOME/.hermes/logs/jstack-schedule-cc"
DETLOG="$DETDIR/jsc-$SLUG.detached.log"
printf '%s\n' "$PROMPT" > "$PROMPTFILE"

# --- one-shot detection ------------------------------------------------------
# Duration ("30m"/"2h"/"1d") or ISO timestamp ("2026-06-22T09:00:00") => fires once.
# "every ..." or a 5+-field cron expr => recurring. One-shots auto-clean: the job entry
# self-removes (via --repeat 1, which deletes on completion) and the run deletes its own
# wrapper + prompt file when done.
is_oneshot() {
  case "$1" in [Ee][Vv][Ee][Rr][Yy]\ *) return 1;; esac   # "every ..." = recurring
  if [ "$(printf '%s' "$1" | awk '{print NF}')" -ge 5 ] && printf '%s' "$1" | grep -qE '^[0-9*,/ -]+$'; then
    return 1   # 5+-field cron expr = recurring
  fi
  return 0      # duration or timestamp = one-shot
}
ONESHOT=0; is_oneshot "$SCHEDULE" && ONESHOT=1
[ "$ONESHOT" = 1 ] && [ -z "$REPEAT" ] && REPEAT=1            # auto-remove the spent job entry
CLEANUP_ARG=""
[ "$ONESHOT" = 1 ] && CLEANUP_ARG="--cleanup-files \"$WRAPPER $PROMPTFILE\" "

# --- generate the no_agent wrapper cron will run -----------------------------
# The cron scheduler runs no_agent scripts with subprocess.run(timeout=~120s) and only
# SIGKILLs the direct script process on timeout (no process-group kill). So the wrapper
# DETACHES the real run (nohup, fds redirected off the captured pipe): the launcher survives
# the cap and runs as long as the task needs. The wrapper returns immediately, printing a
# "started" line Hermes delivers to the home channel; the detached run posts its result
# there on completion via run_claude.sh --notify.
SESSION_ARG=""
[ -n "$SESSION" ] && SESSION_ARG="--session \"$SESSION\" "
{
  echo '#!/usr/bin/env bash'
  echo "# Auto-generated by jstack-schedule-cc $(date '+%Y-%m-%d %H:%M:%S %Z'). Edit via the skill, not by hand."
  echo "# Detaches the real Claude run so it survives the ~120s cron script timeout; the run"
  echo "# posts its result to the delivery target on completion. Watch a run with:"
  echo "#   tail -f $DETLOG"
  echo "mkdir -p \"$DETDIR\""
  echo "echo \"🟢 jstack-schedule-cc — '$JOBNAME' started \$(date '+%Y-%m-%d %H:%M %Z') · model $MODEL · dir $DIR. Detached; result posts here on completion.\""
  echo "nohup \"$RUN\" --dir \"$DIR\" --model \"$MODEL\" --prompt-file \"$PROMPTFILE\" ${SESSION_ARG}${CLEANUP_ARG}--notify \"$DELIVER\" --label \"$JOBNAME\" </dev/null >>\"$DETLOG\" 2>&1 &"
  echo "disown 2>/dev/null || true"
  echo "exit 0"
} > "$WRAPPER"
chmod +x "$WRAPPER"

# --- register the cron job ---------------------------------------------------
set -- cron create "$SCHEDULE" --no-agent --script "jsc-$SLUG.sh" --workdir "$DIR" --name "$JOBNAME" --deliver "$DELIVER"
[ -n "$REPEAT" ] && set -- "$@" --repeat "$REPEAT"
echo "Registering: hermes $*"
OUT="$(hermes "$@" 2>&1)"; RC=$?
echo "$OUT"
[ "$RC" -eq 0 ] || die "hermes cron create failed (rc=$RC)"

JOBID="$(printf '%s' "$OUT" | grep -oE '[0-9a-f]{12}' | head -1)"
echo "------------------------------------------------------------------"
echo "Scheduled. name=$JOBNAME  schedule=$SCHEDULE  model=$MODEL  deliver=$DELIVER"
echo "  wrapper : $WRAPPER"
echo "  prompt  : $PROMPTFILE"
echo "  log     : $DETLOG  (tail -f to watch a run live)"
echo "  runs    : detached — survives the ~120s cron cap; posts a start + a result message to $DELIVER"
[ "$ONESHOT" = 1 ] && echo "  type    : one-shot — job auto-removes after firing; wrapper + prompt self-delete on completion" \
                   || echo "  type    : recurring — wrapper + prompt persist for every fire"
[ -n "$SESSION" ] && echo "  session : $SESSION (appends each run)" || echo "  session : fresh per run"
[ -n "$JOBID" ] && {
  echo "  job id  : $JOBID"
  echo "Manage:  hermes cron run $JOBID   |   hermes cron pause $JOBID   |   hermes cron remove $JOBID"
  echo "Or:      $0 --unschedule $JOBID"
}
exit 0
