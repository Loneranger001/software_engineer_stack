#!/usr/bin/env python3
"""
Confluence Write Operations
===========================

Create, update, move, search, and manage Confluence pages and comments.

USAGE:
    python3 utils/confluence/write.py create --space KEY --title "Title" --body-file path/to/body.html
    python3 utils/confluence/write.py create --space KEY --title "Title" --body "<h1>Hello</h1>"
    python3 utils/confluence/write.py create --space KEY --title "Title" --body-file body.html --parent PAGE_ID

    python3 utils/confluence/write.py update PAGE_ID --body-file path/to/body.html
    python3 utils/confluence/write.py update PAGE_ID --body "<p>Updated</p>"
    python3 utils/confluence/write.py update PAGE_ID --title "New Title" --body-file body.html

    python3 utils/confluence/write.py move PAGE_ID --space TARGET_SPACE_KEY [--parent PARENT_ID]

    python3 utils/confluence/write.py search "CQL query" [--limit 25]

    python3 utils/confluence/write.py comments PAGE_ID [--limit 50]

    python3 utils/confluence/write.py notifications [--days 1] [--spaces EECI,SRESUP]

ENVIRONMENT:
    JIRA_EMAIL - Atlassian email
    JIRA_TOKEN - Atlassian API token (works for Confluence too)

NOTES:
    - Body content must be Confluence storage format (HTML), not Markdown
    - Mermaid diagrams are auto-detected and rendered to SVG via mmdc CLI:
      * <pre class="mermaid"> blocks (from HTML)
      * <pre><code class="language-mermaid"> blocks (from markdown-to-HTML)
      * ```mermaid fenced blocks (from raw markdown)
      SVGs are uploaded as page attachments and referenced via ac:image.
      Falls back to a code block if mmdc is not installed.
    - For update, the script auto-increments the version number
    - For create, --space is required (e.g. EECI, SRESUP, ~631a246e9794410874c7acee)
    - For move, page is deleted from source and recreated in target (new page ID)
    - Default space for new pages: ~631a246e9794410874c7acee (Sohail's personal space)
    - Inline comment resolution is UI-only (Confluence API limitation)
"""

import os
import sys
import json
import re
import hashlib
import argparse
import requests
from requests.auth import HTTPBasicAuth

CONFLUENCE_URL = "https://lululemon.atlassian.net/wiki"


def upload_attachment(session, page_id, filename, data, content_type="image/svg+xml"):
    """Upload a file as a Confluence page attachment.

    If an attachment with the same filename already exists, it is updated in place.
    Temporarily removes the session Content-Type header so requests can set
    multipart/form-data (session default of application/json causes HTTP 415).
    """
    saved_ct = session.headers.pop("Content-Type", None)
    try:
        r = session.post(
            f"{CONFLUENCE_URL}/rest/api/content/{page_id}/child/attachment",
            headers={"X-Atlassian-Token": "nocheck", "Accept": "application/json"},
            files={"file": (filename, data, content_type)},
        )
        # Attachment already exists — update it
        if r.status_code == 400:
            att_r = session.get(
                f"{CONFLUENCE_URL}/rest/api/content/{page_id}/child/attachment",
                params={"filename": filename},
            )
            if att_r.status_code == 200:
                results = att_r.json().get("results", [])
                if results:
                    att_id = results[0]["id"]
                    r = session.post(
                        f"{CONFLUENCE_URL}/rest/api/content/{page_id}/child/attachment/{att_id}/data",
                        headers={"X-Atlassian-Token": "nocheck", "Accept": "application/json"},
                        files={"file": (filename, data, content_type)},
                    )
    finally:
        if saved_ct:
            session.headers["Content-Type"] = saved_ct
    return r


