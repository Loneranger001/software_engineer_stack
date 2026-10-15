#!/usr/bin/env python3
"""xsearch.py — search every repo in a task's analysis scope, counts first.

Cross-repo impact analysis fails silently: a repo nobody searched and a repo
with no callers both read as "no callers". This runs one search in EVERY repo,
records the exact command and commit searched per repo, and prints counts plus
the top files — so the agent opens only the hits that matter instead of
pulling every match into context.

Usage:
    xsearch.py [--ws <ws> | --repos a,b,...] [--ref <ref>] [-i] [-F]
               [--top N] [--save FILE] -- <pattern> [<pattern> ...]

    --ws     task workspace: repos come from STATUS.md repos-analyzed
    --repos  comma-separated repo paths instead of a workspace
    --ref    search this ref in each repo (e.g. origin/main) instead of the
             working tree; a repo lacking the ref is reported, not skipped
    -i / -F  case-insensitive / fixed-string patterns (default: extended regex)
    --top N  files listed per repo (default 15); totals always cover all files
    --save   write the complete per-file list (every repo, every file) to FILE,
             e.g. <ws>/evidence/research-search-<term>.txt

Output ends with Markdown rows for research-notes.md's "Cross-repo search
record": | repo | ref@sha | command | result |. A later stage may reuse a
recorded row while that repo's sha is unchanged; a repo whose sha moved is
re-searched.

Exit codes: 0 searched every repo (hits or not), 1 a repo could not be
searched, 2 usage error.
"""
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from status import Status, StatusError, resolve  # noqa: E402


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def search(repo: Path, patterns: list[str], ref: str | None, icase: bool, fixed: bool):
    """Return (ref_label, sha, command, {file: count}) or raise RuntimeError."""
    target = ref or "HEAD"
    sha = git(repo, "rev-parse", "--short", target)
    if sha.returncode != 0:
        raise RuntimeError(f"ref '{target}' not found (fetch it, or search the working tree)")
    args = ["grep", "-c", "-I"]
    args += ["-i"] if icase else []
    args += ["-F"] if fixed else ["-E"]
    for p in patterns:
        args += ["-e", p]
    if ref:
        args.append(ref)
    args.append("--")
    cmd = "git -C " + shlex.quote(str(repo)) + " " + " ".join(shlex.quote(a) for a in args)
    r = git(repo, *args)
    if r.returncode not in (0, 1):  # 1 = no match
        raise RuntimeError(r.stderr.strip() or f"git grep exited {r.returncode}")
    counts = {}
    for line in r.stdout.splitlines():
        path, _, n = line.rpartition(":")
        if ref and path.startswith(ref + ":"):
            path = path[len(ref) + 1:]
        if n.isdigit():
            counts[path] = int(n)
    label = ref or "worktree"
    return label, sha.stdout.strip(), cmd, counts


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], usage=__doc__.split("Usage:")[1].split("\n\n")[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--ws")
    src.add_argument("--repos")
    ap.add_argument("--ref")
    ap.add_argument("-i", action="store_true", dest="icase")
    ap.add_argument("-F", action="store_true", dest="fixed")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--save")
    ap.add_argument("patterns", nargs="+")
    a = ap.parse_args(argv)

    if a.ws:
        try:
            repos = [Path(p) for p in Status(resolve(a.ws)).repos_analyzed()]
        except StatusError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        if not repos:
            print("error: STATUS.md has no repos-analyzed", file=sys.stderr)
            return 2
    else:
        repos = [Path(p) for p in a.repos.split(",") if p]

    rows, full, failed = [], [], 0
    pat_label = " | ".join(a.patterns)
    print(f"search: {pat_label}   repos: {len(repos)}   ref: {a.ref or 'worktree'}")
    for repo in repos:
        name = repo.name
        try:
            label, sha, cmd, counts = search(repo, a.patterns, a.ref, a.icase, a.fixed)
        except RuntimeError as e:
            failed += 1
            print(f"\n## {name}: NOT SEARCHED — {e}")
            rows.append(f"| {name} | {a.ref or 'worktree'} | — | NOT SEARCHED: {e} |")
            full.append(f"## {name}: NOT SEARCHED — {e}")
            continue
        total, nfiles = sum(counts.values()), len(counts)
        ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        result = (f"{total} match(es) in {nfiles} file(s)" if counts
                  else "searched, no references found")
        print(f"\n## {name} ({label}@{sha}): {result}")
        print(f"   {cmd}")
        for path, n in ranked[:a.top]:
            print(f"   {n:5d}  {path}")
        if nfiles > a.top:
            print(f"   … {nfiles - a.top} more file(s)" + (f" — full list in {a.save}" if a.save else
                                                          " — rerun with --save to keep the full list"))
        rows.append(f"| {name} | {label}@{sha} | `{cmd}` | {result} |")
        full.append(f"## {name} ({label}@{sha}): {result}\n{cmd}")
        full += [f"{n:5d}  {path}" for path, n in ranked]

    print("\nCross-repo search record rows:")
    print("| Repo | Ref@sha | Search command | Result |")
    print("|---|---|---|---|")
    print("\n".join(rows))
    if a.save:
        Path(a.save).parent.mkdir(parents=True, exist_ok=True)
        Path(a.save).write_text(f"search: {pat_label}\n\n" + "\n".join(full) + "\n")
        print(f"\nfull per-file list: {a.save}")
    print("\nNext: open only the files that matter — `git -C <repo> grep -n -e <pattern> [<ref>] -- <path>`.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
