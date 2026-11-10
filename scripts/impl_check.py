#!/usr/bin/env python3
"""impl_check.py — is the implementation document complete enough to execute? (run as `ses impl-check`)

/implement touches only the files a step names, so a test file the plan runs
but no step creates, or a rollback script nobody writes, surfaces mid-task as
an impl-doc amendment — or not at all. This checks the plan before approval:

  FILES        every repo path that §3 "How run", §4 Deployment, §5 Rollback
               or a §2 Rollback cell names is in some §2 "Files" cell, or
               already exists in a repo of the task at its base (mainline)
  VERIFY       every §2 step has its own Verify and Rollback cell (not empty, not "—")
  REPO         every §2 step names a repo of the task (work-repo or repos-analyzed)
  PLAN         every TDD §7 row, contract A# and approved FDD TS# has a §3 T#
               (ses coverage --plan)
  WORKSPACE    (warning) a test run from the task workspace (<ws>/…, evidence/…):
               that tooling is versioned nowhere and hashed nowhere

Usage:
    impl_check.py <ws>

Exit codes: 0 complete, 3 problems found (fix the impl doc before approval),
1 error (no impl-doc.md), 2 usage.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checkpoint import all_repos, load, mainline  # noqa: E402
from coverage import impl_tests, tdd_rows  # noqa: E402
from doctables import col, rows_missing_from_tdd, section, strip_comments, tables  # noqa: E402
from status import StatusError  # noqa: E402

NOT_MET = 3
EXT = r"(?:sql|pks|pkb|pls|plb|trg|ksh|sh|py|ctl|dat|txt|csv|json|ya?ml|toml|cfg|ini|xml|md)"
PATH_RE = re.compile(rf"(?<![\w$<{{])@?((?:[\w.-]+/)*[\w.-]+\.{EXT})\b")
WS_PATH = re.compile(r"(<ws>/|(?<![\w/])evidence/)[\w./<>-]+")
NONE = {"", "-", "—", "–", "n/a", "none"}


def paths_in(text: str) -> list[str]:
    """Repo-relative file paths named in text (sqlplus @file included); workspace paths excluded."""
    text = WS_PATH.sub(" ", text)
    out = []
    for m in PATH_RE.finditer(text):
        p = m.group(1).lstrip("@").removeprefix("./")
        if "://" in p or p in out:
            continue
        out.append(p)
    return out


def same_file(named: str, path: str) -> bool:
    """A named path matches a repo path when one is the other's tail: commands often run from a
    subdirectory (`cd deploy && sqlplus @run_tests.sql`) or name a fixture by its file name."""
    named, path = named.strip("/"), path.strip("/")
    return named == path or path.endswith("/" + named) or named.endswith("/" + path)


def repo_files(repos: dict[str, Path], st) -> list[str]:
    """Every tracked path at each repo's base (base.<repo>, else origin/<mainline>, else HEAD)."""
    out: list[str] = []
    for name, repo in repos.items():
        refs = [st.field(f"base.{name}")] if f"base.{name}" in st.fields else []
        refs += [f"origin/{mainline(st, name)}"] if mainline(st, name) else []
        for ref in refs + ["HEAD"]:
            r = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "--name-only", ref],
                               capture_output=True, text=True)
            if r.returncode == 0:
                out += r.stdout.splitlines()
                break
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv and argv[0] in ("-h", "--help") else 2
    ws, st = load(argv[0])
    doc = ws / "impl-doc.md"
    if not doc.is_file():
        raise StatusError(f"no impl-doc.md in {ws}")
    text = strip_comments(doc.read_text())
    repos = {n: p for n, p in all_repos(st).items()}
    problems, warnings = [], []

    steps_body = section(text, re.compile(r"implementation steps", re.I))
    files: list[str] = []
    rollback_text = []
    for header, rows in tables(steps_body)[:1]:
        c_repo, c_files = col(header, "repo"), col(header, "files")
        c_verify, c_rb = col(header, "verify"), col(header, "rollback")
        for r in rows:
            if not r or not r[0].strip().isdigit():
                continue
            n = r[0].strip()
            cell = lambda i: r[i].strip() if i is not None and i < len(r) else ""   # noqa: E731
            if c_repo is not None and cell(c_repo).strip("`{}") not in repos:
                problems.append(f"REPO      step {n}: '{cell(c_repo)}' is not a repo of this task "
                                f"({', '.join(sorted(repos))})")
            for name, c in (("Verify", c_verify), ("Rollback", c_rb)):
                if c is not None and cell(c).lower() in NONE:
                    problems.append(f"VERIFY    step {n}: no {name} of its own — every step is verified and "
                                    f"rolled back on its own")
            if c_files is not None:
                files += [t.strip("`{}()") for t in re.split(r"[,;\s]+", cell(c_files))
                          if t.strip("`{}()") and ("/" in t or "." in t)]
            if c_rb is not None:
                rollback_text.append(cell(c_rb))

    named = []
    plan_body = section(text, re.compile(r"test plan", re.I))
    for header, rows in tables(plan_body):
        c_how, c_t = col(header, "howrun"), col(header, "t#")
        if c_how is None:
            continue
        for r in rows:
            how = r[c_how] if c_how < len(r) else ""
            tid = r[c_t] if c_t is not None and c_t < len(r) else "?"
            if WS_PATH.search(how):
                warnings.append(f"WORKSPACE {tid}: runs tooling from the task workspace ({how.strip()}) — "
                                f"it is versioned and hashed nowhere; put the test in the repo")
            named += [(f"§3 {tid}", p) for p in paths_in(how)]
    named += [("§4", p) for p in paths_in(section(text, re.compile(r"deployment", re.I)))]
    named += [("§5", p) for p in paths_in(section(text, re.compile(r"rollback", re.I)))]
    named += [("§2 Rollback", p) for t in rollback_text for p in paths_in(t)]
    seen = set()
    tracked = repo_files(repos, st)
    for where, p in named:
        if (where, p) in seen:
            continue
        seen.add((where, p))
        if any(same_file(p, f) for f in files) or any(same_file(p, f) for f in tracked):
            continue
        problems.append(f"FILES     {where} names {p}, which no §2 step creates and no repo has — add it "
                        f"to the step that writes it")

    try:
        rows = tdd_rows(ws)
    except StatusError:
        rows = []
    missing = rows_missing_from_tdd(ws)
    tests = impl_tests(ws)
    for rid in rows:
        if rid not in tests:
            problems.append(f"PLAN      {rid}: no §3 T# covers it")
    for rid, src in missing:
        problems.append(f"PLAN      {rid} ({src}): no TDD §7 row, so no test plans it")

    for w in warnings:
        print(f"warning: {w}")
    if problems:
        print(f"impl-check {st.field('task-id')}: {len(problems)} problem(s)")
        for p in problems:
            print(f"  {p}")
        return NOT_MET
    print(f"impl-check {st.field('task-id')}: ok — {len(files)} file(s) in §2, {len(named)} path(s) "
          f"referenced, {len(rows)} §7 row(s) planned")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except StatusError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
