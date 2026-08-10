#!/bin/sh
# list-repos.sh — enumerate the git repos in a workspace folder, one absolute
# path per line, so cross-repo analysis has a recorded, reproducible search set.
#
# Usage: list-repos.sh [repos-folder] [--depth N]
#   repos-folder  folder holding the repos (default: current directory)
#   --depth N     how deep to look for .git (default: 2 — the folder itself and
#                 its immediate children, which covers the usual
#                 workspace-root/<repo>/ layout; raise it for grouped layouts
#                 like workspace-root/<team>/<repo>/)
#
# Prints nothing and exits 1 if no repo is found — a task's analysis scope is
# never silently empty. See core/repo-resolution.md.
set -eu

DIR="."
DEPTH=2
while [ $# -gt 0 ]; do
  case "$1" in
    --depth) DEPTH="${2:?--depth needs a number}"; shift 2 ;;
    --depth=*) DEPTH="${1#--depth=}"; shift ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    -*) echo "error: unknown option $1" >&2; exit 2 ;;
    *) DIR="$1"; shift ;;
  esac
done

case "$DEPTH" in
  ''|*[!0-9]*) echo "error: --depth must be a number" >&2; exit 2 ;;
esac
[ -d "$DIR" ] || { echo "error: not a directory: $DIR" >&2; exit 2; }

ABS=$(cd "$DIR" && pwd)

# .git is a directory in a normal clone and a file in a worktree/submodule.
# A repo nested inside another (submodule, vendored checkout) belongs to its
# parent's analysis, not to a separate one — drop it. Sorting guarantees a
# parent precedes its children, but NOT that they are adjacent
# (repo-a.x sorts between repo-a and repo-a/vendor), so each candidate is
# tested against every root kept so far.
FOUND=$(find "$ABS" -maxdepth "$DEPTH" -name .git \( -type d -o -type f \) 2>/dev/null \
        | sed 's#/\.git$##' | LC_ALL=C sort -u \
        | awk '{ for (i = 1; i <= n; i++) if (index($0, kept[i]) == 1) next
                 kept[++n] = $0 "/"; print }')

[ -n "$FOUND" ] || { echo "error: no git repositories found under $ABS (depth $DEPTH)" >&2; exit 1; }
printf '%s\n' "$FOUND"
