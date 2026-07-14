#!/bin/sh
# md2pdf.sh — convert a Markdown deliverable to PDF.
# Usage: md2pdf.sh <input.md> [output.pdf]
# Requires pandoc + a PDF engine (tries weasyprint, wkhtmltopdf, then LaTeX).
set -eu

IN="${1:?usage: md2pdf.sh <input.md> [output.pdf]}"
[ -f "$IN" ] || { echo "error: no such file: $IN" >&2; exit 1; }

if ! command -v pandoc >/dev/null 2>&1; then
  echo "error: pandoc not found — see https://pandoc.org/installing.html" >&2
  exit 127
fi

ENGINE=""
for e in weasyprint wkhtmltopdf tectonic xelatex pdflatex; do
  if command -v "$e" >/dev/null 2>&1; then ENGINE="$e"; break; fi
done
if [ -z "$ENGINE" ]; then
  cat >&2 <<'EOF'
error: no PDF engine found. Install one of:
  weasyprint:  pip install weasyprint          (lightest)
  tectonic:    https://tectonic-typesetting.github.io
  LaTeX:       sudo apt-get install texlive-xetex
Alternatively convert to docx (md2docx.sh) and export PDF from Word.
EOF
  exit 127
fi

dir=$(dirname "$IN"); base=$(basename "$IN" .md)
if [ -d "$dir/deliverables" ]; then def="$dir/deliverables/$base.pdf"; else def="$dir/$base.pdf"; fi
OUT="${2:-$def}"
mkdir -p "$(dirname "$OUT")"

pandoc "$IN" -f gfm --toc --pdf-engine="$ENGINE" -o "$OUT"
[ -s "$OUT" ] || { echo "error: conversion produced an empty file: $OUT" >&2; exit 1; }
echo "wrote $OUT (engine: $ENGINE)"
