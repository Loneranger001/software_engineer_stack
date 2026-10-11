#!/usr/bin/env python3
"""checkpoint.py — crash safety for /implement and /change-request.

Usage:
    checkpoint.py resume  <ws>            is it safe to continue from the recorded state?
    checkpoint.py trailer <ws> <file>...  Evidence-SHA256 lines for a checkpoint commit
    checkpoint.py verify  <ws>            do the recorded evidence hashes still match?

<ws> is the task workspace (work/<task-id>). Changed repos and their branches
come from STATUS.md `branch.<repo-name>` fields; a repo name resolves to the
STATUS work-repo or "Repos analyzed" path with that basename.

resume — per changed repo: recorded vs checked-out branch, the last
  `<task-id> step <N>` checkpoint commit, STATUS `current-step`, and every
  uncommitted file classified against the NEXT step's file list from
  impl-doc.md §2 ("expected" = that step's own files, i.e. a half-done step;
  "unexpected" = anything else). It decides nothing: it shows the facts the
  user needs to choose keep-and-continue or discard-and-redo.
  Exit 0 = clean (resume at the next step); 3 = needs a decision.

trailer — prints one `Evidence-SHA256: <sha256> <path>` line per file, path
  relative to <ws>. Add them as the last paragraph of the checkpoint commit
  message, so the hash of the step's evidence lives in git even though work/
  may live outside any repository.

verify — reads every Evidence-SHA256 line on each recorded task branch and
  re-hashes the file. Exit 1 if any recorded evidence is missing or altered.
  Evidence files with no recorded hash are listed as a warning, not a failure.
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from status import Status, StatusError, resolve  # noqa: E402

TRAILER_RE = re.compile(r"^Evidence-SHA256:\s*([0-9a-f]{64})\s+(\S.*?)\s*$", re.M)
NEEDS_DECISION = 3


def git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise StatusError(f"git {' '.join(args)} failed in {repo}: {r.stderr.strip()}")
    return r.stdout


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load(ws: str) -> tuple[Path, Status]:
    st = Status(resolve(ws))
    return Path(st.path).parent, st


def changed_repos(st: Status) -> dict[str, tuple[Path, str]]:
    """{repo-name: (path, recorded branch)} from branch.<repo-name> fields."""
    candidates = [Path(p) for p in st.repos_analyzed()]
    if "work-repo" in st.fields:
        candidates.append(Path(st.field("work-repo")))
    by_name = {p.name: p for p in candidates}
    out = {}
    for f in st.fields:
        if not f.startswith("branch."):
            continue
        name = f[len("branch."):]
        if name not in by_name:
            raise StatusError(f"STATUS {f}: no repo named '{name}' among work-repo / Repos analyzed")
        out[name] = (by_name[name], st.field(f))
    return out


def impl_steps(ws: Path) -> dict[int, tuple[str, list[str]]]:
    """{step number: (repo, [file tokens])} from impl-doc.md §2's table."""
    doc = ws / "impl-doc.md"
    if not doc.is_file():
        return {}
    text = doc.read_text()
    m = re.search(r"^##+ [^\n]*Implementation steps[^\n]*\n(.*?)(?=^## |\Z)", text, re.S | re.M | re.I)
    steps = {}
    for line in (m.group(1) if m else "").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and cells[0].isdigit():
            tokens = [t.strip("`{}()") for t in re.split(r"[,;\s]+", cells[3])]
            steps[int(cells[0])] = (cells[1].strip("`{}"),
                                    [t for t in tokens if t and ("/" in t or "." in t)])
    return steps


def belongs(path: str, tokens: list[str]) -> bool:
    for t in tokens:
        t = t.rstrip("/")
        if path == t or path.endswith("/" + t) or path.startswith(t + "/"):
            return True
    return False


def dirty_files(repo: Path, ignore_prefix: str | None) -> list[str]:
    out = []
    for line in git(repo, "status", "--porcelain=v1", "-uall").splitlines():
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = path.strip('"')
        if ignore_prefix and (path == ignore_prefix or path.startswith(ignore_prefix + "/")):
            continue
        out.append(path)
    return out


