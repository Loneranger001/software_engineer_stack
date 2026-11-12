# mermaid-prep.sh — sourced by md2docx.sh, md2pdf.sh and md2confluence.sh (not a command).
# Expects IN (the Markdown file), OUT (the output file) and HERE (scripts/).
# Sets MERMAID_ARGS: the pandoc options that render ```mermaid blocks as images
# (mermaid-cli `mmdc` on PATH), or nothing — with a warning naming how many
# diagrams will reach the reader as source code instead.
MERMAID_ARGS=""
MERMAID_DIR=""
MERMAID_N=$(grep -c '^[[:space:]]*```[[:space:]]*mermaid' "$IN" 2>/dev/null || true)
if [ "${MERMAID_N:-0}" -gt 0 ]; then
  if command -v mmdc >/dev/null 2>&1; then
    MERMAID_DIR="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT" | sed 's/\.[^.]*$//')-diagrams"
    mkdir -p "$MERMAID_DIR"
    MERMAID_ARGS="--lua-filter=$HERE/mermaid.lua"
    export SES_MERMAID_DIR="$MERMAID_DIR"
  else
    echo "WARNING: $MERMAID_N mermaid diagram(s) in $(basename "$IN") will appear as source code — install" \
         "mermaid-cli (npm install -g @mermaid-js/mermaid-cli) for mmdc, then convert again" >&2
  fi
fi
