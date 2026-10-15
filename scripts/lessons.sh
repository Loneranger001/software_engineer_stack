#!/bin/sh
# lessons.sh — print only the lessons a stage should apply, instead of every
# skill reading all of the lessons into context (run as `ses lessons`).
#
# Usage: lessons.sh <stage> [--lang plsql,sql,...] [--repo <name>]
#        lessons.sh --add '<lesson line>'     validate and append to your lessons file
#        lessons.sh --path                    print your lessons file's path
#
#   Prints lessons tagged [stage:<stage>] or [stage:any], plus — when given —
#   lessons for any stage whose [lang:...] is in --lang or whose [repo:...] is
#   --repo (a stage:verify PL/SQL lesson matters to /implement on PL/SQL code).
#   Ends with a one-line count so "no lessons" is visible, not silent.
#
# Two sources: the framework's knowledge/lessons.md (ships with the framework,
# read-only in an installed copy) and your own ${SES_HOME:-~/.ses}/lessons.md,
# which /retro appends to. Your file lives outside every install, so it
# survives plugin updates and is shared by every harness on the machine.
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FILE="$ROOT/knowledge/lessons.md"
USER_FILE="${SES_HOME:-$HOME/.ses}/lessons.md"
STAGES='intake|research|func-design|tech-design|grill|impl-plan|implement|deliver|change-request|document|understand|verify|any'
FORMAT='- [YYYY-MM-DD] [stage:<stage>] [lang:<plsql|sql|ksh|python|->] [repo:<name|->] <lesson> (task <id>)'

case "${1:-}" in
  --path) echo "$USER_FILE"; exit 0 ;;
  --add)
    LINE="${2:?--add needs a lesson line}"
    if ! printf '%s\n' "$LINE" | grep -Eq "^- \[[0-9]{4}-[0-9]{2}-[0-9]{2}\] \[stage:($STAGES)\] \[lang:(plsql|sql|ksh|python|-)\] \[repo:[^]]+\] .+ \(task [^)]+\)$"; then
      echo "error: not a lesson line — format: $FORMAT (stage one of ${STAGES})" >&2
      exit 2
    fi
    mkdir -p "$(dirname "$USER_FILE")"
    if [ ! -f "$USER_FILE" ]; then
      cat > "$USER_FILE" <<EOF
# Lessons (yours)

> Appended by /retro (\`ses lessons --add\`), read by every stage through
> \`ses lessons\` together with the framework's own knowledge/lessons.md.
> Format: \`$FORMAT\`

<!-- lessons below this line -->
EOF
    fi
    if grep -Fxq -- "$LINE" "$USER_FILE"; then
      echo "already recorded in $USER_FILE"
    else
      printf '%s\n' "$LINE" >> "$USER_FILE"
      echo "added to $USER_FILE"
    fi
    exit 0 ;;
esac

STAGE="${1:?usage: lessons.sh <stage> [--lang a,b] [--repo name] | --add LINE | --path}"
shift
LANGS=""
REPO=""
while [ $# -gt 0 ]; do
  case "$1" in
    --lang) LANGS="${2:?--lang needs a value}"; shift 2 ;;
    --lang=*) LANGS="${1#--lang=}"; shift ;;
    --repo) REPO="${2:?--repo needs a value}"; shift 2 ;;
    --repo=*) REPO="${1#--repo=}"; shift ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) echo "error: unknown argument $1" >&2; exit 2 ;;
  esac
done

case "$STAGE" in
  *[!a-z-]*) echo "error: stage must be a stage tag like implement or tech-design" >&2; exit 2 ;;
esac

[ -f "$FILE" ] || { echo "error: no lessons file at $FILE" >&2; exit 1; }

# tag values are [a-z-] (stage, lang) or repo names; escape regex metachars
# in user-supplied values so a repo like "a.b" matches literally
esc() { printf '%s' "$1" | sed 's/[][\.*^$|+?(){}\\/]/\\&/g'; }

PAT="\\[stage:($STAGE|any)\\]"
if [ -n "$LANGS" ]; then
  ALT=$(printf '%s' "$LANGS" | tr ',' '\n' | while read -r l; do [ -n "$l" ] && esc "$l" && printf '|'; done)
  PAT="$PAT|\\[lang:(${ALT%|})\\]"
fi
[ -n "$REPO" ] && PAT="$PAT|\\[repo:$(esc "$REPO")\\]"

# only lesson lines (below the marker), never the format examples in a header
below() { sed -n '/<!-- lessons below this line -->/,$p' "$1" | grep -E '^- \[' || true; }
ALL=$(below "$FILE")
[ -f "$USER_FILE" ] && ALL=$(printf '%s\n%s' "$ALL" "$(below "$USER_FILE")")
OUT=$(printf '%s\n' "$ALL" | grep -E "$PAT" || true)
if [ -n "$OUT" ]; then
  printf '%s\n' "$OUT"
  N=$(printf '%s\n' "$OUT" | wc -l | tr -d ' ')
else
  N=0
fi
echo "($N lesson(s) for stage:$STAGE${LANGS:+ lang:$LANGS}${REPO:+ repo:$REPO})"