def cmd_resume(ws_arg: str) -> int:
    ws, st = load(ws_arg)
    repos = changed_repos(st)
    if not repos:
        print("no branch.<repo> recorded — first run: start at branch setup (§1)")
        return 0
    task = st.field("task-id")
    step_re = re.compile(rf"\b{re.escape(task)} step (\d+)\b")
    steps = impl_steps(ws)
    last = 0
    problems, report = [], []
    for name, (repo, branch) in sorted(repos.items()):
        head = git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip()
        subjects = git(repo, "log", "--format=%s", branch).splitlines()
        done = [int(m.group(1)) for s in subjects for m in [step_re.search(s)] if m]
        repo_last = max(done) if done else 0
        last = max(last, repo_last)
        report.append((name, repo, branch, head, repo_last))
        if head != branch:
            problems.append(f"{name}: checked out '{head}', STATUS records '{branch}' — switch or re-record")
    nxt = last + 1
    recorded = st.field("current-step") if "current-step" in st.fields else None
    print(f"task {task}: last checkpoint commit is step {last or '(none)'}; "
          f"STATUS current-step: {recorded or '(unset)'}")
    if recorded is not None and recorded != str(last):
        problems.append(f"STATUS current-step is {recorded} but the commits end at step {last} — "
                        f"trust the commits and re-record (status.py field <ws> current-step {last})")
    nxt_repo, nxt_tokens = steps.get(nxt, ("", []))
    if not steps:
        print("no impl-doc.md steps (change-request pipeline?) — uncommitted files are listed as-is")
    else:
        print(f"next step: {nxt}" + (f" ({nxt_repo}: {', '.join(nxt_tokens) or 'files not parsed'})"
                                      if nxt in steps else " (not in impl-doc §2 — all steps done?)"))
    for name, repo, branch, head, repo_last in report:
        rel_ws = os.path.relpath(ws, repo)
        dirty = dirty_files(repo, None if rel_ws.startswith("..") else Path(rel_ws).parts[0])
        expected = [d for d in dirty if name == nxt_repo and belongs(d, nxt_tokens)]
        unexpected = [d for d in dirty if d not in expected]
        print(f"- {name} ({repo}) branch {head}, last step here {repo_last or '-'}: "
              f"{len(dirty)} uncommitted file(s)")
        for d in expected:
            print(f"    expected   {d}   (step {nxt}'s file — likely its half-done work)")
        for d in unexpected:
            if steps:
                print(f"    UNEXPECTED {d}   (not in step {nxt}'s file list)")
            else:
                print(f"    uncommitted {d}")
        if dirty:
            what = f"finish step {nxt}" if steps else "finish the change"
            problems.append(f"{name}: {len(dirty)} uncommitted file(s) — show them "
                            f"(git -C {repo} status; git -C {repo} diff; untracked files' "
                            f"contents) and ask: keep and {what}, or discard and redo it")
    if problems:
        print("NEEDS DECISION:")
        for p in problems:
            print(f"  - {p}")
        return NEEDS_DECISION
    print(f"CLEAN — resume at step {nxt}")
    return 0


def cmd_trailer(ws_arg: str, files: list[str]) -> int:
    ws, _ = load(ws_arg)
    if not files:
        raise StatusError("trailer needs at least one evidence file")
    for f in files:
        p = Path(f) if os.path.isabs(f) else (Path.cwd() / f)
        if not p.is_file():
            p = ws / f
        if not p.is_file():
            raise StatusError(f"no such evidence file: {f}")
        rel = os.path.relpath(p.resolve(), ws.resolve())
        if rel.startswith(".."):
            raise StatusError(f"{f} is outside the workspace {ws}")
        print(f"Evidence-SHA256: {sha256(p)} {rel}")
    return 0


def cmd_verify(ws_arg: str) -> int:
    ws, st = load(ws_arg)
    repos = changed_repos(st)
    if not repos:
        print("no task branches recorded (e.g. a document task) — no checkpoint evidence to verify")
        return 0
    recorded: dict[str, str] = {}
    for name, (repo, branch) in sorted(repos.items()):
        for digest, rel in TRAILER_RE.findall(git(repo, "log", "--format=%B", branch)):
            recorded.setdefault(rel, digest)  # newest commit first: its hash wins
    bad = []
    for rel, digest in sorted(recorded.items()):
        p = ws / rel
        if not p.is_file():
            bad.append(f"MISSING  {rel} (hash recorded in a checkpoint commit)")
        elif sha256(p) != digest:
            bad.append(f"ALTERED  {rel} (content no longer matches its recorded hash)")
    ev = ws / "evidence"
    unrecorded = sorted(str(p.relative_to(ws)) for p in ev.rglob("*")
                        if p.is_file() and str(p.relative_to(ws)) not in recorded) if ev.is_dir() else []
    print(f"{len(recorded)} recorded evidence file(s), {len(bad)} problem(s)")
    for b in bad:
        print(f"  {b}")
    if unrecorded:
        print(f"warning: {len(unrecorded)} evidence file(s) with no recorded hash "
              f"(fine for research/test-plan evidence; a step's evidence should be recorded):")
        for u in unrecorded[:20]:
            print(f"  {u}")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] not in ("resume", "trailer", "verify"):
        print(__doc__)
        return 1
    cmd, ws, rest = argv[0], argv[1], argv[2:]
    if cmd == "resume":
        return cmd_resume(ws)
    if cmd == "trailer":
        return cmd_trailer(ws, rest)
    return cmd_verify(ws)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except StatusError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
