"""Shared Jira session setup and helpers. Imported by query.py, write.py, bulk.py."""

import os
import sys
import json
import requests
from requests.auth import HTTPBasicAuth

# The Atlassian tenant is never stored in this framework — it is read from the
# environment of the machine running the agent, like SES_DB_CONN and friends.
JIRA_URL = os.environ.get("JIRA_URL", "").rstrip("/")

ENV_HELP = """Set these in your shell before using the jira-ops skill:
  export JIRA_URL=https://your-org.atlassian.net
  export JIRA_EMAIL=you@your-org.example
  export JIRA_TOKEN=...   # https://id.atlassian.com/manage-profile/security/api-tokens
Optional: JIRA_ACCOUNT_ID, JIRA_PROJECT, JIRA_NOTIFICATION_PROJECTS"""


def get_session():
    """Create authenticated Jira session. Exits on missing configuration."""
    missing = [name for name, value in (
        ("JIRA_URL", JIRA_URL),
        ("JIRA_EMAIL", os.environ.get("JIRA_EMAIL")),
        ("JIRA_TOKEN", os.environ.get("JIRA_TOKEN")),
    ) if not value]
    if missing:
        print(f"ERROR: missing environment variable(s): {', '.join(missing)}", file=sys.stderr)
        print(ENV_HELP, file=sys.stderr)
        sys.exit(1)
    session = requests.Session()
    session.auth = HTTPBasicAuth(os.environ["JIRA_EMAIL"], os.environ["JIRA_TOKEN"])
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