def render_mermaid_to_svg(mermaid_code, page_id=None, session=None):
    """Render mermaid code to SVG.

    If page_id and session are provided, uploads the SVG as a Confluence
    page attachment and returns an ac:image macro referencing it.
    Otherwise returns the raw SVG string.

    Falls back to a Confluence code block if mmdc is not available or
    rendering fails.

    Requires: mmdc (npm install -g @mermaid-js/mermaid-cli)
    """
    import subprocess
    import tempfile
    import shutil

    mmdc_path = shutil.which("mmdc")
    if not mmdc_path:
        return (
            '<ac:structured-macro ac:name="code">'
            '<ac:parameter ac:name="language">text</ac:parameter>'
            '<ac:parameter ac:name="title">Mermaid Diagram (install mmdc to render)</ac:parameter>'
            '<ac:plain-text-body><![CDATA['
            f'{mermaid_code}'
            ']]></ac:plain-text-body>'
            '</ac:structured-macro>'
        )

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.mmd")
            output_path = os.path.join(tmpdir, "diagram.svg")

            with open(input_path, "w") as f:
                f.write(mermaid_code)

            result = subprocess.run(
                [mmdc_path, "-i", input_path, "-o", output_path, "-b", "transparent"],
                capture_output=True, text=True, timeout=30,
            )

            if result.returncode != 0 or not os.path.exists(output_path):
                return (
                    '<ac:structured-macro ac:name="code">'
                    '<ac:parameter ac:name="language">text</ac:parameter>'
                    '<ac:parameter ac:name="title">Mermaid Diagram (render failed)</ac:parameter>'
                    '<ac:plain-text-body><![CDATA['
                    f'{mermaid_code}'
                    ']]></ac:plain-text-body>'
                    '</ac:structured-macro>'
                )

            with open(output_path, "rb") as f:
                svg_data = f.read()

            # Upload as attachment if we have a page context
            if page_id and session:
                filename = f"mermaid_diagram_{hashlib.md5(mermaid_code.encode()).hexdigest()[:8]}.svg"
                r = upload_attachment(session, page_id, filename, svg_data)
                if r.status_code in (200, 201):
                    return (
                        f'<ac:image ac:width="800">'
                        f'<ri:attachment ri:filename="{filename}"/>'
                        f'</ac:image>'
                    )

            # Fallback: return raw SVG
            return svg_data.decode("utf-8")

    except (subprocess.TimeoutExpired, Exception):
        return (
            '<ac:structured-macro ac:name="code">'
            '<ac:parameter ac:name="language">text</ac:parameter>'
            '<ac:plain-text-body><![CDATA['
            f'{mermaid_code}'
            ']]></ac:plain-text-body>'
            '</ac:structured-macro>'
        )


def extract_and_render_mermaid(html, page_id=None, session=None):
    """Find mermaid blocks in HTML and render them to SVG.

    Detects mermaid from three sources:
    1. <pre class="mermaid">...</pre>           (HTML documents)
    2. <pre><code class="language-mermaid">      (markdown-to-HTML converters)
    3. ```mermaid ... ```                        (raw markdown fenced blocks)

    Each block is replaced with an ac:image attachment reference (if page_id
    provided) or inline SVG.
    """
    patterns = [
        # Raw markdown fenced blocks
        (r'```mermaid\s*\n(.*?)```', False),
        # Markdown-to-HTML: <pre><code class="language-mermaid">
        (r'<pre>\s*<code[^>]*class="[^"]*language-mermaid[^"]*"[^>]*>(.*?)</code>\s*</pre>', True),
        # HTML: <pre class="mermaid">
        (r'<pre[^>]*class="[^"]*mermaid[^"]*"[^>]*>(.*?)</pre>', True),
    ]

    for pattern, needs_unescape in patterns:
        for match in reversed(list(re.finditer(pattern, html, re.DOTALL | re.IGNORECASE))):
            code = match.group(1).strip()
            if needs_unescape:
                code = code.replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")
            replacement = render_mermaid_to_svg(code, page_id=page_id, session=session)
            html = html[:match.start()] + replacement + html[match.end():]

    return html


def get_session():
    """Create authenticated Confluence session."""
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_TOKEN")
    if not email or not token:
        print("ERROR: Missing JIRA_EMAIL or JIRA_TOKEN", file=sys.stderr)
        sys.exit(1)
    s = requests.Session()
    s.auth = HTTPBasicAuth(email, token)
    s.headers.update({"Accept": "application/json", "Content-Type": "application/json"})
    return s


