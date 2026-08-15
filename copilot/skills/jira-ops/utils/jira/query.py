#!/usr/bin/env python3
"""Consolidated Jira query tool.

Usage:
    python3 utils/jira/query.py backlog                    # All open issues grouped by project
    python3 utils/jira/query.py issues                     # Flat list of open issues
    python3 utils/jira/query.py epic-stories PROJ-1000     # Child issues of an epic
    python3 utils/jira/query.py review PROJ-1234           # Full details + children
    python3 utils/jira/query.py issue PROJ-1234 PROJ-5678  # Details for specific issues
    python3 utils/jira/query.py users "Paul Q"             # Search users by name
    python3 utils/jira/query.py jql "project = PROJ ..."   # Raw JQL query
"""

import sys
import os
import argparse

from _session import get_session, search_jql, get_issue, extract_text, JIRA_URL, get_create_issue_types, get_create_issue_fields


# ─── Subcommands ───────────────────────────────────────────────────────────────

def cmd_backlog(session, args):
    """Pull all open issues grouped by project and type."""
    issues = search_jql(
        session,
        "assignee = currentUser() AND statusCategory != Done ORDER BY project ASC, priority ASC, updated DESC",
        fields=["key", "summary", "status", "priority", "issuetype", "parent", "labels", "updated", "project"],
    )
    print(f"TOTAL OPEN ISSUES: {len(issues)}\n")

    by_project = {}
    for issue in issues:
        f = issue.get("fields", {})
        proj = f.get("project", {}).get("key", "?")
        entry = {
            "key": issue["key"],
            "type": f.get("issuetype", {}).get("name", ""),
            "summary": f.get("summary", ""),
            "status": f.get("status", {}).get("name", ""),
            "priority": f.get("priority", {}).get("name", "") if f.get("priority") else "",
            "parent": f.get("parent", {}).get("key", "") if f.get("parent") else "",
            "labels": f.get("labels", []),
            "updated": f.get("updated", "")[:10],
        }
        by_project.setdefault(proj, []).append(entry)

    for proj in sorted(by_project):
        items = by_project[proj]
        print(f"{'=' * 70}")
        print(f"  {proj} ({len(items)} issues)")
        print(f"{'=' * 70}")
        type_order = [("Epics", "Epic"), ("Features", "Feature"), ("Stories", "Story"),
                      ("Tasks", "Task"), ("Bugs", "Bug")]
        shown_types = set()
        for label, tname in type_order:
            group = [i for i in items if i["type"] == tname]
            if not group:
                continue
            shown_types.add(tname)
            print(f"\n  --- {label} ---")
            for i in group:
                parent_str = f"  (parent: {i['parent']})" if i["parent"] else ""
                labels_str = f"  [{', '.join(i['labels'])}]" if i["labels"] else ""
                print(f"  {i['key']:15s} {i['priority']:10s} {i['status']:20s} {i['updated']}  {i['summary'][:75]}{parent_str}{labels_str}")
        other = [i for i in items if i["type"] not in shown_types]
        if other:
            print(f"\n  --- Other ---")
            for i in other:
                print(f"  {i['key']:15s} {i['priority']:10s} {i['status']:20s} {i['updated']}  {i['summary'][:75]}")
        print()

    # Summary
    print(f"{'=' * 70}")
    print("  SUMMARY")
    print(f"{'=' * 70}")
    for proj in sorted(by_project):
        items = by_project[proj]
        statuses = {}
        for i in items:
            statuses[i["status"]] = statuses.get(i["status"], 0) + 1
        status_str = ", ".join(f"{s}: {c}" for s, c in sorted(statuses.items()))
        print(f"  {proj:12s} {len(items):3d} issues  ({status_str})")


def cmd_issues(session, args):
    """Flat list of open issues."""
    issues = search_jql(
        session,
        "assignee = currentUser() AND statusCategory != Done ORDER BY priority ASC, updated DESC",
    )
    print(f"Issues assigned to you (excluding Done): {len(issues)}\n")
    print(f"{'Key':<14} {'Type':<12} {'Status':<16} {'Priority':<10} {'Parent':<14} Summary")
    print("-" * 120)
    for issue in issues:
        f = issue.get("fields", {})
        print(
            f"{issue['key']:<14} "
            f"{f.get('issuetype', {}).get('name', ''):<12} "
            f"{f.get('status', {}).get('name', ''):<16} "
            f"{(f.get('priority', {}) or {}).get('name', ''):<10} "
            f"{(f.get('parent', {}) or {}).get('key', ''):<14} "
            f"{f.get('summary', '')[:60]}"
        )
    print(f"\nTotal: {len(issues)}")


