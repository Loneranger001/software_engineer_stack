#!/bin/sh
# workspace-root.sh — print the directory that holds work/<task-id>/ task
# workspaces, so every stage and new-task.sh agree on it without guessing.
#
# Usage: workspace-root.sh [dir]     (dir: a repo, a path inside one, or the
#                                     folder holding the repos; default: cwd)
#
# Resolution, first match wins:
#   1. $SES_WORKSPACE_ROOT, if set (must be an existing directory).
#   2. dir is inside a git repo R, and R's parent is NOT inside a git repo and
#      holds 2+ repos → R's parent (the multi-repo workspace folder).
#   3. dir is inside a git repo R → R (a standalone repo keeps work/ inside).
#   4. dir is not in a git repo but holds 1+ repos → dir.
#   5. otherwise: error — ask the user where workspaces live.
# A workspace that already exists keeps the root recorded in its STATUS.md;
# this only decides where NEW workspaces go. See core/repo-resolution.md.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
DIR="${1:-.}"
case "$DIR" in -h|--help) sed -n '2,17p' "$0"; exit 0 ;; esac

if [ -n "${SES_WORKSPACE_ROOT:-}" ]; then
  [ -d "$SES_WORKSPACE_ROOT" ] || { echo "error: SES_WORKSPACE_ROOT is not a directory: $SES_WORKSPACE_ROOT" >&2; exit 1; }
  (cd "$SES_WORKSPACE_ROOT" && pwd)
  exit 0
fi

[ -d "$DIR" ] || { echo "error: not a directory: $DIR" >&2; exit 1; }
ABS=$(cd "$DIR" && pwd)

count_repos() { sh "$HERE/list-repos.sh" "$1" 2>/dev/null | grep -c . || true; }

if REPO=$(git -C "$ABS" rev-parse --show-toplevel 2>/dev/null); then
  PARENT=$(dirname "$REPO")
  if ! git -C "$PARENT" rev-parse --show-toplevel >/dev/null 2>&1 \
     && [ "$(count_repos "$PARENT")" -ge 2 ]; then
    printf '%s\n' "$PARENT"
  else
    printf '%s\n' "$REPO"
  fi
  exit 0
fi

if [ "$(count_repos "$ABS")" -ge 1 ]; then
  printf '%s\n' "$ABS"
  exit 0
fi

echo "error: $ABS is not in a git repo and holds none — ask the user where task workspaces live (or set SES_WORKSPACE_ROOT)" >&2
exit 1