def cmd_create(args):
    """Create a new Confluence page."""
    s = get_session()

    body_html = args.body
    if args.body_file:
        with open(args.body_file, "r") as f:
            body_html = f.read()

    if not body_html:
        print("ERROR: Provide --body or --body-file", file=sys.stderr)
        sys.exit(1)

    payload = {
        "type": "page",
        "title": args.title,
        "space": {"key": args.space},
        "body": {
            "storage": {
                "value": body_html,
                "representation": "storage"
            }
        }
    }

    if args.parent:
        payload["ancestors"] = [{"id": str(args.parent)}]

    r = s.post(f"{CONFLUENCE_URL}/rest/api/content", json=payload)
    if r.status_code == 200:
        d = r.json()
        page_id = d["id"]
        title = d["title"]
        link = f"https://lululemon.atlassian.net/wiki/pages/viewpage.action?pageId={page_id}"
        print(f"✅ Created: {title}")
        print(f"   ID: {page_id}")
        print(f"   URL: {link}")
    else:
        print(f"❌ Failed: {r.status_code}", file=sys.stderr)
        print(r.text[:500], file=sys.stderr)
        sys.exit(1)


def cmd_update(args):
    """Update an existing Confluence page."""
    s = get_session()

    # Fetch current version
    r = s.get(f"{CONFLUENCE_URL}/rest/api/content/{args.page_id}",
              params={"expand": "version,space"})
    if r.status_code != 200:
        print(f"❌ Failed to fetch page {args.page_id}: {r.status_code}", file=sys.stderr)
        sys.exit(1)

    current = r.json()
    current_version = current["version"]["number"]
    current_title = current["title"]

    body_html = args.body
    if args.body_file:
        with open(args.body_file, "r") as f:
            body_html = f.read()

    if not body_html:
        print("ERROR: Provide --body or --body-file", file=sys.stderr)
        sys.exit(1)

    title = args.title if args.title else current_title

    payload = {
        "version": {"number": current_version + 1},
        "title": title,
        "type": "page",
        "body": {
            "storage": {
                "value": body_html,
                "representation": "storage"
            }
        }
    }

    r = s.put(f"{CONFLUENCE_URL}/rest/api/content/{args.page_id}", json=payload)
    if r.status_code == 200:
        d = r.json()
        new_version = d["version"]["number"]
        print(f"✅ Updated: {title}")
        print(f"   ID: {args.page_id}")
        print(f"   Version: {current_version} → {new_version}")
    else:
        print(f"❌ Failed: {r.status_code}", file=sys.stderr)
        print(r.text[:500], file=sys.stderr)
        sys.exit(1)


def cmd_search(args):
    """Search Confluence pages via CQL."""
    s = get_session()

    r = s.get(f"{CONFLUENCE_URL}/rest/api/content/search",
              params={"cql": args.query, "limit": args.limit})
    if r.status_code != 200:
        print(f"❌ Search failed: {r.status_code}", file=sys.stderr)
        print(r.text[:500], file=sys.stderr)
        sys.exit(1)

    data = r.json()
    results = data.get("results", [])
    total = data.get("totalSize", len(results))

    print(f"── {total} results for: {args.query} ──")
    for p in results:
        pid = p["id"]
        title = p["title"]
        space = p.get("space", {}).get("key", "?")
        print(f"  {pid:<12} [{space}] {title}")

    if not results:
        print("  (no results)")