def cmd_epic_stories(session, args):
    """Query child issues of an epic."""
    issues = search_jql(
        session,
        f"parent = {args.key}",
        fields=["key", "summary", "status", "priority", "assignee"],
    )
    print(f"Found {len(issues)} issues in {args.key}.\n")
    print(f"{'Key':<14} {'Status':<16} {'Priority':<10} {'Assignee':<25} Summary")
    print("-" * 110)
    for issue in issues:
        f = issue.get("fields", {})
        assignee = f.get("assignee", {}).get("displayName", "Unassigned") if f.get("assignee") else "Unassigned"
        print(
            f"{issue['key']:<14} "
            f"{f.get('status', {}).get('name', ''):<16} "
            f"{(f.get('priority', {}) or {}).get('name', ''):<10} "
            f"{assignee:<25} "
            f"{f.get('summary', '')[:55]}"
        )
    print(f"\nTotal: {len(issues)}")


def cmd_review(session, args):
    """Full details + children for one or more issues."""
    for key in args.keys:
        key = key.upper()
        issue = get_issue(session, key)
        if not issue:
            continue
        f = issue["fields"]
        desc_adf = f.get("description")
        desc = " ".join(extract_text(desc_adf)) if desc_adf else "No description"
        assignee = f.get("assignee", {}).get("displayName", "Unassigned") if f.get("assignee") else "Unassigned"
        parent = f.get("parent", {}).get("key", "-") if f.get("parent") else "-"

        print(f"\n{'=' * 80}")
        print(f"  {key}  |  {f['issuetype']['name']}  |  {(f.get('priority') or {}).get('name', 'N/A')}  |  {f['status']['name']}")
        print(f"  Assignee: {assignee}  |  Parent: {parent}")
        print(f"  Created: {f['created'][:10]}  |  Updated: {f['updated'][:10]}")
        print(f"  Labels: {', '.join(f.get('labels', [])) or 'none'}")
        print(f"  Summary: {f['summary']}")
        print(f"{'=' * 80}")

        # Word-wrap description
        print("  Description:")
        words = desc.split()
        line = "  "
        for w in words:
            if len(line) + len(w) + 1 > 100:
                print(line)
                line = "  " + w
            else:
                line += " " + w if line.strip() else "  " + w
        if line.strip():
            print(line)

        # Comments (all, full text)
        comments = f.get("comment", {}).get("comments", [])
        if comments:
            print(f"\n  Comments ({len(comments)}):")
            for c in comments:
                author = c.get("author", {}).get("displayName", "")
                created = c.get("created", "")[:10]
                body_text = " ".join(extract_text(c.get("body", {})))
                print(f"    [{created}] {author}:")
                # Word-wrap comment body
                words = body_text.split()
                line = "      "
                for w in words:
                    if len(line) + len(w) + 1 > 100:
                        print(line)
                        line = "      " + w
                    else:
                        line += " " + w if line.strip() else "      " + w
                if line.strip():
                    print(line)
                print()

        # Children
        children = search_jql(
            session,
            f"parent = {key} ORDER BY status ASC, priority ASC",
            fields=["key", "summary", "status", "priority", "assignee", "issuetype", "updated"],
        )
        if children:
            open_count = sum(
                1 for c in children
                if c["fields"]["status"].get("statusCategory", {}).get("name") != "Done"
            )
            done_count = len(children) - open_count
            print(f"\n  Child Issues: {len(children)} total ({open_count} open, {done_count} done)")
            print(f"  {'Key':<14} {'Type':<12} {'Priority':<10} {'Status':<16} {'Assignee':<25} Summary")
            print(f"  {'-' * 14} {'-' * 12} {'-' * 10} {'-' * 16} {'-' * 25} {'-' * 40}")
            for c in children:
                cf = c["fields"]
                a = cf.get("assignee", {}).get("displayName", "Unassigned") if cf.get("assignee") else "Unassigned"
                print(
                    f"  {c['key']:<14} {cf['issuetype']['name']:<12} "
                    f"{(cf.get('priority') or {}).get('name', ''):<10} "
                    f"{cf['status']['name']:<16} {a:<25} {cf['summary'][:50]}"
                )
        else:
            print("\n  Child Issues: none")
        print()


