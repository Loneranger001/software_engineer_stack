-- mermaid.lua — pandoc filter: render ```mermaid blocks to PNG with mermaid-cli (mmdc),
-- so Word, PDF and Confluence show the diagram instead of its source code.
-- Used by md2docx.sh / md2pdf.sh / md2confluence.sh when `mmdc` is on PATH.
-- SES_MERMAID_DIR: where the PNGs go (default: the current directory).
-- A diagram mmdc cannot render stays a code block, so nothing is lost.

local count = 0

local function sh_quote(s)
  return "'" .. string.gsub(s, "'", "'\\''") .. "'"
end

function CodeBlock(el)
  if not el.classes:includes("mermaid") then
    return nil
  end
  count = count + 1
  local dir = os.getenv("SES_MERMAID_DIR") or "."
  local png = dir .. "/diagram-" .. count .. ".png"
  local src = os.tmpname()
  local f = io.open(src, "w")
  f:write(el.text)
  f:close()
  local ok = os.execute("mmdc -q -i " .. sh_quote(src) .. " -o " .. sh_quote(png)
                        .. " -b white >/dev/null 2>&1")
  os.remove(src)
  if not ok then
    io.stderr:write("warning: mermaid diagram " .. count .. " could not be rendered; kept as code\n")
    return nil
  end
  -- Confluence wiki markup names an attachment, not a path
  local ref = (FORMAT == "jira") and ("diagram-" .. count .. ".png") or png
  return pandoc.Para({ pandoc.Image({}, ref) })
end
