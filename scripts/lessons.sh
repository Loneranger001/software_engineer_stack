#!/bin/sh
# lessons.sh — print only the lessons a stage should apply, instead of every
# skill reading all of knowledge/lessons.md into context.
#
# Usage: lessons.sh <stage> [--lang plsql,sql,...] [--repo <name>]
#   Prints lessons tagged [stage:<stage>] or [stage:any], plus — when given —
#   lessons for any stage whose [lang:...] is in --lang or whose [repo:...] is
#   --repo (a stage:verify PL/SQL lesson matters to /implement on PL/SQL code).
#   Ends with a one-line count so "no lessons" is visible, not silent.
#
# Reads the lessons.md next to this script's framework root, so an install
# copy (copilot/, .github/se-stack/) reads its own per-install lessons.
set -eu

STAGE="${1:?usage: lessons.sh <stage> [--lang a,b] [--repo name]}"
shift
LANGS=""
REPO=""
while [ $# -gt 0 ]; do
  case "$1" in
    --lang) LANGS="${2:?--lang needs a value}"; shift 2 ;;
    --lang=*) LANGS="${1#--lang=}"; shift ;;
    --repo) REPO="${2:?--repo needs a value}"; shift 2 ;;
    --repo=*) REPO="${1#--repo=}"; shift ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "error: unknown argument $1" >&2; exit 2 ;;
  esac
done

case "$STAGE" in
  *[!a-z-]*) echo "error: stage must be a stage tag like implement or tech-design" >&2; exit 2 ;;
esac

FILE="$(cd "$(dirname "$0")/.." && pwd)/knowledge/lessons.md"
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

# only lesson lines (below the marker), never the format examples in the header
OUT=$(sed -n '/<!-- lessons below this line -->/,$p' "$FILE" | grep -E '^- \[' | grep -E "$PAT" || true)
if [ -n "$OUT" ]; then
  printf '%s\n' "$OUT"
  N=$(printf '%s\n' "$OUT" | wc -l | tr -d ' ')
else
  N=0
fi
echo "($N lesson(s) for stage:$STAGE${LANGS:+ lang:$LANGS}${REPO:+ repo:$REPO})"
