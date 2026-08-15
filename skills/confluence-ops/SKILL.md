---
name: confluence-ops
kind: tool
description: "Read, search, create, update, and move Confluence pages — wiki pages, TDD and design pages, Confluence URLs and short links, page ids, spaces, CQL searches. Use when a request references a Confluence page or wiki content. Converts pages to Markdown for reading and renders mermaid diagrams to SVG attachments on publish."
argument-hint: "<operation> [page-id|url|CQL]"
---

# Confluence Operations Skill

> Path note: `${CLAUDE_PLUGIN_ROOT}` is this framework's root — the ancestor
> directory of this file containing `plugin.json`/`skills/`. Claude Code resolves
> it automatically; other harnesses resolve it from this file's location.

A **tool** skill, not a lifecycle stage: it has no workspace, no gate, and no
`STATUS.md` of its own. Lifecycle stages call it (see `/deliver`).

## Prerequisites

Connection details are **never stored in this framework** — they come from the
environment of the machine running the agent. The helpers exit with this list
if any required variable is unset.

| Variable | Required | Purpose |
|---|---|---|
| `JIRA_URL` | yes* | Atlassian site, e.g. `https://your-org.atlassian.net` (Confluence is assumed at `<site>/wiki`) |
| `CONFLUENCE_URL` | yes* | Only when Confluence is not at `<JIRA_URL>/wiki`; overrides the above |
| `JIRA_EMAIL` | yes | Your Atlassian account email |
| `JIRA_TOKEN` | yes | API token — the same token works for Confluence |
| `CONFLUENCE_SPACES` | no | Comma-separated default space keys for `notifications` |

\* one of `JIRA_URL` or `CONFLUENCE_URL`.

Also required: Python 3.10+ with the `requests` package
(`pip install requests`). Mermaid rendering additionally needs `mmdc`
(`npm install -g @mermaid-js/mermaid-cli`) and degrades to a code block
without it.

## When to use
Use this skill for Confluence operations — searching, reading, creating, or updating documentation pages. Also for pulling page content for reference or drafting.

**Trigger phrases**: "confluence", "wiki", "docs", "documentation", "page", "create page", "update page"

## Scripts

### pull_confluence_page.py — Read pages (converts to markdown)

```bash
# Pull page by ID (prints to stdout as markdown)
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/pull_confluence_page.py 5575940659

# Pull page by URL
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/pull_confluence_page.py "https://your-org.atlassian.net/wiki/spaces/SPACE/pages/123456789/Some+Page"

# Pull page by short URL
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/pull_confluence_page.py "https://your-org.atlassian.net/wiki/x/EodugAE"

# Save to file
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/pull_confluence_page.py 5575940659 docs/pulled/my-page.md
```

### write.py — Create, update, move, and search pages

```bash
# ─── Create page ───────────────────────────────────────────
# Inline HTML body
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/write.py create --space SPACE --title "My Page" --body "<h1>Hello</h1>"

# Body from HTML file (preferred for large content)
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/write.py create --space SPACE --title "My Page" --body-file body.html

# With parent page
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/write.py create --space SPACE --title "Child Page" --body-file body.html --parent 5575940659

# Personal space (replace with your own space key)
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/write.py create --space "~YOUR_ACCOUNT_ID" --title "My Draft" --body-file body.html

# ─── Update page ───────────────────────────────────────────
# Update body only (keeps current title, auto-increments version)
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/write.py update 5575940659 --body-file updated_body.html

# Update title and body
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/write.py update 5575940659 --title "New Title" --body-file body.html

# ─── Move page ─────────────────────────────────────────────
# NOT a real move: Confluence's REST API cannot move a page across spaces, so
# this COPIES the page into the target and then deletes the original. The copy
# gets a NEW page id and does NOT carry over version history, comments,
# attachments, labels, child pages, or inbound links. Child pages are orphaned.
# The copy is created and verified before the original is deleted, so any
# failure leaves the source page intact. --yes is required.
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/write.py move PAGE_ID --space "~YOUR_ACCOUNT_ID" --yes

# Into a space under a specific parent
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/write.py move 6105498164 --space SPACE --parent 5575940659 --yes

# ─── Search pages ──────────────────────────────────────────
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/write.py search "type=page AND space=SPACE AND title~'Design'"
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/write.py search "type=page AND label='sdp-platform'" --limit 50
```

**Important**: Body content MUST be Confluence storage format (HTML), not Markdown.
For large pages, always use `--body-file` with an HTML file — never inline complex HTML on the command line.

### Mermaid diagram rendering

The skill provides helper functions for rendering mermaid diagrams to SVG and uploading them as Confluence page attachments. Three input patterns are supported:

- `<pre class="mermaid">...</pre>` — from HTML documents
- `<pre><code class="language-mermaid">` — from markdown-to-HTML converters
- Raw ` ```mermaid ` fenced blocks — from markdown content

**How it works**: Mermaid code is rendered to SVG via `mmdc` CLI, uploaded as a page attachment, and referenced with `<ac:image>`. Falls back to a Confluence code block if `mmdc` is not installed.

**Prerequisite**: `npm install -g @mermaid-js/mermaid-cli` (optional — graceful fallback without it)

**Python API** (for agent use):

```python
import sys
sys.path.insert(0, "${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence")
from write import get_session, render_mermaid_to_svg, extract_and_render_mermaid, upload_attachment

s = get_session()

# Render a single mermaid block and upload as attachment
svg_macro = render_mermaid_to_svg("graph LR\n  A --> B", page_id="12345", session=s)

# Find and render ALL mermaid blocks in an HTML body
body_html = extract_and_render_mermaid(body_html, page_id="12345", session=s)

# Upload any file as a page attachment
upload_attachment(s, "12345", "report.pdf", pdf_bytes, "application/pdf")
```


## Customization

This skill is generic. Add your team-specific Confluence context to `.github/copilot-instructions.md`:

```markdown
## My Confluence Context
- Key spaces: MYTEAM (team docs), ARCH (architecture)
- Personal space: ~YOUR_ACCOUNT_ID
- Default space for new pages: MYTEAM
```

The agent reads your instructions at startup and applies them to all Confluence operations.

## Safety rules
- **READ operations**: Always safe.
- **CREATE/UPDATE**: Execute when the user instructs. Always confirm before writing.
- **MOVE is destructive** — a copy-then-delete that loses history, comments,
  attachments and children, and orphans child pages. Show the user what will be
  lost and get explicit confirmation before passing `--yes`.
- Confluence uses HTML storage format, not Markdown. The pull script converts to Markdown for reading.

## Key spaces

Configure these for your team. Find your personal space key via `/wiki/rest/api/user/current` (use accountId with `~` prefix), and set `CONFLUENCE_SPACES` for the spaces `notifications` should watch.

- **~YOUR_ACCOUNT_ID** — Your personal space
- Add your team's spaces here (e.g., your project space key from Confluence)

## Notifications

Approximates the Confluence notification inbox using CQL queries. Shows recent page modifications by others in key spaces and on pages you've contributed to.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/write.py notifications                  # Last 24 hours
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/write.py notifications --days 7         # Last week
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/write.py notifications --spaces SPACE   # Specific space only
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/write.py notifications --days 3 --spaces SPACE1,SPACE2  # Custom
```

Categories:
- 📄 **Space activity** — pages modified by others in monitored spaces
- ✏️ **My contributions** — pages you've edited that someone else subsequently modified

Self-edits are automatically filtered out.
