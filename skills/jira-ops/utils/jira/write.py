#!/usr/bin/env python3
"""Consolidated Jira write tool — comments, transitions, story creation, fix versions.

Usage:
    python3 utils/jira/write.py comment PROJ-1234 "Your comment text"
    python3 utils/jira/write.py comment PROJ-1234 --file /tmp/comment.json
    python3 utils/jira/write.py transition PROJ-1234 "Done"
    python3 utils/jira/write.py transition PROJ-1234 "In Progress"
    python3 utils/jira/write.py create --title "Fix X" --description "Details" --epic EECI-9999
    python3 utils/jira/write.py create --title "Fix X" --description "Details" --epic PROJ-1000 --dry-run
    python3 utils/jira/write.py create --file /tmp/story.json
    python3 utils/jira/write.py assign PROJ-1234 --account-id 712020:xxxxx
    python3 utils/jira/write.py assign PROJ-1234 --search "Paul Quincoses"
    python3 utils/jira/write.py fix-version PROJ-1234 "Q1'26"
    python3 utils/jira/write.py fix-version PROJ-1234 --clear
    python3 utils/jira/write.py fix-version --list
    python3 utils/jira/write.py component PROJ-1234 "My Component"
    python3 utils/jira/write.py component PROJ-1234 --clear
    python3 utils/jira/write.py component --list
"""

import sys
import json
import re
import argparse
import os

from _session import get_session, JIRA_URL, get_current_user, get_issue, get_create_issue_types


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _parse_inline_marks(text):
    """Parse inline markdown (bold, code, italic) into ADF text nodes with marks."""
    nodes = []
    # Pattern: **bold**, `code`, *italic* (in that order to avoid conflicts)
    pattern = re.compile(r'(\*\*(.+?)\*\*|`(.+?)`|\*(.+?)\*)')
    last = 0
    for m in pattern.finditer(text):
        # Add plain text before this match
        if m.start() > last:
            plain = text[last:m.start()]
            if plain:
                nodes.append({"type": "text", "text": plain})
        if m.group(2):  # **bold**
            nodes.append({"type": "text", "text": m.group(2), "marks": [{"type": "strong"}]})
        elif m.group(3):  # `code`
            nodes.append({"type": "text", "text": m.group(3), "marks": [{"type": "code"}]})
        elif m.group(4):  # *italic*
            nodes.append({"type": "text", "text": m.group(4), "marks": [{"type": "em"}]})
        last = m.end()
    # Trailing plain text
    if last < len(text):
        remaining = text[last:]
        if remaining:
            nodes.append({"type": "text", "text": remaining})
    if not nodes:
        nodes.append({"type": "text", "text": text})
    return nodes


def convert_markdown_to_adf(text):
    """Convert markdown to ADF with headings, bold, code, italic, and grouped bullet lists."""
    # Handle both real newlines and literal \n from CLI
    lines = text.replace("\\n", "\n").strip().split("\n")
    content = []
    bullet_items = []  # accumulate consecutive bullet items
    task_items = []

    def flush_bullets():
        if bullet_items:
            content.append({"type": "bulletList", "content": list(bullet_items)})
            bullet_items.clear()

    def flush_tasks():
        if task_items:
            content.append({"type": "taskList", "content": list(task_items)})
            task_items.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_bullets()
            flush_tasks()
            continue

        # Headings: #, ##, ###
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if heading_match:
            flush_bullets()
            flush_tasks()
            level = len(heading_match.group(1))
            content.append({"type": "heading", "attrs": {"level": level},
                            "content": _parse_inline_marks(heading_match.group(2))})
            continue

        # Task items: - [ ] item / - [x] item
        task_match = re.match(r'^[-•]\s+\[([ xX])\]\s+(.+)$', stripped)
        if task_match:
            flush_bullets()
            task_items.append({
                "type": "taskItem",
                "attrs": {"state": "DONE" if task_match.group(1).lower() == "x" else "TODO"},
                "content": [{"type": "paragraph", "content": _parse_inline_marks(task_match.group(2))}],
            })
            continue

        # Bullet items: - or •
        bullet_match = re.match(r'^[-•]\s+(.+)$', stripped)
        if bullet_match:
            flush_tasks()
            bullet_items.append({
                "type": "listItem",
                "content": [{"type": "paragraph", "content": _parse_inline_marks(bullet_match.group(1))}]
            })
            continue

        # Regular paragraph
        flush_bullets()
        flush_tasks()
        content.append({"type": "paragraph", "content": _parse_inline_marks(stripped)})

    flush_bullets()
    flush_tasks()
    return {"type": "doc", "version": 1, "content": content}


