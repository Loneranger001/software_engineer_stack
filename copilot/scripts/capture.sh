#!/bin/sh
# capture.sh — run a verification command, keep its FULL output on disk, and
# print only a bounded summary (exit code, line count, last N lines, matched
# error lines). The summary is what goes into the evidence file and the
# agent's context; the raw log is the audit trail, opened only when needed.
#
# Usage: capture.sh <evidence-dir> <name> [--tail N] [--grep REGEX] -- <command> [args...]
#   evidence-dir  the task's evidence/ directory (created if missing)
#   name          log name; output goes to <evidence-dir>/raw/<name>.log
#   --tail N      lines of output to show (default 40)
#   --grep REGEX  also show every line matching REGEX (extended regex), capped
#                 at 40 — e.g. 'ORA-|PLS-|SP2-|ERROR|FAILED|Traceback'
#
# Exits with the command's own exit code, so callers still see failure.
# stdin is /dev/null: a sqlplus script without EXIT ends instead of hanging.
# Arguments equal to or containing $SES_DB_CONN are redacted in the recorded
# command line. The command's OUTPUT is not redacted — keep secrets out of it
# (wallet/OS auth, no echoing connect strings).
set -u

DIR="${1:?usage: capture.sh <evidence-dir> <name> [--tail N] [--grep RE] -- cmd...}"
NAME="${2:?usage: capture.sh <evidence-dir> <name> [--tail N] [--grep RE] -- cmd...}"
shift 2
TAIL=40
GREP=""
while [ $# -gt 0 ]; do
  case "$1" in
    --tail) TAIL="${2:?--tail needs a number}"; shift 2 ;;
    --grep) GREP="${2:?--grep needs a regex}"; shift 2 ;;
    --) shift; break ;;
    *) echo "error: expected options then -- <command>, got '$1'" >&2; exit 2 ;;
  esac
done
[ $# -gt 0 ] || { echo "error: no command after --" >&2; exit 2; }
case "$TAIL" in ''|*[!0-9]*) echo "error: --tail must be a number" >&2; exit 2 ;; esac
case "$NAME" in *[!A-Za-z0-9._-]*) echo "error: name may only contain letters, digits, . _ -" >&2; exit 2 ;; esac

mkdir -p "$DIR/raw" || exit 2
LOG="$DIR/raw/$NAME.log"

# recorded command line, with the DB connect string redacted
CMDLINE=""
for a in "$@"; do
  if [ -n "${SES_DB_CONN:-}" ]; then
    case "$a" in
      "$SES_DB_CONN") a='<SES_DB_CONN>' ;;
      *"$SES_DB_CONN"*) a='<redacted: contains SES_DB_CONN>' ;;
    esac
  fi
  CMDLINE="$CMDLINE '$a'"
done

START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
"$@" </dev/null >"$LOG" 2>&1
RC=$?
LINES=$(wc -l <"$LOG" | tr -d ' ')

echo "command:$CMDLINE"
echo "started: $START   exit: $RC   output: $LINES line(s)   raw log: $LOG"
if [ -n "$GREP" ]; then
  HITS=$(grep -cE -- "$GREP" "$LOG" || true)
  echo "--- lines matching /$GREP/: $HITS (first 40) ---"
  grep -nE -- "$GREP" "$LOG" | head -n 40
fi
if [ "$LINES" -gt "$TAIL" ]; then
  echo "--- last $TAIL of $LINES lines ---"
else
  echo "--- output ---"
fi
tail -n "$TAIL" "$LOG"
exit "$RC"
