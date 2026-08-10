#!/bin/sh
# new-task.sh — scaffold a task workspace with a STATUS.md resume point.
# Usage: new-task.sh <task-id> [workspace-root] [pipeline] [work-repo]
#   task-id         e.g. PROJ-123 (no spaces)
#   workspace-root  directory that holds work/ (default: current directory)
#   pipeline        full | change-request | document | understand  (default: full)
#   work-repo       repo whose code the task changes, holding .conventions.md
#                   (default: workspace-root). See core/repo-resolution.md —
#                   with a parent folder as the session cwd these differ, and
#                   both are recorded absolutised so later stages don't guess.
#   repo-set        comma-separated repos in ANALYSIS scope, i.e. searched for
#                   callers and dependents (default: work-repo only). Get the
#                   list from list-repos.sh <repos-folder>.
set -eu

TASK_ID="${1:?usage: new-task.sh <task-id> [workspace-root] [pipeline] [work-repo] [repo-set]}"
ROOT="${2:-.}"
PIPELINE="${3:-full}"
REPO="${4:-$ROOT}"
REPO_SET="${5:-}"

case "$TASK_ID" in
  *[!A-Za-z0-9._-]*) echo "error: task-id may only contain letters, digits, . _ -" >&2; exit 1 ;;
esac

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
REPO_LINES=$(printf '%s\n' "$ANALYZED" | sed 's/^/  - /')

DIR="$ABS_ROOT/work/$TASK_ID"
if [ -e "$DIR/STATUS.md" ]; then
  echo "workspace already exists: $DIR (resume from its STATUS.md)" >&2
  exit 0
fi

mkdir -p "$DIR/evidence" "$DIR/deliverables"

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
  *) echo "error: unknown pipeline '$PIPELINE' (full|change-request|document|understand)" >&2; exit 1 ;;
esac

cat > "$DIR/STATUS.md" <<EOF
# STATUS — $TASK_ID

- task-id: $TASK_ID
- pipeline: $PIPELINE
- created: $(date -u +%Y-%m-%dT%H:%M:%SZ)
- work-repo: $ABS_REPO
- workspace-root: $ABS_ROOT
- branch: (set by /implement — one line per changed repo)

## Repos analyzed

Analysis scope: every repo searched for callers and dependents. Impact
analysis covers ALL of them; only repos the scope contract names may be
changed (core/repo-resolution.md).

$REPO_LINES

## Stage gates

Legend: pending | in-progress | done | approved (user sign-off)

$STAGES

## Next action

$NEXT

## Log

- $(date -u +%Y-%m-%dT%H:%M:%SZ) workspace created
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