def _normalize_labels(labels_text):
    return [label.strip() for label in labels_text.split(",") if label.strip()]


def _resolve_project_key(session, explicit_project=None, parent_key=None, issue_key=None):
    if explicit_project:
        return explicit_project

    env_project = os.environ.get("JIRA_PROJECT")
    if env_project:
        return env_project

    reference_key = parent_key or issue_key
    if reference_key:
        issue = get_issue(session, reference_key, fields="project")
        if issue:
            project_key = issue.get("fields", {}).get("project", {}).get("key")
            if project_key:
                return project_key

    print("FAIL: Project key is required. Provide --project, set JIRA_PROJECT, or supply a resolvable parent/issue key.", file=sys.stderr)
    sys.exit(1)


def _resolve_issue_type(session, project_key, issue_type_name):
    issue_types = get_create_issue_types(session, project_key)
    if not issue_types:
        print(f"FAIL: No issue types available for project {project_key}", file=sys.stderr)
        sys.exit(1)

    lowered = issue_type_name.lower()
    for issue_type in issue_types:
        if issue_type["name"].lower() == lowered or issue_type["id"] == issue_type_name:
            return issue_type, issue_types

    for issue_type in issue_types:
        if lowered in issue_type["name"].lower():
            return issue_type, issue_types

    available = ", ".join(sorted(issue_type["name"] for issue_type in issue_types))
    print(f"FAIL: Issue type '{issue_type_name}' is not valid for {project_key}. Available: {available}", file=sys.stderr)
    sys.exit(1)


def _validate_parent_for_create(session, project_key, issue_type, parent_key):
    if issue_type.get("subtask") and not parent_key:
        print("FAIL: Sub-task creation requires --parent", file=sys.stderr)
        sys.exit(1)

    if not parent_key:
        return

    parent_issue = get_issue(session, parent_key, fields="summary,issuetype")
    if not parent_issue:
        print(f"FAIL: Unable to fetch parent {parent_key}", file=sys.stderr)
        sys.exit(1)

    parent_type = parent_issue.get("fields", {}).get("issuetype", {}).get("name", "")
    child_type = issue_type["name"]

    if issue_type.get("subtask"):
        if parent_type == "Sub-task":
            print(f"FAIL: Cannot create sub-task under sub-task parent {parent_key}", file=sys.stderr)
            sys.exit(1)
        return

    if parent_type != "Epic":
        print(
            f"FAIL: Cannot create {child_type} under {parent_type} parent {parent_key}. "
            f"Use --issue-type Sub-task for a Story/Task parent, or use an Epic parent for {child_type}.",
            file=sys.stderr,
        )
        sys.exit(1)


# ─── Subcommands ───────────────────────────────────────────────────────────────

def cmd_comment(session, args):
    """Add a comment to a Jira issue."""
    if args.file:
        with open(args.file) as f:
            adf_body = json.load(f)
    else:
        adf_body = convert_markdown_to_adf(args.text)

    r = session.post(f"{JIRA_URL}/rest/api/3/issue/{args.key}/comment", json={"body": adf_body})
    if r.status_code in (200, 201):
        print(f"OK: Comment added to {args.key} (id: {r.json().get('id')})")
    else:
        print(f"FAIL: {r.status_code} {r.text[:300]}", file=sys.stderr)
        sys.exit(1)


