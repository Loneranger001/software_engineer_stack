#!/usr/bin/env python3
"""
Pull Confluence Page to Markdown
================================

Fetches a Confluence page and converts the storage format to readable markdown.

USAGE:
    python3 pull_confluence_page.py <PAGE_ID> [OUTPUT_FILE]

EXAMPLES:
    python3 pull_confluence_page.py 5575940659
    python3 pull_confluence_page.py "https://lululemon.atlassian.net/wiki/spaces/EECI/pages/5575940659/Some+Page"
    python3 pull_confluence_page.py "https://lululemon.atlassian.net/wiki/x/EodugAE"
    python3 pull_confluence_page.py 5575940659 ../docs/pulled/adoption-guide.md

ENVIRONMENT:
    JIRA_EMAIL - Your Atlassian email
    JIRA_TOKEN - Your Atlassian API token (works for Confluence too)
"""

import os
import sys
import re
import json
import html
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import parse_qs, urlparse

CONFLUENCE_URL = "https://lululemon.atlassian.net/wiki"

def clean_html_to_markdown(html_content):
    """Convert Confluence storage format HTML to readable markdown."""

    # Unescape HTML entities
    text = html.unescape(html_content)

    # Remove Confluence-specific tags
    text = re.sub(r'<ac:inline-comment-marker[^>]*>', '', text)
    text = re.sub(r'</ac:inline-comment-marker>', '', text)
    text = re.sub(r'<ac:image[^>]*>.*?</ac:image>', '[IMAGE]', text, flags=re.DOTALL)
    text = re.sub(r'<ac:image[^>]*/>', '[IMAGE]', text)
    text = re.sub(r'<ri:attachment[^>]*/>', '', text)
    text = re.sub(r'<ac:caption>.*?</ac:caption>', '', text, flags=re.DOTALL)

    # Handle Confluence links
    def replace_ac_link(match):
        content = match.group(0)
        # Extract link body text
        body_match = re.search(r'<ac:link-body>(.*?)</ac:link-body>', content)
        if body_match:
            return f"**{body_match.group(1)}**"
        # Extract page title
        title_match = re.search(r'ri:content-title="([^"]*)"', content)
        if title_match:
            return f"**{title_match.group(1)}**"
        return "[LINK]"

    text = re.sub(r'<ac:link>.*?</ac:link>', replace_ac_link, text, flags=re.DOTALL)

    # Convert basic HTML to markdown
    text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text)
    text = re.sub(r'<em>(.*?)</em>', r'*\1*', text)
    text = re.sub(r'<u>(.*?)</u>', r'_\1_', text)
    text = re.sub(r'<code>(.*?)</code>', r'`\1`', text)

    # Convert links
    def replace_link(match):
        href = match.group(1)
        text_content = match.group(2)
        # Clean up text content
        text_content = re.sub(r'<[^>]+>', '', text_content)
        return f"[{text_content}]({href})"

    text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', replace_link, text, flags=re.DOTALL)

    # Convert headings
    text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n# \1\n', text)
    text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', text)
    text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', text)

    # Convert lists
    text = re.sub(r'<ol[^>]*>', '\n', text)
    text = re.sub(r'</ol>', '\n', text)
    text = re.sub(r'<ul[^>]*>', '\n', text)
    text = re.sub(r'</ul>', '\n', text)
    text = re.sub(r'<li[^>]*>', '- ', text)
    text = re.sub(r'</li>', '\n', text)

    # Convert paragraphs
    text = re.sub(r'<p[^>]*/>', '\n', text)
    text = re.sub(r'<p[^>]*>', '', text)
    text = re.sub(r'</p>', '\n', text)

    # Remove remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Clean up whitespace
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    text = re.sub(r'  +', ' ', text)

    return text.strip()

def fetch_page(page_id):
    """Fetch a Confluence page by ID."""
    url = f"{CONFLUENCE_URL}/rest/api/content/{page_id}?expand=body.storage,version"

    response = requests.get(url, auth=get_auth())

    if response.status_code != 200:
        print(f"❌ Failed to fetch page: {response.status_code}", file=sys.stderr)
        print(response.text[:500], file=sys.stderr)
        sys.exit(1)

    return response.json()