def cmd_issue(session, args):
    """Fetch details for specific issue keys."""
    for key in args.keys:
        key = key.upper()
        issue = get_issue(session, key)
        if not issue:
            continue
        f = issue.get("fields", {})
        print("=" * 80)
        print(f"Key: {issue['key']}")
        print(f"Summary: {f.get('summary')}")
        print(f"Status: {f.get('status', {}).get('name')}")
        print(f"Type: {f.get('issuetype', {}).get('name')}")
        print(f"Priority: {(f.get('priority') or {}).get('name', 'None')}")
        assignee = f.get("assignee")
        print(f"Assignee: {assignee.get('displayName') if assignee else 'Unassigned'}")
        parent = f.get("parent")
        if parent:
            print(f"Parent: {parent.get('key', '')} - {parent.get('fields', {}).get('summary', '')}")
        print(f"Labels: {f.get('labels')}")
        print(f"Created: {f.get('created', '')[:10]}")
        print(f"Updated: {f.get('updated', '')[:10]}")

        desc = f.get("description")
        if desc:
            desc_text = " ".join(extract_text(desc))
            if len(desc_text) > 500:
                desc_text = desc_text[:500] + "..."
            print(f"Description: {desc_text}")
        else:
            print("Description: (empty)")

        comments = f.get("comment", {}).get("comments", [])
        if comments:
            print(f"Comments ({len(comments)}):")
            for c in comments:
                author = c.get("author", {}).get("displayName", "")
                created = c.get("created", "")[:10]
                body_text = " ".join(extract_text(c.get("body", {})))
                print(f"  [{created}] {author}:")
                words = body_text.split()
                line = "    "
                for w in words:
                    if len(line) + len(w) + 1 > 100:
                        print(line)
                        line = "    " + w
                    else:
                        line += " " + w if line.strip() else "    " + w
                if line.strip():
                    print(line)
                print()
        print()


def cmd_users(session, args):
    """Search for Jira users by name/email."""
    for query in args.queries:
        r = session.get(f"{JIRA_URL}/rest/api/3/user/search", params={"query": query, "maxResults": 5})
        users = r.json()
        print(f'Search: "{query}"')
        for u in users:
            print(f"  accountId: {u.get('accountId')} | displayName: {u.get('displayName')} | email: {u.get('emailAddress', 'N/A')}")
        if not users:
            print("  (no results)")
        print()


def _find_mentions_in_adf(node):
    """Recursively find mention accountIds in ADF nodes."""
    mentions = set()
    if isinstance(node, dict):
        if node.get("type") == "mention":
            mid = node.get("attrs", {}).get("id", "")
            if mid:
                mentions.add(mid)
        for child in node.get("content", []):
            mentions.update(_find_mentions_in_adf(child))
    elif isinstance(node, list):
        for item in node:
            mentions.update(_find_mentions_in_adf(item))
    return mentions


