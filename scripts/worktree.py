#!/usr/bin/env python3
"""worktree.py — give each task branch its own git worktree (run as `ses worktree`).

Without it, two tasks in one repo share that repo's single checkout: the
second task analyses and branches from whatever the first has checked out,
and a resume of either reads the other's files as its own. A worktree per
task branch keeps them apart, and the repo's own checkout — the user's — is
never switched or touched.

Usage:
    worktree.py add    <ws> <repo-name> <branch> [--base <mainline>]
    worktree.py remove <ws> <repo-name>

add — checks <branch> out in <ws>/wt/<repo-name>. A new branch is cut from
  origin/<mainline> after a fetch — from local <mainline> only when the repo
  has no origin or the fetch fails, and it says so — never from whatever the
  repo has checked out. An existing branch is checked out as it is (a
  resume). Records in STATUS.md: branch.<repo-name>, base.<repo-name> (the
  ref the branch was cut from: every later diff and log compares against
  it) and worktree.<repo-name>. --base is required unless base.<repo-name>
  is already recorded — the mainline is the user's call, never a guess.
  Re-running for a worktree that already exists reuses it.
  A change-request workspace changes one repo: asking for a second exits 3
  (the escalation rule, /change-request §1).
remove — `git worktree remove` (git refuses while the worktree has
  uncommitted changes), keeps the branch, drops worktree.<repo-name>.

Exit codes: 0 ok, 1 error, 2 usage, 3 the user must decide (nothing changed).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checkpoint import all_repos, load  # noqa: E402
from status import StatusError  # noqa: E402

DECIDE = 3


def run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def ok(repo: Path, *args: str) -> str:
    r = run(repo, *args)
    if r.returncode != 0:
        raise StatusError(f"git {' '.join(args)} failed in {repo}: {r.stderr.strip()}")
    return r.stdout.strip()


def has_ref(repo: Path, ref: str) -> bool:
    return run(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode == 0


def common_dir(repo: Path) -> Path:
    """The repository's shared git dir — the same for a repo and each of its worktrees."""
    d = Path(ok(repo, "rev-parse", "--git-common-dir"))
    return (d if d.is_absolute() else repo / d).resolve()


def start_point(repo: Path, base: str) -> tuple[str, str]:
    """(ref to cut the branch from, note). origin/<base> after a fetch, else local <base>."""
    mainline = base[len("origin/"):] if base.startswith("origin/") else base
    if run(repo, "remote", "get-url", "origin").returncode != 0:
        note = f"no origin remote — cut from local {mainline}"
    else:
        f = run(repo, "fetch", "--quiet", "origin", mainline)
        if f.returncode == 0 and has_ref(repo, f"origin/{mainline}"):
            return f"origin/{mainline}", f"fetched origin {mainline}"
        note = (f"fetch of origin {mainline} failed ({f.stderr.strip() or 'no such branch'}) — "
                f"cut from local {mainline}, which may be stale")
    if not has_ref(repo, mainline):
        raise StatusError(f"mainline '{mainline}' not found in {repo} — ask the user which branch it releases from")
    return mainline, note


def cmd_add(ws_arg: str, name: str, branch: str, base_arg: str | None) -> int:
    ws, st = load(ws_arg)
    repos = all_repos(st)
    if name not in repos:
        raise StatusError(f"no repo named '{name}' among work-repo / repos-analyzed ({', '.join(sorted(repos))})")
    repo = repos[name]
    others = sorted(f[len("branch."):] for f in st.fields if f.startswith("branch.") and f != f"branch.{name}")
    if st.field("pipeline") == "change-request" and others:
        print(f"ASK THE USER — {st.field('task-id')} is a change request and already changes "
              f"{', '.join(others)}; a change request changes one repo. Landing in {name} as well is "
              f"/change-request §1's escalation rule: recommend the full pipeline. Nothing was changed.",
              file=sys.stderr)
        return DECIDE
    base = base_arg or (st.field(f"base.{name}") if f"base.{name}" in st.fields else None)
    if not base:
        raise StatusError(f"no --base given and no base.{name} recorded — ask the user which branch "
                          f"{name} releases from")
    path = ws / "wt" / name
    if path.exists():
        if run(path, "rev-parse", "--is-inside-work-tree").returncode != 0:
            raise StatusError(f"{path} exists and is not a git worktree — move it aside first")
        head = ok(path, "rev-parse", "--abbrev-ref", "HEAD")
        common = common_dir(path)
        mine = common_dir(repo)
        if common != mine or head != branch:
            raise StatusError(f"{path} is a worktree of {common.parent} on '{head}', not {name} on '{branch}'")
        note, start = "worktree already exists — reused", None
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        if has_ref(repo, f"refs/heads/{branch}"):
            start, note = None, f"branch {branch} exists — checked out as it is"
            r = run(repo, "worktree", "add", str(path), branch)
        else:
            start, note = start_point(repo, base)
            ok(repo, "branch", "--no-track", branch, start)
            r = run(repo, "worktree", "add", str(path), branch)
            if r.returncode != 0:
                run(repo, "branch", "-D", branch)   # leave nothing behind
        if r.returncode != 0:
            err = r.stderr.strip()
            if "already checked out" in err or "already used by worktree" in err:
                print(f"ASK THE USER — {name}: branch {branch} is checked out elsewhere ({err}). Switch that "
                      f"checkout to another branch — it may hold the user's own work, so they decide — "
                      f"then re-run. Nothing was changed.", file=sys.stderr)
                return DECIDE
            raise StatusError(f"git worktree add failed in {repo}: {err}")
    st.set_field(f"branch.{name}", branch)
    if start:                       # a new branch: the ref it was cut from
        st.set_field(f"base.{name}", start)
    elif base_arg:                  # an existing branch: the mainline the user named, as a ref
        st.set_field(f"base.{name}", start_point(repo, base_arg)[0])
    st.set_field(f"worktree.{name}", str(path))
    st.save()
    sha = ok(path, "rev-parse", "--short", "HEAD")
    print(f"{name}: {branch} at {sha} in {path} ({note}); base.{name} = {st.field(f'base.{name}')}")
    print(f"  edit, diff, stage, commit and test {name} there — the repo's own checkout is left as it is")
    return 0


def cmd_remove(ws_arg: str, name: str) -> int:
    _ws, st = load(ws_arg)
    f = f"worktree.{name}"
    if f not in st.fields:
        print(f"no worktree recorded for {name}")
        return 0
    path = Path(st.field(f))
    repos = all_repos(st)
    if path.exists():
        if name not in repos:
            raise StatusError(f"no repo named '{name}' among work-repo / repos-analyzed")
        r = run(repos[name], "worktree", "remove", str(path))
        if r.returncode != 0:
            raise StatusError(f"git worktree remove refused: {r.stderr.strip()} — commit or ask the user "
                              f"about its changes first (git -C {path} status)")
    st.unset_field(f)
    st.save()
    branch = st.field(f"branch.{name}") if f"branch.{name}" in st.fields else "?"
    print(f"{name}: worktree removed; branch {branch} kept")
    return 0


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    cmd, rest = argv[0], argv[1:]
    base = None
    if "--base" in rest:
        i = rest.index("--base")
        if i + 1 >= len(rest):
            print("error: --base needs a value", file=sys.stderr)
            return 2
        base = rest[i + 1]
        del rest[i:i + 2]
    if cmd == "add" and len(rest) == 3:
        return cmd_add(rest[0], rest[1], rest[2], base)
    if cmd == "remove" and len(rest) == 2 and base is None:
        return cmd_remove(rest[0], rest[1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except StatusError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
