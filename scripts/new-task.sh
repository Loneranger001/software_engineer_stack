#!/bin/sh
# new-task.sh — scaffold a task workspace with a minimal STATUS.md (run as `ses new-task`).
# Usage: new-task.sh <task-id> [workspace-root] [pipeline] [work-repo] [repo-set]
#   task-id         e.g. PROJ-123 (no spaces)
#   workspace-root  directory that holds work/, or `auto` (the default):
#                   resolved by workspace-root.sh from work-repo — the folder
#                   holding the repos in a multi-repo workspace, else the repo
#   pipeline        full | change-request | document | understand | func-design
#                   (default: full)
#   work-repo       repo whose code the task changes (default: the git repo
#                   containing the current directory; with an explicit
#                   workspace-root, that directory). See core/repo-resolution.md —
#                   both paths are recorded absolutised so later stages don't guess.
#   repo-set        comma-separated repos in ANALYSIS scope, i.e. searched for
#                   callers and dependents (default: work-repo only). Get the
#                   list from list-repos.sh <repos-folder>.
set -eu

case "${1:-}" in
  -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
esac
TASK_ID="${1:?usage: new-task.sh <task-id> [workspace-root] [pipeline] [work-repo] [repo-set]}"
ROOT="${2:-auto}"
PIPELINE="${3:-full}"
REPO="${4:-}"
REPO_SET="${5:-}"
HERE=$(cd "$(dirname "$0")" && pwd)

case "$TASK_ID" in
  -*|*[!A-Za-z0-9._-]*) echo "error: task-id may only contain letters, digits, . _ - and not start with -" >&2; exit 1 ;;
esac

if [ -z "$REPO" ]; then
  if [ "$ROOT" = auto ]; then
    REPO=$(git rev-parse --show-toplevel 2>/dev/null) \
      || { echo "error: not inside a git repo — pass work-repo explicitly" >&2; exit 1; }
  else
    REPO=$ROOT
  fi
fi
[ -d "$REPO" ] || { echo "error: not a directory: $REPO" >&2; exit 1; }
if [ "$ROOT" = auto ]; then
  ROOT=$("$HERE/workspace-root.sh" "$REPO") || exit 1
fi

for d in "$ROOT" "$REPO"; do
  [ -d "$d" ] || { echo "error: not a directory: $d" >&2; exit 1; }
done
ABS_ROOT=$(cd "$ROOT" && pwd)
ABS_REPO=$(cd "$REPO" && pwd)
[ -e "$ABS_REPO/.git" ] || echo "warning: $ABS_REPO has no .git — is that the work repo?" >&2

# analysis scope: every repo searched for callers/dependents, absolutised so
# the recorded scope is unambiguous when the analysis is audited later
ANALYZED="$ABS_REPO"
if [ -n "$REPO_SET" ]; then
  ANALYZED=""
  OIFS=$IFS; IFS=,
  for r in $REPO_SET; do
    IFS=$OIFS
    [ -n "$r" ] || continue
    [ -d "$r" ] || { echo "error: repo-set entry is not a directory: $r" >&2; exit 1; }
    ANALYZED="$ANALYZED$(cd "$r" && pwd)
"
    IFS=,
  done
  IFS=$OIFS
  ANALYZED=$(printf '%s' "$ANALYZED" | LC_ALL=C sort -u)
fi
REPOS_FIELD=$(printf '%s\n' "$ANALYZED" | sed '/^$/d' | paste -sd, - | sed 's/,/, /g')

DIR="$ABS_ROOT/work/$TASK_ID"

# Task workspaces never go into git. When work/ lands inside a repository (a
# standalone repo, or a parent folder that is itself a repo), exclude it there
# through .git/info/exclude: local to this clone, never committed or pushed,
# and the team's .gitignore is left alone.
keep_out_of_git() {
  TOP=$(git -C "$ABS_ROOT" rev-parse --show-toplevel 2>/dev/null) || return 0
  TOP=$(cd "$TOP" && pwd)
  REL_WORK="${ABS_ROOT#"$TOP"}/work"
  if [ -n "$(git -C "$TOP" ls-files -- "${REL_WORK#/}")" ]; then
    echo "WARNING: ${REL_WORK#/}/ is tracked in $TOP — remove it from git (git -C $TOP rm -r --cached ${REL_WORK#/}); ses checkpoint refuses to commit workspace files" >&2
  fi
  git -C "$TOP" check-ignore -q "${REL_WORK#/}/$TASK_ID/STATUS.md" 2>/dev/null && return 0
  EXCLUDE=$(git -C "$TOP" rev-parse --git-path info/exclude)
  case "$EXCLUDE" in /*) ;; *) EXCLUDE="$TOP/$EXCLUDE" ;; esac
  mkdir -p "$(dirname "$EXCLUDE")"
  printf '%s/\n' "$REL_WORK" >> "$EXCLUDE"
  echo "kept out of git: added $REL_WORK/ to $EXCLUDE (local only, never committed)"
}

if [ -e "$DIR/STATUS.md" ]; then
  keep_out_of_git
  echo "workspace already exists: $DIR (resume from its STATUS.md)" >&2
  exit 0
fi

mkdir -p "$DIR/evidence" "$DIR/deliverables"
keep_out_of_git

case "$PIPELINE" in
  full)
    NEXT="Run /intake with the requirement brief."
    STAGES="intake: pending
research: pending
tech-design: pending
grill: pending
impl-plan: pending
implement: pending
deliver: pending
retro: pending" ;;
  change-request)
    NEXT="Run /change-request with the CR description (starts at analyze)."
    STAGES="analyze: pending
mini-contract: pending
change: pending
verify: pending
deliver: pending
retro: pending" ;;
  document)
    NEXT="Run /document with the doc type and target (starts at analyze)."
    STAGES="analyze: pending
draft: pending
fact-check: pending
deliver: pending" ;;
  understand)
    NEXT="Run /understand with the interface or integration to investigate."
    STAGES="classify: pending
trace: pending
map: pending
explain: pending" ;;
  func-design)
    NEXT="Run /func-design with the brief or the component to describe (starts at analyze)."
    STAGES="analyze: pending
draft: pending
fact-check: pending
approval: pending
deliver: pending" ;;
  *) echo "error: unknown pipeline '$PIPELINE' (full|change-request|document|understand|func-design)" >&2; exit 1 ;;
esac

cat > "$DIR/STATUS.md" <<EOF
# STATUS — $TASK_ID
<!-- gates are read and set with \`ses status\`, never edited by hand -->

- task-id: $TASK_ID
- pipeline: $PIPELINE
- created: $(date -u +%Y-%m-%d)
- work-repo: $ABS_REPO
- workspace-root: $ABS_ROOT
- repos-analyzed: $REPOS_FIELD

## Stage gates

$STAGES

## Next action

$NEXT
EOF

cat > "$DIR/PARKED.md" <<EOF
# PARKED — out-of-scope findings for $TASK_ID

Items discovered during work that are OUTSIDE the scope contract.
Logged here for later triage; never acted on within this task.

| Date | Found during | Finding | Suggested follow-up |
|---|---|---|---|
EOF

cat > "$DIR/ASSUMPTIONS.md" <<EOF
# ASSUMPTIONS — $TASK_ID

Proceed-and-log decisions per core/decision-protocol.md: recorded the moment
they are made, presented for ratification at every approval gate. Delivery
with an open entry is a scope-audit finding.

| # | Date | Stage | Assumption | Basis (why ~90%) | Impact if wrong | Reversal step | Status |
|---|---|---|---|---|---|---|---|
EOF

echo "created $DIR"