def cmd_move(args):
    """Move a page to a different space (and optionally under a parent)."""
    s = get_session()

    # Fetch current page (full body + version)
    r = s.get(f"{CONFLUENCE_URL}/rest/api/content/{args.page_id}",
              params={"expand": "version,body.storage,space"})
    if r.status_code != 200:
        print(f"❌ Failed to fetch page {args.page_id}: {r.status_code}", file=sys.stderr)
        sys.exit(1)

    current = r.json()
    src_space = current["space"]["key"]
    title = current["title"]
    body_html = current["body"]["storage"]["value"]

    if src_space == args.space and not args.parent:
        print(f"Page already in space {args.space}. Nothing to do.")
        return

    # Confluence REST API doesn't reliably move across spaces via PUT.
    # Strategy: delete from source, recreate in target.
    # Step 1: Delete
    r = s.delete(f"{CONFLUENCE_URL}/rest/api/content/{args.page_id}")
    if r.status_code != 204:
        print(f"❌ Failed to delete page from {src_space}: {r.status_code}", file=sys.stderr)
        print(r.text[:500], file=sys.stderr)
        sys.exit(1)

    # Step 2: Recreate in target space
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": args.space},
        "body": {
            "storage": {
                "value": body_html,
                "representation": "storage"
            }
        }
    }
    if args.parent:
        payload["ancestors"] = [{"id": str(args.parent)}]

    r = s.post(f"{CONFLUENCE_URL}/rest/api/content", json=payload)
    if r.status_code in (200, 201):
        d = r.json()
        new_id = d["id"]
        print(f"✅ Moved: {title}")
        print(f"   {src_space} → {args.space}")
        print(f"   Old ID: {args.page_id} → New ID: {new_id}")
        print(f"   URL: https://lululemon.atlassian.net/wiki/pages/viewpage.action?pageId={new_id}")
    else:
        print(f"❌ Failed to create in {args.space}: {r.status_code}", file=sys.stderr)
        print(r.text[:500], file=sys.stderr)
        print(f"⚠️  Page was deleted from {src_space} but not recreated! Content may be in trash.", file=sys.stderr)
        sys.exit(1)


def cmd_notifications(args):
    """Approximate Confluence notification inbox — recent page changes and comments."""
    s = get_session()
    days = args.days
    spaces = args.spaces.split(",") if args.spaces else ["EECI", "SRESUP"]

    from datetime import datetime, timezone

    # Get current user to filter out own activity
    me_r = s.get(f"{CONFLUENCE_URL}/rest/api/user/current")
    me_data = me_r.json() if me_r.status_code == 200 else {}
    my_account_id = me_data.get("accountId", "")
    my_user_key = me_data.get("userKey", "")

    # Include personal space in searches
    personal_space = f"~{my_account_id}" if my_account_id else None

    print(f"── Confluence Notifications (last {days}d) ──\n")

    total = 0

    # 1. Recently modified pages in key spaces (by others)
    for space in spaces:
        cql = f'type=page AND space="{space}" AND lastModified > now("-{days}d") ORDER BY lastModified DESC'
        r = s.get(f"{CONFLUENCE_URL}/rest/api/content/search",
                  params={"cql": cql, "limit": 25,
                          "expand": "version,space"})
        if r.status_code != 200:
            print(f"  ⚠ Failed to search space {space}: {r.status_code}")
            continue

        results = r.json().get("results", [])
        # Filter out own edits
        results = [p for p in results if p.get("version", {}).get("by", {}).get("accountId", "") != my_account_id]
        if not results:
            continue

        print(f"📄 SPACE: {space} ({len(results)} pages modified by others)")
        print(f"{'─' * 80}")
        for p in results:
            pid = p["id"]
            title = p.get("title", "?")[:55]
            version = p.get("version", {})
            modified_by = version.get("by", {}).get("displayName", "Unknown")
            when = version.get("friendlyWhen", "?")
            ver_num = version.get("number", "?")
            print(f"  {pid:<12} v{ver_num:<4} {modified_by:<25} {when:<18} {title}")
            total += 1
        print()

    # 2. Pages I contributed to that were recently modified by others
    cql_contrib = f'type=page AND contributor=currentUser() AND lastModified > now("-{days}d") ORDER BY lastModified DESC'
    r = s.get(f"{CONFLUENCE_URL}/rest/api/content/search",
              params={"cql": cql_contrib, "limit": 25,
                      "expand": "version,space"})
    if r.status_code == 200:
        results = r.json().get("results", [])
        # Filter out own edits
        results = [p for p in results if p.get("version", {}).get("by", {}).get("accountId", "") != my_account_id]
        if results:
            print(f"✏️  MY CONTRIBUTIONS (modified by others, last {days}d)")
            print(f"{'─' * 80}")
            for p in results:
                pid = p["id"]
                title = p.get("title", "?")[:45]
                space = p.get("space", {}).get("key", "?")
                version = p.get("version", {})
                modified_by = version.get("by", {}).get("displayName", "Unknown")
                when = version.get("friendlyWhen", "?")
                print(f"  {pid:<12} [{space}] {modified_by:<25} {when:<18} {title}")
                total += 1
            print()

    # 3. Recent comments by others on pages in key spaces + personal space
    comment_spaces = list(spaces)
    if personal_space:
        comment_spaces.append(personal_space)
    comment_results = []
    for space in comment_spaces:
        cql_comments = f'type=comment AND space="{space}" AND lastModified > now("-{days}d")'
        r = s.get(f"{CONFLUENCE_URL}/rest/api/content/search",
                  params={"cql": cql_comments, "limit": 25,
                          "expand": "version,container,space"})
        if r.status_code == 200:
            results = r.json().get("results", [])
            # Filter out own comments
            others = [p for p in results if p.get("version", {}).get("by", {}).get("accountId", "") != my_account_id]
            comment_results.extend(others)

    if comment_results:
        print(f"💬 COMMENTS BY OTHERS ({len(comment_results)} comments)")
        print(f"{'─' * 80}")
        for p in comment_results:
            by = p.get("version", {}).get("by", {}).get("displayName", "?")
            when = p.get("version", {}).get("friendlyWhen", "?")
            space = p.get("space", {}).get("key", "?") if p.get("space") else "?"
            container = p.get("container", {}).get("title", "?")[:45] if p.get("container") else "?"
            print(f"  [{space}] {by:<25} {when:<20} on: {container}")
            total += 1
        print()

    print(f"Total: {total} updates")