def cmd_transition(session, args):
    """Transition a Jira issue to a target status."""
    key = args.key
    target = args.status
    force = getattr(args, 'force', False)

    # Get current status and assignee
    r = session.get(f"{JIRA_URL}/rest/api/3/issue/{key}", params={"fields": "status,assignee"})
    if r.status_code != 200:
        print(f"FAIL: Cannot fetch {key}: {r.status_code}", file=sys.stderr)
        sys.exit(1)
    fields = r.json()["fields"]
    current = fields["status"]["name"]
    print(f"Current: {current}")

    # Ownership check: verify issue is assigned to current user
    assignee = fields.get("assignee")
    current_user_id = get_current_user(session)
    if current_user_id and assignee:
        assignee_id = assignee.get("accountId")
        if assignee_id != current_user_id:
            assignee_name = assignee.get("displayName", assignee_id)
            if not force:
                print(f"BLOCKED: {key} is assigned to {assignee_name}, not you.", file=sys.stderr)
                print(f"  Use --force to transition anyway.", file=sys.stderr)
                sys.exit(1)
            else:
                print(f"WARNING: {key} is assigned to {assignee_name} (--force used)")
    elif not assignee and not force:
        print(f"WARNING: {key} is unassigned (proceeding)")

    # Get available transitions
    r = session.get(f"{JIRA_URL}/rest/api/3/issue/{key}/transitions")
    transitions = r.json().get("transitions", [])

    # Find matching transition
    tid = None
    for t in transitions:
        if t["to"]["name"].lower() == target.lower() or t["name"].lower() == target.lower():
            tid = t["id"]
            break
    if not tid:
        # Partial match
        for t in transitions:
            if target.lower() in t["to"]["name"].lower() or target.lower() in t["name"].lower():
                tid = t["id"]
                break

    if not tid:
        avail = ", ".join(f"{t['name']} -> {t['to']['name']}" for t in transitions)
        print(f"FAIL: No transition to '{target}'. Available: {avail}", file=sys.stderr)
        sys.exit(1)

    r = session.post(f"{JIRA_URL}/rest/api/3/issue/{key}/transitions", json={"transition": {"id": tid}})
    if r.status_code in (200, 204):
        print(f"OK: {key} moved from '{current}' to '{target}'")
    else:
        print(f"FAIL: {r.status_code} {r.text[:300]}", file=sys.stderr)
        sys.exit(1)


def cmd_create(session, args):
    """Create a new Jira issue."""
    if args.file:
        with open(args.file) as f:
            story_data = json.load(f)
    else:
        if args.parent and args.epic:
            print("FAIL: Use either --parent or --epic, not both", file=sys.stderr)
            sys.exit(1)

        description_text = args.description
        if args.description_file:
            with open(args.description_file) as f:
                description_text = f.read()

        if not args.title or description_text is None:
            print("FAIL: --title and --description/--description-file required (or use --file)", file=sys.stderr)
            sys.exit(1)

        project_key = _resolve_project_key(session, explicit_project=args.project, parent_key=args.parent or args.epic)
        issue_type, _ = _resolve_issue_type(session, project_key, args.issue_type)
        parent_key = args.parent or args.epic
        _validate_parent_for_create(session, project_key, issue_type, parent_key)

        story_data = {
            "fields": {
                "project": {"key": project_key},
                "summary": args.title,
                "description": convert_markdown_to_adf(description_text),
                "issuetype": {"id": issue_type["id"]},
            }
        }
        if parent_key:
            story_data["fields"]["parent"] = {"key": parent_key}
        if args.component:
            story_data["fields"]["components"] = [{"name": args.component}]
        if args.labels:
            story_data["fields"]["labels"] = _normalize_labels(args.labels)

    if args.dry_run:
        print("DRY RUN: Jira issue was not created.")
        print(json.dumps(story_data, indent=2, sort_keys=True))
        return

    r = session.post(f"{JIRA_URL}/rest/api/3/issue", json=story_data)
    if r.status_code in (200, 201):
        result = r.json()
        print(f"OK: Created {result['key']} — https://lululemon.atlassian.net/browse/{result['key']}")
    else:
        print(f"FAIL: {r.status_code} {r.text[:500]}", file=sys.stderr)
        sys.exit(1)