def cmd_notifications(session, args):
    """Approximate Jira notification inbox — recent activity on your issues."""
    days = args.days
    account_id = os.environ.get("JIRA_ACCOUNT_ID")
    if not account_id:
        r = session.get(f"{JIRA_URL}/rest/api/3/myself")
        if r.status_code == 200:
            account_id = r.json().get("accountId", "")

    from datetime import datetime, timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # 1. Issues where I'm assignee or reporter
    issues = search_jql(
        session,
        f"assignee = currentUser() AND updated >= -{days}d ORDER BY updated DESC",
        fields=["key", "summary", "status", "priority", "issuetype", "updated", "comment", "assignee"],
    )
    reporter_issues = search_jql(
        session,
        f"reporter = currentUser() AND assignee != currentUser() AND updated >= -{days}d ORDER BY updated DESC",
        fields=["key", "summary", "status", "priority", "issuetype", "updated", "comment", "assignee"],
    )
    seen_keys = {i["key"] for i in issues}
    for ri in reporter_issues:
        if ri["key"] not in seen_keys:
            issues.append(ri)
            seen_keys.add(ri["key"])

    # 2. Scan for @mentions in optionally scoped projects where I'm mentioned in recent comments
    mentions_issues = []
    if account_id:
        notification_projects = os.environ.get("JIRA_NOTIFICATION_PROJECTS", "").strip()
        project_scope = f"project in ({notification_projects}) AND " if notification_projects else ""
        mention_candidates = search_jql(
            session,
            f"{project_scope}updated >= -{days}d AND assignee != currentUser() AND reporter != currentUser() ORDER BY updated DESC",
            fields=["key", "summary", "status", "priority", "issuetype", "updated", "comment"],
        )
        for issue in mention_candidates:
            if issue["key"] in seen_keys:
                continue
            comments = issue.get("fields", {}).get("comment", {}).get("comments", [])
            for c in comments:
                c_created = c.get("created", "")
                try:
                    c_dt = datetime.fromisoformat(c_created.replace("Z", "+00:00"))
                    is_recent = c_dt >= cutoff
                except (ValueError, AttributeError):
                    is_recent = False
                if is_recent and account_id in _find_mentions_in_adf(c.get("body", {})):
                    mentions_issues.append(issue)
                    seen_keys.add(issue["key"])
                    break

    # Categorize assignee/reporter issues
    new_comments = []
    other_updates = []

    for issue in issues:
        f = issue.get("fields", {})
        key = issue["key"]
        summary = f.get("summary", "")[:65]
        status = f.get("status", {}).get("name", "")
        updated = f.get("updated", "")

        comments = f.get("comment", {}).get("comments", [])
        recent_comments = []
        for c in comments:
            c_created = c.get("created", "")
            c_author_id = c.get("author", {}).get("accountId", "")
            c_author_name = c.get("author", {}).get("displayName", "")
            try:
                c_dt = datetime.fromisoformat(c_created.replace("Z", "+00:00"))
                is_recent = c_dt >= cutoff
            except (ValueError, AttributeError):
                is_recent = False
            is_someone_else = (account_id and c_author_id != account_id) or (not account_id)
            if is_recent and is_someone_else:
                body_preview = " ".join(extract_text(c.get("body", {})))[:80]
                recent_comments.append((c_author_name, c_created[:16], body_preview))

        if recent_comments:
            new_comments.append((key, summary, status, recent_comments))
        else:
            other_updates.append((key, summary, status, updated[:16]))

    # Categorize @mention issues
    mention_entries = []
    for issue in mentions_issues:
        f = issue.get("fields", {})
        key = issue["key"]
        summary = f.get("summary", "")[:65]
        status = f.get("status", {}).get("name", "")
        comments = f.get("comment", {}).get("comments", [])
        for c in comments:
            c_created = c.get("created", "")
            try:
                c_dt = datetime.fromisoformat(c_created.replace("Z", "+00:00"))
                is_recent = c_dt >= cutoff
            except (ValueError, AttributeError):
                is_recent = False
            if is_recent and account_id in _find_mentions_in_adf(c.get("body", {})):
                c_author_name = c.get("author", {}).get("displayName", "")
                body_preview = " ".join(extract_text(c.get("body", {})))[:80]
                mention_entries.append((key, summary, status, c_author_name, c_created[:16], body_preview))

    # Print results
    total = len(issues) + len(mentions_issues)
    print(f"── Jira Notifications (last {days}d) ── {total} issues with activity ──\n")

    if mention_entries:
        print(f"📣 @MENTIONS ({len(mention_entries)} issues)")
        print(f"{'─' * 90}")
        for key, summary, status, author, when, preview in mention_entries:
            print(f"  {key:<14} [{status}]  {summary}")
            print(f"    → {author} ({when}): {preview}")
        print()

    if new_comments:
        print(f"💬 NEW COMMENTS ({len(new_comments)} issues)")
        print(f"{'─' * 90}")
        for key, summary, status, comments_list in new_comments:
            print(f"  {key:<14} [{status}]  {summary}")
            for author, when, preview in comments_list:
                print(f"    → {author} ({when}): {preview}")
        print()

    if other_updates:
        print(f"📋 OTHER UPDATES ({len(other_updates)} issues)")
        print(f"{'─' * 90}")
        for key, summary, status, updated in other_updates:
            print(f"  {key:<14} [{status}]  {updated}  {summary}")
        print()

    print(f"Total: {total} issues  |  {len(mention_entries)} @mentions  |  {len(new_comments)} with new comments  |  {len(other_updates)} other updates")


