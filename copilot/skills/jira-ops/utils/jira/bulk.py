#!/usr/bin/env python3
"""Bulk Jira operations — comment, transition, or assign multiple issues at once.

Usage:
    python3 utils/jira/bulk.py comment EECI-1234,EECI-5678 "Closing — remediation complete."
    python3 utils/jira/bulk.py transition EECI-1234,EECI-5678 Done
    python3 utils/jira/bulk.py assign EECI-1234,EECI-5678 --search "Paul Quincoses"
    python3 utils/jira/bulk.py assign EECI-1234,EECI-5678 --account-id 712020:xxxxx
"""

import sys
import argparse

from _session import get_session, JIRA_URL, get_current_user


def bulk_comment(session, keys, text):
    """Add the same comment to multiple issues."""
    adf = {
        "type": "doc", "version": 1,
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
    }
    for key in keys:
        r = session.post(f"{JIRA_URL}/rest/api/3/issue/{key}/comment", json={"body": adf})
        status = "OK" if r.status_code in (200, 201) else f"FAIL ({r.status_code})"
        print(f"  [{status}] Comment on {key}")


def bulk_transition(session, keys, target_status, force=False):
    """Transition multiple issues to target status."""
    current_user_id = get_current_user(session)
    for key in keys:
        # Ownership check
        if current_user_id and not force:
            r_issue = session.get(f"{JIRA_URL}/rest/api/3/issue/{key}", params={"fields": "assignee"})
            if r_issue.status_code == 200:
                assignee = r_issue.json()["fields"].get("assignee")
                if assignee and assignee.get("accountId") != current_user_id:
                    print(f"  [SKIP] {key} — assigned to {assignee.get('displayName', '?')}, not you (use --force)")
                    continue
        r = session.get(f"{JIRA_URL}/rest/api/3/issue/{key}/transitions")
        transitions = r.json().get("transitions", [])
        tid = None
        for t in transitions:
            if t["to"]["name"].lower() == target_status.lower() or t["name"].lower() == target_status.lower():
                tid = t["id"]
                break
        if not tid:
            for t in transitions:
                if target_status.lower() in t["to"]["name"].lower():
                    tid = t["id"]
                    break
        if not tid:
            print(f"  [FAIL] No transition to '{target_status}' for {key}")
            continue
        r = session.post(f"{JIRA_URL}/rest/api/3/issue/{key}/transitions", json={"transition": {"id": tid}})
        status = "OK" if r.status_code in (200, 204) else f"FAIL ({r.status_code})"
        print(f"  [{status}] {key} -> {target_status}")


def bulk_assign(session, keys, account_id):
    """Assign multiple issues to a user."""
    for key in keys:
        r = session.put(f"{JIRA_URL}/rest/api/3/issue/{key}/assignee", json={"accountId": account_id})
        status = "OK" if r.status_code in (200, 204) else f"FAIL ({r.status_code})"
        print(f"  [{status}] {key} assigned")


def main():
    parser = argparse.ArgumentParser(description="Bulk Jira Operations", prog="bulk.py")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("comment", help="Add comment to multiple issues")
    p.add_argument("keys", help="Comma-separated issue keys")
    p.add_argument("text", help="Comment text")

    p = sub.add_parser("transition", help="Transition multiple issues")
    p.add_argument("keys", help="Comma-separated issue keys")
    p.add_argument("status", help="Target status")
    p.add_argument("--force", action="store_true", help="Override ownership check")

    p = sub.add_parser("assign", help="Assign multiple issues")
    p.add_argument("keys", help="Comma-separated issue keys")
    p.add_argument("--account-id", help="User account ID")
    p.add_argument("--search", help="Search user by name (picks first match)")

    args = parser.parse_args()
    session = get_session()
    keys = [k.strip().upper() for k in args.keys.split(",")]

    print(f"Bulk {args.command} on {len(keys)} issues:")

    if args.command == "comment":
        bulk_comment(session, keys, args.text)
    elif args.command == "transition":
        bulk_transition(session, keys, args.status, force=getattr(args, 'force', False))
    elif args.command == "assign":
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
        bulk_assign(session, keys, account_id)

    print("Done.")


if __name__ == "__main__":
    main()
