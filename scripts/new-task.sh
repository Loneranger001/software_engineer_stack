#!/bin/sh
# new-task.sh — scaffold a task workspace with a STATUS.md resume point.
# Usage: new-task.sh <task-id> [workspace-root] [pipeline]
#   task-id         e.g. PROJ-123 (no spaces)
#   workspace-root  directory that holds work/ (default: current directory)
#   pipeline        full | change-request | document  (default: full)
set -eu

TASK_ID="${1:?usage: new-task.sh <task-id> [workspace-root] [pipeline]}"
ROOT="${2:-.}"
PIPELINE="${3:-full}"

case "$TASK_ID" in
  *[!A-Za-z0-9._-]*) echo "error: task-id may only contain letters, digits, . _ -" >&2; exit 1 ;;
esac

DIR="$ROOT/work/$TASK_ID"
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
  *) echo "error: unknown pipeline '$PIPELINE' (full|change-request|document)" >&2; exit 1 ;;
esac

cat > "$DIR/STATUS.md" <<EOF
# STATUS — $TASK_ID

- task-id: $TASK_ID
- pipeline: $PIPELINE
- created: $(date -u +%Y-%m-%dT%H:%M:%SZ)
- work-repo: $(pwd)
- branch: (set by /implement)

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
