"""Shared Jira session setup and helpers. Imported by query.py, write.py, bulk.py."""

import os
import sys
import json
import requests
from requests.auth import HTTPBasicAuth

JIRA_URL = os.environ.get("JIRA_URL", "https://lululemon.atlassian.net")


def _load_env_from_zshrc():
    """Fallback: parse env vars from ~/.zshrc when not in shell environment."""
    zshrc = os.path.expanduser("~/.zshrc")
    if not os.path.exists(zshrc):
        return
    with open(zshrc) as f:
        for line in f:
            line = line.strip()
            if line.startswith("export ") and "=" in line:
                parts = line[7:].split("=", 1)
                key = parts[0].strip()
                val = parts[1].strip().strip('"').strip("'")
                if key in ("JIRA_EMAIL", "JIRA_TOKEN", "JIRA_ACCOUNT_ID", "JIRA_URL", "PRIVATE_TOKEN") and key not in os.environ:
                    os.environ[key] = val


def get_session():
    """Create authenticated Jira session. Exits on missing env vars."""
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_TOKEN")
    if not email or not token:
        _load_env_from_zshrc()
        email = os.environ.get("JIRA_EMAIL")
        token = os.environ.get("JIRA_TOKEN")
    if not email or not token:
        print("ERROR: Missing JIRA_EMAIL or JIRA_TOKEN", file=sys.stderr)
        sys.exit(1)
    session = requests.Session()
    session.auth = HTTPBasicAuth(email, token)
    session.headers.update({"Accept": "application/json", "Content-Type": "application/json"})
    return session


def extract_text(node):
    """Recursively extract text from ADF (Atlassian Document Format) nodes."""
    texts = []
    if isinstance(node, dict):
        if node.get("type") == "text":
            texts.append(node.get("text", ""))
        for child in node.get("content", []):
            texts.extend(extract_text(child))
    elif isinstance(node, list):
        for item in node:
            texts.extend(extract_text(item))
    return texts


def search_jql(session, jql, fields=None, max_results=100):
    """Paginate through JQL results using nextPageToken."""
    if fields is None:
        fields = ["key", "summary", "status", "priority", "issuetype", "parent", "labels", "updated", "project"]
    results = []
    next_token = None
    while True:
        payload = {"jql": jql, "maxResults": max_results, "fields": fields}
        if next_token:
            payload["nextPageToken"] = next_token
        r = session.post(f"{JIRA_URL}/rest/api/3/search/jql", json=payload)
        if r.status_code != 200:
            print(f"ERROR: {r.status_code} {r.text[:300]}", file=sys.stderr)
            break
        data = r.json()
        results.extend(data.get("issues", []))
        if data.get("isLast", True):
            break
        next_token = data.get("nextPageToken")
        if not next_token:
            break
    return results


def get_issue(session, key, fields=None):
    """Fetch a single issue by key."""
    if fields is None:
        fields = "summary,status,priority,description,issuetype,labels,created,updated,parent,assignee,comment"
    r = session.get(f"{JIRA_URL}/rest/api/3/issue/{key}", params={"fields": fields})
    if r.status_code != 200:
        print(f"ERROR fetching {key}: {r.status_code} {r.text[:200]}", file=sys.stderr)
        return None
    return r.json()


def get_current_user(session):
    """Get the current authenticated user's account ID. Caches result."""
    if not hasattr(get_current_user, '_cached'):
        account_id = os.environ.get("JIRA_ACCOUNT_ID")
        if account_id:
            get_current_user._cached = account_id
        else:
            r = session.get(f"{JIRA_URL}/rest/api/3/myself")
            if r.status_code == 200:
                get_current_user._cached = r.json().get("accountId")
            else:
                get_current_user._cached = None
    return get_current_user._cached


def get_create_issue_types(session, project_key):
    """List createable issue types for a project."""
    r = session.get(f"{JIRA_URL}/rest/api/3/issue/createmeta/{project_key}/issuetypes")
    if r.status_code != 200:
        print(f"ERROR: {r.status_code} {r.text[:300]}", file=sys.stderr)
        return []
    return r.json().get("issueTypes", [])


def get_create_issue_fields(session, project_key, issue_type_id):
    """Return create metadata fields for a given project issue type."""
    r = session.get(f"{JIRA_URL}/rest/api/3/issue/createmeta/{project_key}/issuetypes/{issue_type_id}")
    if r.status_code != 200:
        print(f"ERROR: {r.status_code} {r.text[:300]}", file=sys.stderr)
        return []
    return r.json().get("fields", [])