def cmd_jql(session, args):
    """Run arbitrary JQL and display results."""
    issues = search_jql(session, args.jql)
    print(f"Results: {len(issues)}\n")
    print(f"{'Key':<14} {'Type':<12} {'Status':<16} {'Priority':<10} Summary")
    print("-" * 100)
    for issue in issues:
        f = issue.get("fields", {})
        print(
            f"{issue['key']:<14} "
            f"{f.get('issuetype', {}).get('name', ''):<12} "
            f"{f.get('status', {}).get('name', ''):<16} "
            f"{(f.get('priority', {}) or {}).get('name', ''):<10} "
            f"{f.get('summary', '')[:55]}"
        )


def cmd_create_meta(session, args):
    """Inspect Jira create metadata for a project and optionally one issue type."""
    issue_types = get_create_issue_types(session, args.project)
    if not issue_types:
        sys.exit(1)

    if not args.issue_type:
        print(f"Createable issue types for {args.project}:\n")
        print(f"{'Id':<8} {'Subtask':<8} {'Level':<6} Name")
        print("-" * 60)
        for issue_type in issue_types:
            print(
                f"{issue_type['id']:<8} "
                f"{str(issue_type.get('subtask', False)):<8} "
                f"{str(issue_type.get('hierarchyLevel', '')):<6} "
                f"{issue_type['name']}"
            )
        return

    selected = None
    for issue_type in issue_types:
        if issue_type["name"].lower() == args.issue_type.lower() or issue_type["id"] == args.issue_type:
            selected = issue_type
            break
    if selected is None:
        for issue_type in issue_types:
            if args.issue_type.lower() in issue_type["name"].lower():
                selected = issue_type
                break
    if selected is None:
        available = ", ".join(sorted(issue_type["name"] for issue_type in issue_types))
        print(f"FAIL: Issue type '{args.issue_type}' is not valid for {args.project}. Available: {available}", file=sys.stderr)
        sys.exit(1)

    fields = get_create_issue_fields(session, args.project, selected["id"])
    print(f"Create metadata for {args.project} / {selected['name']} ({selected['id']}):\n")
    print(f"Sub-task: {selected.get('subtask', False)}")
    print(f"Hierarchy level: {selected.get('hierarchyLevel', '')}\n")
    print("Required fields:")
    required_fields = [field for field in fields if field.get("required")]
    if not required_fields:
        print("  (none)")
    else:
        for field in required_fields:
            print(f"  {field['key']}: {field['name']}")

    if args.verbose:
        print("\nAll fields:")
        for field in fields:
            allowed = field.get("allowedValues", [])
            allowed_suffix = f" | allowedValues={len(allowed)}" if allowed else ""
            print(f"  {field['key']}: {field['name']} | required={field.get('required', False)}{allowed_suffix}")


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Jira Query Tool", prog="query.py")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("backlog", help="All open issues grouped by project")
    sub.add_parser("issues", help="Flat list of open issues")

    p = sub.add_parser("epic-stories", help="Child issues of an epic")
    p.add_argument("key", help="Epic key (e.g., PROJ-1000)")

    p = sub.add_parser("review", help="Full details + children")
    p.add_argument("keys", nargs="+", help="Issue key(s)")

    p = sub.add_parser("issue", help="Details for specific issues")
    p.add_argument("keys", nargs="+", help="Issue key(s)")

    p = sub.add_parser("users", help="Search users by name")
    p.add_argument("queries", nargs="+", help="Name(s) to search")

    p = sub.add_parser("jql", help="Run raw JQL")
    p.add_argument("jql", help="JQL string")

    p = sub.add_parser("create-meta", help="Inspect create metadata for a project or issue type")
    p.add_argument("--project", required=True, help="Project key")
    p.add_argument("--issue-type", help="Issue type name or id")
    p.add_argument("--verbose", action="store_true", help="Show all fields, not just required ones")

    p = sub.add_parser("notifications", help="Recent activity on your issues")
    p.add_argument("--days", type=int, default=1, help="Lookback window in days (default: 1)")

    args = parser.parse_args()
    session = get_session()

    commands = {
        "backlog": cmd_backlog,
        "issues": cmd_issues,
        "epic-stories": cmd_epic_stories,
        "review": cmd_review,
        "issue": cmd_issue,
        "users": cmd_users,
        "jql": cmd_jql,
        "create-meta": cmd_create_meta,
        "notifications": cmd_notifications,
    }
    commands[args.command](session, args)


if __name__ == "__main__":
    main()
