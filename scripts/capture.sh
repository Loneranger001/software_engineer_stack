#!/bin/sh
# capture.sh — run a verification command, keep its FULL output on disk, and
# print only a bounded summary (exit code, line count, last N lines, matched
# error lines). The summary is what goes into the evidence file and the
# agent's context; the raw log is the audit trail, opened only when needed.
#
# Usage: capture.sh <evidence-dir> <name> [--tail N] [--grep REGEX] -- <command> [args...]
#   evidence-dir  the task's evidence/ directory (created if missing)
#   name          log name; output goes to <evidence-dir>/raw/<name>.log. Use a
#                 new name for every run: a checkpoint commit may already hold
#                 the hash of an existing log, and rewriting it makes
#                 `ses checkpoint verify` report ALTERED. Replacing a log is
#                 allowed (a failed attempt's log is not hashed yet) but noted.
#   --tail N      lines of output to show (default 40)
#   --grep REGEX  also show every line matching REGEX (extended regex), capped
#                 at 40 — e.g. 'ORA-|PLS-|SP2-|ERROR|FAILED|Traceback'
#
# Exits with the command's own exit code, so callers still see failure.
# stdin is /dev/null: a sqlplus script without EXIT ends instead of hanging.
#
# Secrets are redacted — in the recorded command line, the raw log and the
# printed summary — as <NAME> of the variable that holds them: the value of
# every environment variable whose name looks like a credential (*_CONN,
# *_CONN_*, *PASSWORD*, *PASSWD*, *_PW, *_PWD, *SECRET*, *TOKEN*, *API_KEY*,
# *APIKEY*), plus SES_DB_CONN and every name listed in SES_REDACT_VARS
# (space- or comma-separated) — e.g. a repo's own INV_DB_CONN. Values shorter
# than 4 characters are left alone. This is a safety net, not a licence:
# prefer wallet/OS auth and keep connect strings off command lines.
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
REPLACED=""
[ -e "$LOG" ] && REPLACED=1

# names whose values are secrets: credential-looking names, SES_DB_CONN, and SES_REDACT_VARS;
# longest value first, so a password inside a connect string never leaves a partial match
SECRET_NAMES=$( {
  env | sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1/p' | while IFS= read -r n; do
    case "$n" in
      *_CONN|*_CONN_*|*PASSWORD*|*PASSWD*|*_PW|*_PWD|*SECRET*|*TOKEN*|*API_KEY*|*APIKEY*|SES_DB_CONN) echo "$n" ;;
    esac
  done
  printf '%s\n' "${SES_REDACT_VARS:-}" | tr ', ' '\n\n'
} | sed '/^$/d' | LC_ALL=C sort -u | while IFS= read -r n; do
  v=$(printenv "$n" 2>/dev/null || true)
  [ "${#v}" -ge 4 ] && printf '%s %s\n' "${#v}" "$n"
done | sort -rn | cut -d' ' -f2 | paste -sd' ' -)

# replace each secret value with <NAME>, literally (no regex: values hold / @ . and worse)
redact() {
  if [ -z "$SECRET_NAMES" ]; then cat; return; fi
  awk -v names="$SECRET_NAMES" 'BEGIN { n = split(names, N, " ") }
    { line = $0
      for (i = 1; i <= n; i++) {
        v = ENVIRON[N[i]]; out = ""
        while ((p = index(line, v)) > 0) { out = out substr(line, 1, p - 1) "<" N[i] ">"; line = substr(line, p + length(v)) }
        line = out line
      }
      print line }'
}

# recorded command line, secrets redacted
CMDLINE=""
for a in "$@"; do
  CMDLINE="$CMDLINE '$a'"
done
CMDLINE=$(printf '%s\n' "$CMDLINE" | redact)

START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
"$@" </dev/null >"$LOG.part" 2>&1
RC=$?
redact <"$LOG.part" >"$LOG"   # the raw log keeps no secret either
rm -f "$LOG.part"
LINES=$(wc -l <"$LOG" | tr -d ' ')

echo "command:$CMDLINE"
echo "started: $START   exit: $RC   output: $LINES line(s)   raw log: $LOG"
[ -n "$REPLACED" ] && echo "note: replaced an existing $NAME.log — if a commit recorded its hash, rerun under a new name"
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
