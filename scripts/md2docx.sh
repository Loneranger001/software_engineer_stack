#!/bin/sh
# md2docx.sh — convert a Markdown deliverable to Word.
# Usage: md2docx.sh <input.md> [output.docx]
#   Default output: <task-workspace>/deliverables/<name>.docx if the input
#   lives in a task workspace, else alongside the input.
# Optional: set SES_DOCX_REFERENCE to a reference.docx for corporate styling
#   (pandoc --reference-doc).
set -eu

IN="${1:?usage: md2docx.sh <input.md> [output.docx]}"
[ -f "$IN" ] || { echo "error: no such file: $IN" >&2; exit 1; }

if ! command -v pandoc >/dev/null 2>&1; then
  cat >&2 <<'EOF'
error: pandoc not found. Install it:
  macOS:         brew install pandoc
  Debian/Ubuntu: sudo apt-get install pandoc
  RHEL/Oracle:   sudo dnf install pandoc
  other:         https://pandoc.org/installing.html
EOF
  exit 127
fi

dir=$(dirname "$IN"); base=$(basename "$IN" .md)
if [ -d "$dir/deliverables" ]; then def="$dir/deliverables/$base.docx"; else def="$dir/$base.docx"; fi
OUT="${2:-$def}"
mkdir -p "$(dirname "$OUT")"

set --
[ -n "${SES_DOCX_REFERENCE:-}" ] && set -- --reference-doc="$SES_DOCX_REFERENCE"

pandoc "$IN" -f gfm -t docx --toc "$@" -o "$OUT"
[ -s "$OUT" ] || { echo "error: conversion produced an empty file: $OUT" >&2; exit 1; }
echo "wrote $OUT"