def cmd_component(session, args):
    """Set, clear, or list components."""
    project = _resolve_project_key(session, explicit_project=args.project, issue_key=args.key) if (args.list or args.key) else None

    # List mode
    if args.list:
        r = session.get(f"{JIRA_URL}/rest/api/3/project/{project}/components")
        if r.status_code != 200:
            print(f"FAIL: {r.status_code} {r.text[:300]}", file=sys.stderr)
            sys.exit(1)
        components = r.json()
        print(f"Components for {project}:")
        for c in components:
            lead = c.get("lead", {}).get("displayName", "")
            print(f"  {c['id']:>6}  {c['name']:<40} {lead}")
        return

    key = args.key
    if not key:
        print("FAIL: Issue key required (or use --list)", file=sys.stderr)
        sys.exit(1)

    # Show current
    r = session.get(f"{JIRA_URL}/rest/api/3/issue/{key}", params={"fields": "components"})
    current = r.json()["fields"]["components"]
    if current:
        print(f"Current: {', '.join(c['name'] for c in current)}")
    else:
        print("Current: none")

    # Clear mode
    if args.clear:
        r = session.put(f"{JIRA_URL}/rest/api/3/issue/{key}", json={"fields": {"components": []}})
        if r.status_code == 204:
            print(f"OK: Cleared components on {key}")
        else:
            print(f"FAIL: {r.status_code} {r.text[:300]}", file=sys.stderr)
            sys.exit(1)
        return

    if not args.name:
        print("FAIL: Provide component name or use --clear/--list", file=sys.stderr)
        sys.exit(1)

    r = session.put(f"{JIRA_URL}/rest/api/3/issue/{key}",
        json={"fields": {"components": [{"name": args.name}]}})
    if r.status_code == 204:
        print(f"OK: {key} component set to '{args.name}'")
    else:
        print(f"FAIL: {r.status_code} {r.text[:300]}", file=sys.stderr)
        sys.exit(1)


def cmd_fix_version(session, args):
    """Set, clear, or list fix versions."""
    project = _resolve_project_key(session, explicit_project=args.project, issue_key=args.key) if (args.list or args.key) else None

    # List mode
    if args.list:
        r = session.get(f"{JIRA_URL}/rest/api/3/project/{project}/versions")
        if r.status_code != 200:
            print(f"FAIL: {r.status_code} {r.text[:300]}", file=sys.stderr)
            sys.exit(1)
        versions = r.json()
        unreleased = [v for v in versions if not v.get("released")]
        print(f"Unreleased versions for {project}:")
        for v in unreleased:
            print(f"  {v['id']:>6}  {v['name']:<40} {v.get('releaseDate', 'no date')}")
        return

    key = args.key
    if not key:
        print("FAIL: Issue key required (or use --list)", file=sys.stderr)
        sys.exit(1)

    # Show current
    r = session.get(f"{JIRA_URL}/rest/api/3/issue/{key}", params={"fields": "fixVersions"})
    current = r.json()["fields"]["fixVersions"]
    if current:
        print(f"Current: {', '.join(v['name'] for v in current)}")
    else:
        print("Current: none")

    # Clear mode
    if args.clear:
        r = session.put(f"{JIRA_URL}/rest/api/3/issue/{key}", json={"fields": {"fixVersions": []}})
        if r.status_code == 204:
            print(f"OK: Cleared fix versions on {key}")
        else:
            print(f"FAIL: {r.status_code} {r.text[:300]}", file=sys.stderr)
            sys.exit(1)
        return

    if not args.version:
        print("FAIL: Provide version name or use --clear/--list", file=sys.stderr)
        sys.exit(1)

    # Find matching version by partial name match
    r = session.get(f"{JIRA_URL}/rest/api/3/project/{project}/versions")
    versions = r.json()
    target = args.version.lower()
    match = None
    for v in versions:
        if target == v["name"].lower():
            match = v
            break
    if not match:
        for v in versions:
            if target in v["name"].lower():
                match = v
                break
    if not match:
        print(f"FAIL: No version matching '{args.version}'. Use --list to see options.", file=sys.stderr)
        sys.exit(1)

    r = session.put(f"{JIRA_URL}/rest/api/3/issue/{key}", json={"fields": {"fixVersions": [{"id": match["id"]}]}})
    if r.status_code == 204:
        print(f"OK: {key} fix version set to '{match['name']}'")
    else:
        print(f"FAIL: {r.status_code} {r.text[:300]}", file=sys.stderr)
        sys.exit(1)