def get_auth():
    """Return Confluence basic auth credentials from the environment."""
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_TOKEN")

    if not email or not token:
        print("❌ Missing env vars: JIRA_EMAIL and JIRA_TOKEN", file=sys.stderr)
        sys.exit(1)

    return HTTPBasicAuth(email, token)

def extract_page_id(value):
    """Extract or resolve a Confluence page ID from a page ID or URL."""
    if re.fullmatch(r'\d+', value):
        return value

    parsed = urlparse(value)
    query_page_ids = parse_qs(parsed.query).get("pageId")
    if query_page_ids:
        return query_page_ids[0]

    path_page_id_match = re.search(r'/pages/(\d+)', parsed.path)
    if path_page_id_match:
        return path_page_id_match.group(1)

    if re.search(r'/wiki/x/[^/]+/?$', parsed.path):
        return resolve_short_url(value)

    return value

def resolve_short_url(url):
    """Resolve a Confluence short URL and extract the destination page ID."""
    try:
        response = requests.get(url, auth=get_auth(), allow_redirects=True, timeout=30)
    except requests.RequestException as exc:
        print(f"❌ Failed to resolve Confluence short URL: {exc}", file=sys.stderr)
        sys.exit(1)

    if response.status_code >= 400:
        print(f"❌ Failed to resolve Confluence short URL: {response.status_code}", file=sys.stderr)
        print(response.text[:500], file=sys.stderr)
        sys.exit(1)

    page_id = extract_resolved_page_id(response.url, response.text)
    if page_id:
        return page_id

    print("❌ Could not resolve Confluence short URL to a page ID.", file=sys.stderr)
    print("Provide the full Confluence page URL containing /pages/<id> or pageId=<id>.", file=sys.stderr)
    sys.exit(1)

def extract_resolved_page_id(final_url, body):
    """Extract a page ID from a resolved URL or Confluence page body."""
    resolved = extract_page_id_without_redirect(final_url)
    if resolved:
        return resolved

    for pattern in (
        r'pageId=(\d+)',
        r'/pages/(\d+)',
        r'contentId["\']?\s*[:=]\s*["\']?(\d+)',
        r'pageId["\']?\s*[:=]\s*["\']?(\d+)',
    ):
        match = re.search(pattern, body)
        if match:
            return match.group(1)

    return None

def extract_page_id_without_redirect(value):
    """Extract a page ID from URL shapes that already carry one."""
    parsed = urlparse(value)
    query_page_ids = parse_qs(parsed.query).get("pageId")
    if query_page_ids:
        return query_page_ids[0]

    path_page_id_match = re.search(r'/pages/(\d+)', parsed.path)
    if path_page_id_match:
        return path_page_id_match.group(1)

    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 pull_confluence_page.py <PAGE_ID_OR_URL> [OUTPUT_FILE]", file=sys.stderr)
        sys.exit(1)

    raw_input = sys.argv[1]
    page_id = extract_page_id(raw_input)
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"📥 Fetching Confluence page {page_id}...")
    page = fetch_page(page_id)

    title = page.get("title", "Untitled")
    version = page.get("version", {}).get("number", "?")
    author = page.get("version", {}).get("by", {}).get("displayName", "Unknown")
    when = page.get("version", {}).get("friendlyWhen", "Unknown")

    html_content = page.get("body", {}).get("storage", {}).get("value", "")
    markdown_content = clean_html_to_markdown(html_content)

    # Build the final document
    doc = f"""# {title}

**Source**: [Confluence Page](https://lululemon.atlassian.net/wiki/spaces/sdp/pages/{page_id})
**Version**: {version}
**Last Updated**: {when} by {author}
**Pulled**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}

---

{markdown_content}
"""

    if output_file:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(doc)
        print(f"✅ Saved to {output_file}")
    else:
        print(doc)

if __name__ == "__main__":
    main()