def main():
    parser = argparse.ArgumentParser(description="Confluence write operations")
    sub = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = sub.add_parser("create", help="Create a new page")
    p_create.add_argument("--space", required=True, help="Space key (e.g. EECI, ~631a...)")
    p_create.add_argument("--title", required=True, help="Page title")
    p_create.add_argument("--body", help="HTML body content (inline)")
    p_create.add_argument("--body-file", help="Path to HTML file with body content")
    p_create.add_argument("--parent", help="Parent page ID (optional)")

    # update
    p_update = sub.add_parser("update", help="Update an existing page")
    p_update.add_argument("page_id", help="Page ID to update")
    p_update.add_argument("--title", help="New title (optional, keeps current if omitted)")
    p_update.add_argument("--body", help="HTML body content (inline)")
    p_update.add_argument("--body-file", help="Path to HTML file with body content")

    # search
    p_search = sub.add_parser("search", help="Search pages via CQL")
    p_search.add_argument("query", help="CQL query string")
    p_search.add_argument("--limit", type=int, default=25, help="Max results (default: 25)")

    # move
    p_move = sub.add_parser("move", help="Move a page to a different space")
    p_move.add_argument("page_id", help="Page ID to move")
    p_move.add_argument("--space", required=True, help="Target space key")
    p_move.add_argument("--parent", help="Parent page ID in target space (optional)")

    # notifications
    p_notif = sub.add_parser("notifications", help="Recent page changes in key spaces")
    p_notif.add_argument("--days", type=int, default=1, help="Lookback window in days (default: 1)")
    p_notif.add_argument("--spaces", default=None, help="Comma-separated space keys (default: EECI,SRESUP)")

    args = parser.parse_args()

    if args.command == "create":
        cmd_create(args)
    elif args.command == "update":
        cmd_update(args)
    elif args.command == "move":
        cmd_move(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "notifications":
        cmd_notifications(args)


if __name__ == "__main__":
    main()
