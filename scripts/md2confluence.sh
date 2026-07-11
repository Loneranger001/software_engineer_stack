#!/bin/sh
# md2confluence.sh — convert a Markdown deliverable to Confluence wiki markup
# suitable for pasting into a Confluence page (Insert > Markup > Confluence wiki).
# Usage: md2confluence.sh <input.md> [output.confluence.txt]
# Note: modern Confluence Cloud also accepts Markdown paste directly; this
# output targets the wiki-markup path which survives more formatting.
set -eu

IN="${1:?usage: md2confluence.sh <input.md> [output.confluence.txt]}"
[ -f "$IN" ] || { echo "error: no such file: $IN" >&2; exit 1; }

if ! command -v pandoc >/dev/null 2>&1; then
  echo "error: pandoc not found — see https://pandoc.org/installing.html" >&2
  exit 127
fi

dir=$(dirname "$IN"); base=$(basename "$IN" .md)
if [ -d "$dir/deliverables" ]; then def="$dir/deliverables/$base.confluence.txt"; else def="$dir/$base.confluence.txt"; fi
OUT="${2:-$def}"
mkdir -p "$(dirname "$OUT")"

# pandoc's jira writer produces Jira/Confluence wiki markup.
pandoc "$IN" -f gfm -t jira -o "$OUT"
[ -s "$OUT" ] || { echo "error: conversion produced an empty file: $OUT" >&2; exit 1; }
echo "wrote $OUT"
echo "paste via Confluence: Insert > Markup > 'Confluence wiki' (or +/markup)"