def cmd_assign(session, args):
    """Assign an issue to a user."""
    account_id = args.account_id
    if args.search:
        r = session.get(f"{JIRA_URL}/rest/api/3/user/search", params={"query": args.search, "maxResults": 1})
        users = r.json()
        if not users:
            print(f"FAIL: No user found for '{args.search}'", file=sys.stderr)
            sys.exit(1)
        account_id = users[0]["accountId"]
        print(f"Found: {users[0].get('displayName')} ({account_id})")

    if not account_id:
        print("FAIL: Provide --account-id or --search", file=sys.stderr)
        sys.exit(1)

    r = session.put(f"{JIRA_URL}/rest/api/3/issue/{args.key}/assignee", json={"accountId": account_id})
    if r.status_code in (200, 204):
        print(f"OK: {args.key} assigned")
    else:
        print(f"FAIL: {r.status_code} {r.text[:300]}", file=sys.stderr)
        sys.exit(1)


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Jira Write Tool", prog="write.py")
    sub = parser.add_subparsers(dest="command", required=True)

    # comment
    p = sub.add_parser("comment", help="Add comment to an issue")
    p.add_argument("key", help="Issue key (e.g., PROJ-1234)")
    p.add_argument("text", nargs="?", help="Comment text (supports basic markdown)")
    p.add_argument("--file", help="Path to ADF JSON file")

    # transition
    p = sub.add_parser("transition", help="Change issue status")
    p.add_argument("key", help="Issue key")
    p.add_argument("status", help='Target status (e.g., "Done", "In Progress")')
    p.add_argument("--force", action="store_true", help="Override ownership check")

    # create
    p = sub.add_parser("create", help="Create a new Jira issue")
    p.add_argument("--title", help="Issue summary")
    p.add_argument("--description", help="Issue description in markdown")
    p.add_argument("--description-file", help="Path to markdown description file")
    p.add_argument("--epic", help="Convenience alias for --parent when creating a story under an epic")
    p.add_argument("--parent", help="Parent issue key")
    p.add_argument("--issue-type", default="Story", help="Issue type name (default: Story)")
    p.add_argument("--project", help="Project key (defaults to JIRA_PROJECT or can be inferred from parent)")
    p.add_argument("--component", help="Component name")
    p.add_argument("--labels", help="Comma-separated labels")
    p.add_argument("--file", help="JSON file with full story payload")
    p.add_argument("--dry-run", action="store_true", help="Validate and print the resolved payload without creating the issue")

    # assign
    p = sub.add_parser("assign", help="Assign issue to user")
    p.add_argument("key", help="Issue key")
    p.add_argument("--account-id", help="User account ID")
    p.add_argument("--search", help="Search user by name (picks first match)")

    # fix-version
    p = sub.add_parser("fix-version", help="Set or clear fix version")
    p.add_argument("key", nargs="?", help="Issue key")
    p.add_argument("version", nargs="?", help="Version name (partial match supported, e.g. \"Q1'26\")")
    p.add_argument("--clear", action="store_true", help="Remove all fix versions")
    p.add_argument("--list", action="store_true", help="List unreleased versions for project")
    p.add_argument("--project", help="Project key (defaults to JIRA_PROJECT or can be inferred from issue key)")

    # component
    p = sub.add_parser("component", help="Set or clear component")
    p.add_argument("key", nargs="?", help="Issue key")
    p.add_argument("name", nargs="?", help="Component name")
    p.add_argument("--clear", action="store_true", help="Remove all components")
    p.add_argument("--list", action="store_true", help="List components for project")
    p.add_argument("--project", help="Project key (defaults to JIRA_PROJECT or can be inferred from issue key)")

    args = parser.parse_args()
    session = get_session()

    commands = {
        "comment": cmd_comment,
        "transition": cmd_transition,
        "create": cmd_create,
        "assign": cmd_assign,
        "fix-version": cmd_fix_version,
        "component": cmd_component,
    }
    commands[args.command](session, args)


if __name__ == "__main__":
    main()
