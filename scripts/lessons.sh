#!/bin/sh
# lessons.sh — print only the lessons a stage should apply, instead of every
# skill reading all of the lessons into context (run as `ses lessons`).
#
# Usage: lessons.sh <stage> [--ws <ws>] [--lang plsql,sql,...] [--repo a,b,...]
#        lessons.sh --add '<lesson line>'     validate and append to your lessons file
#        lessons.sh --path                    print your lessons file's path
#
#   Prints lessons tagged [stage:<stage>] or [stage:any], plus — when given —
#   lessons for any stage whose [lang:...] is in --lang or whose [repo:...] is
#   in --repo (a stage:verify PL/SQL lesson matters to /implement on PL/SQL code).
#   With --repo, a lesson tagged with ANOTHER repo is left out, whatever else
#   it matches: "compile as ALASKAR in MFCS DEV" is no lesson for this repo.
#   --ws <ws> derives both from the task's STATUS.md: the repos are work-repo
#   and every repos-analyzed entry (by folder name); the languages are those
#   their tracked files use (.pks .pkb .pls .plb .trg → plsql, .sql → sql,
#   .ksh .sh → ksh, .py → python). Explicit --lang / --repo add to them.
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

STAGE="${1:?usage: lessons.sh <stage> [--ws ws] [--lang a,b] [--repo a,b] | --add LINE | --path}"
shift
LANGS=""
REPO=""
WS=""
while [ $# -gt 0 ]; do
  case "$1" in
    --lang) LANGS="${2:?--lang needs a value}"; shift 2 ;;
    --lang=*) LANGS="${1#--lang=}"; shift ;;
    --repo) REPO="${2:?--repo needs a value}"; shift 2 ;;
    --repo=*) REPO="${1#--repo=}"; shift ;;
    --ws) WS="${2:?--ws needs a workspace}"; shift 2 ;;
    --ws=*) WS="${1#--ws=}"; shift ;;
    -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
    *) echo "error: unknown argument $1" >&2; exit 2 ;;
  esac
done

# --ws: repos (folder names) and languages from the task's STATUS.md
if [ -n "$WS" ]; then
  ST="$WS"; [ -d "$WS" ] && ST="$WS/STATUS.md"
  [ -f "$ST" ] || { echo "error: no STATUS.md at $WS" >&2; exit 2; }
  PATHS=$( { sed -n 's/^- work-repo: *//p' "$ST"; sed -n 's/^- repos-analyzed: *//p' "$ST" | tr ',' '\n'; } \
           | sed 's/^ *//; s/ *$//' | sed '/^$/d' | sort -u)
  for p in $PATHS; do
    REPO="$REPO,$(basename "$p")"
    EXTS=$(git -C "$p" ls-files 2>/dev/null | sed -n 's/.*\.\([A-Za-z0-9]*\)$/\1/p' | tr 'A-Z' 'a-z' | sort -u)
    for e in $EXTS; do
      case "$e" in
        pks|pkb|pls|plb|trg|fnc|prc) LANGS="$LANGS,plsql" ;;
        sql) LANGS="$LANGS,sql" ;;
        ksh|sh) LANGS="$LANGS,ksh" ;;
        py) LANGS="$LANGS,python" ;;
      esac
    done
  done
  REPO=$(printf '%s\n' "$REPO" | tr ',' '\n' | sed '/^$/d' | sort -u | paste -sd, -)
  LANGS=$(printf '%s\n' "$LANGS" | tr ',' '\n' | sed '/^$/d' | sort -u | paste -sd, -)
fi

case "$STAGE" in
  *[!a-z-]*) echo "error: stage must be a stage tag like implement or tech-design" >&2; exit 2 ;;
esac

[ -f "$FILE" ] || { echo "error: no lessons file at $FILE" >&2; exit 1; }

# tag values are [a-z-] (stage, lang) or repo names; escape regex metachars
# in user-supplied values so a repo like "a.b" matches literally
esc() { printf '%s' "$1" | sed 's/[][\.*^$|+?(){}\\/]/\\&/g'; }

# alternation of a comma list, each value escaped; printf '%s\n' so `read`
# also sees the last value (an unterminated last line is dropped by read)
alt() { printf '%s\n' "$1" | tr ',' '\n' | while IFS= read -r v; do [ -n "$v" ] && esc "$v" && printf '|'; done; }

PAT="\\[stage:($STAGE|any)\\]"
if [ -n "$LANGS" ]; then
  ALT=$(alt "$LANGS")
  PAT="$PAT|\\[lang:(${ALT%|})\\]"
fi
REPO_ALT=""
if [ -n "$REPO" ]; then
  REPO_ALT=$(alt "$REPO")
  REPO_ALT=${REPO_ALT%|}
  PAT="$PAT|\\[repo:($REPO_ALT)\\]"
fi

# only lesson lines (below the marker), never the format examples in a header
below() { sed -n '/<!-- lessons below this line -->/,$p' "$1" | grep -E '^- \[' || true; }
ALL=$(below "$FILE")
[ -f "$USER_FILE" ] && ALL=$(printf '%s\n%s' "$ALL" "$(below "$USER_FILE")")
OUT=$(printf '%s\n' "$ALL" | grep -E "$PAT" || true)
# with --repo: a lesson tagged for another repo does not apply here
if [ -n "$REPO_ALT" ] && [ -n "$OUT" ]; then
  OUT=$(printf '%s\n' "$OUT" | grep -E "\\[repo:(-|$REPO_ALT)\\]" || true)
fi
if [ -n "$OUT" ]; then
  printf '%s\n' "$OUT"
  N=$(printf '%s\n' "$OUT" | wc -l | tr -d ' ')
else
  N=0
fi
echo "($N lesson(s) for stage:$STAGE${LANGS:+ lang:$LANGS}${REPO:+ repo:$REPO})"
