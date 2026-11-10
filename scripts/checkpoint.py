#!/usr/bin/env python3
"""checkpoint.py — crash safety for /implement and /change-request (run as `ses checkpoint`).

Usage:
    checkpoint.py resume  <ws>               is it safe to continue from the recorded state?
    checkpoint.py subject <ws> <repo-name> <N | tests> <description>
                                             a checkpoint subject the repo's commit-msg hook accepts
    checkpoint.py trailer <ws> [--prefix <p>] <file>...
                                             Evidence-SHA256 lines for a checkpoint commit
    checkpoint.py seal    <ws> [<file>...]   hash the design-phase evidence the documents cite
    checkpoint.py verify  <ws> [--delivery]  do the recorded evidence hashes still match?

<ws> is the task workspace (work/<task-id>). Changed repos and their branches
come from STATUS.md `branch.<repo-name>` fields; a repo name resolves to the
STATUS work-repo or repos-analyzed path with that basename. A repo with a
`worktree.<repo-name>` field (made by `ses worktree add`) is checked out
there: resume and trailer look at that worktree, not the repo's own checkout.

subject — prints the first checkpoint subject that the repo's own commit-msg
  hook accepts (core.hooksPath honoured; the task worktree is the cwd), trying
  `<T> step <N>: <d>`, `<T>: step <N>: <d>`, `<T>: <T> step <N>: <d>` — or the
  same with `tests:` for the test-plan commit. Every form is one `resume`
  parses (`<T>[:] step <N>`). No hook → the first form. Exit 3 when the hook
  rejects all three: ask the user how checkpoint commits may be written.

resume — per changed repo: recorded vs checked-out branch, the last
  `<task-id> step <N>` checkpoint commit (the commits are the step record —
  nothing else stores it), and every uncommitted file classified against the
  NEXT step's file list from
  impl-doc.md §2 ("expected" = that step's own files, i.e. a half-done step;
  "unexpected" = anything else). It decides nothing: it shows the facts the
  user needs to choose keep-and-continue or discard-and-redo.
  A checkout on another task's recorded branch is named as such — two tasks
  sharing one checkout is the case `ses worktree add` exists to prevent.
  Verification by-products are not "uncommitted work" and are left out,
  counted: __pycache__/, *.pyc, .pytest_cache/, .ruff_cache/, .mypy_cache/.
  SES_RESUME_IGNORE (space-separated globs) replaces that list.
  Exit 0 = clean (resume at the next step); 3 = needs a decision.

trailer — `trailer <ws> [--prefix <p>] [<file>...]`: with --prefix, every
  file in evidence/ and evidence/raw/ whose name starts with <p> (e.g.
  step4-) joins the files named, so no raw log of the step is left out.
  Prints one `Evidence-SHA256: <sha256> <path>` line per file, path
  relative to <ws>. Add them as the last paragraph of the checkpoint commit
  message, so the hash of the step's evidence lives in git even though work/
  stays out of every repository. Refuses (exit 1) while any file under work/
  is staged in a recorded repo: workspaces never go into git.

seal — design-phase evidence (research probes, grill probes) is what the
  TDD cites as its source of truth, long before any checkpoint commit. seal
  hashes it into evidence/SEALED.sha256: the files named, or — with none —
  every evidence/ file that research-notes.md, fdd.md, tdd.md or
  grill-log.md cites (`evidence/<name>`; a name without extension matches
  evidence/<name>.* and evidence/raw/<name>.*). STATUS records the seal's own
  hash (evidence-seal), and the first checkpoint commit's trailer carries
  evidence/SEALED.sha256, so the seal itself ends up in git. A file already
  sealed with another hash is ALTERED: seal refuses it (exit 1).

verify — reads every Evidence-SHA256 line in this task's commits (subject
  carries the task id) on each recorded task branch and re-hashes the file.
  Commits of other tasks — already on mainline, and so in the branch's
  history — are not this workspace's evidence and are ignored. Exit 1 if:
  - any recorded evidence is missing or altered;
  - any file under work/ is committed on a task branch (it would be pushed);
  - any analyzed repo WITHOUT a recorded branch holds a commit of this task
    (on any ref) — a write outside the changed repos, or a branch never
    recorded;
  - a change-request workspace records branches in more than one repo (a
    change request changes one repo; more is the escalation rule).
  --delivery (before anything is pushed: /deliver's scope audit,
  /change-request §5) also fails when a recorded branch holds no commit of
  this task, or a task commit carries no Evidence-SHA256 line — nothing is
  delivered without the evidence that proves it. Evidence files with no
  recorded hash are a warning, not a failure.
"""
from __future__ import annotations

import fnmatch
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from status import Status, StatusError, resolve  # noqa: E402

TRAILER_RE = re.compile(r"^Evidence-SHA256:\s*([0-9a-f]{64})\s+(\S.*?)\s*$", re.M)
NEEDS_DECISION = 3


def step_pattern(task: str) -> re.Pattern[str]:
    """`<task> step <N>`, also as `<task>: step <N>` — the form a `KEY-N: text` commit-msg hook allows."""
    return re.compile(rf"(?<![\w-]){re.escape(task)}:?\s+step\s+(\d+)\b")


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


def all_repos(st: Status) -> dict[str, Path]:
    """{repo-name: path} for the work-repo and every repo in repos-analyzed."""
    candidates = [Path(p) for p in st.repos_analyzed()]
    if "work-repo" in st.fields:
        candidates.append(Path(st.field("work-repo")))
    return {p.name: p for p in candidates}


def detect_mainline(repo: Path) -> str | None:
    """The branch origin/HEAD points to; else origin's only one of main/master; else None (ask the user)."""
    r = subprocess.run(["git", "-C", str(repo), "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
                       capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip().startswith("origin/"):
        return r.stdout.strip()[len("origin/"):]
    have = [b for b in ("main", "master")
            if subprocess.run(["git", "-C", str(repo), "show-ref", "--verify", "--quiet", f"refs/remotes/origin/{b}"],
                              capture_output=True).returncode == 0]
    return have[0] if len(have) == 1 else None


def mainline(st: Status, name: str) -> str | None:
    """The mainline recorded for repo <name> (STATUS mainline.<name>), or None."""
    f = f"mainline.{name}"
    return st.field(f) if f in st.fields else None


def checkout(st: Status, name: str, repo: Path) -> Path:
    """Where the task branch of <name> is checked out: its recorded worktree, else the repo."""
    f = f"worktree.{name}"
    return Path(st.field(f)) if f in st.fields else repo


def changed_repos(st: Status) -> dict[str, tuple[Path, str]]:
    """{repo-name: (path, recorded branch)} from branch.<repo-name> fields."""
    by_name = all_repos(st)
    out = {}
    for f in st.fields:
        if not f.startswith("branch."):
            continue
        name = f[len("branch."):]
        if name not in by_name:
            raise StatusError(f"STATUS {f}: no repo named '{name}' among work-repo / repos-analyzed")
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


BYPRODUCTS = ("__pycache__", "*.pyc", ".pytest_cache", ".ruff_cache", ".mypy_cache")


def byproduct(path: str) -> bool:
    """A file a verification run leaves behind (bytecode, tool caches) — never the user's work."""
    pats = os.environ["SES_RESUME_IGNORE"].split() if os.environ.get("SES_RESUME_IGNORE") else BYPRODUCTS
    parts = path.split("/")
    return any(fnmatch.fnmatch(part, pat) for part in parts for pat in pats)


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
    step_re = step_pattern(task)
    steps = impl_steps(ws)
    others = other_tasks_branches(ws, st)
    last = 0
    problems, report = [], []
    for name, (repo, branch) in sorted(repos.items()):
        co = checkout(st, name, repo)
        if not co.is_dir():
            problems.append(f"{name}: recorded worktree {co} is missing — recreate it "
                            f"(ses worktree add <ws> {name} {branch})")
            continue
        head = git(co, "rev-parse", "--abbrev-ref", "HEAD").strip()
        subjects = git(repo, "log", "--format=%s", branch).splitlines()
        done = [int(m.group(1)) for s in subjects for m in [step_re.search(s)] if m]
        repo_last = max(done) if done else 0
        last = max(last, repo_last)
        report.append((name, co, branch, head, repo_last))
        if head != branch:
            owner = others.get((str(repo.resolve()), head))
            if owner:
                problems.append(f"{name}: {co} has '{head}' checked out — that is task {owner}'s branch, "
                                f"so the files there are {owner}'s, not this task's. Two tasks share this "
                                f"checkout: give each its own (ses worktree add); never re-record or "
                                f"discard on this report")
            else:
                problems.append(f"{name}: checked out '{head}', STATUS records '{branch}' — switch "
                                f"{co} back to '{branch}'; re-record only if this task really moved branch")
    nxt = last + 1
    print(f"task {task}: last checkpoint commit is step {last or '(none)'}")
    nxt_repo, nxt_tokens = steps.get(nxt, ("", []))
    if not steps:
        print("no impl-doc.md steps (change-request pipeline?) — uncommitted files are listed as-is")
    else:
        print(f"next step: {nxt}" + (f" ({nxt_repo}: {', '.join(nxt_tokens) or 'files not parsed'})"
                                      if nxt in steps else " (not in impl-doc §2 — all steps done?)"))
    all_done = bool(steps) and nxt not in steps
    for name, co, branch, head, repo_last in report:
        rel_ws = os.path.relpath(ws, co)
        dirty = dirty_files(co, None if rel_ws.startswith("..") else Path(rel_ws).parts[0])
        ignored = [d for d in dirty if byproduct(d)]
        dirty = [d for d in dirty if d not in ignored]
        expected = [d for d in dirty if name == nxt_repo and belongs(d, nxt_tokens)]
        unexpected = [d for d in dirty if d not in expected]
        print(f"- {name} ({co}) branch {head}, last step here {repo_last or '-'}: "
              f"{len(dirty)} uncommitted file(s)"
              + (f" ({len(ignored)} verification by-product(s) ignored)" if ignored else ""))
        for d in expected:
            print(f"    expected   {d}   (step {nxt}'s file — likely its half-done work)")
        for d in unexpected:
            if steps:
                print(f"    UNEXPECTED {d}   (not in step {nxt}'s file list)")
            else:
                print(f"    uncommitted {d}")
        show = f"show them (git -C {co} status; git -C {co} diff; untracked files' contents)"
        if expected:
            problems.append(f"{name}: {len(expected)} file(s) of step {nxt} uncommitted — {show} "
                            f"and ask: keep and finish step {nxt}, or discard and redo it")
        if unexpected and steps:
            where = ("every impl-doc step is committed" if all_done
                     else f"step {nxt} is in {nxt_repo or '?'}")
            problems.append(f"{name}: {len(unexpected)} file(s) no step accounts for ({where}) — {show} "
                            f"and ask whose they are; never fold them into a step's commit or discard them unasked")
        elif unexpected:
            problems.append(f"{name}: {len(unexpected)} uncommitted file(s) — {show} "
                            f"and ask: keep and finish the change, or discard and redo it")
    if problems:
        print("NEEDS DECISION:")
        for p in problems:
            print(f"  - {p}")
        return NEEDS_DECISION
    if all_done:
        print("CLEAN — every impl-doc step is committed; continue at the test plan (/implement §3)")
    else:
        print(f"CLEAN — resume at step {nxt}")
    return 0


def other_tasks_branches(ws: Path, st: Status) -> dict[tuple[str, str], str]:
    """{(repo path, branch): task-id} recorded by the OTHER workspaces beside this one."""
    out: dict[tuple[str, str], str] = {}
    me = st.field("task-id")
    for status in ws.parent.glob("*/STATUS.md"):
        if status.parent.resolve() == ws.resolve():
            continue
        try:
            other = Status(str(status))
            task = other.field("task-id")
        except StatusError:
            continue
        if task == me:
            continue
        repos = all_repos(other)
        for f in other.fields:
            if f.startswith("branch.") and f[len("branch."):] in repos:
                out[(str(repos[f[len("branch."):]].resolve()), other.field(f))] = task
    return out


def work_prefix(ws: Path, repo: Path) -> str | None:
    """work/ relative to repo when the workspaces folder sits inside it, else None."""
    rel = os.path.relpath(ws.resolve().parent, repo.resolve())
    return None if rel.startswith("..") else rel.replace(os.sep, "/")


def under(path: str, prefix: str) -> bool:
    return prefix == "." or path == prefix or path.startswith(prefix + "/")


def cmd_trailer(ws_arg: str, files: list[str]) -> int:
    ws, st = load(ws_arg)
    if "--prefix" in files:
        i = files.index("--prefix")
        if i + 1 >= len(files) or not files[i + 1].strip():
            raise StatusError("--prefix needs a value, e.g. --prefix step4-")
        prefix = files[i + 1]
        files = files[:i] + files[i + 2:]
        found = sorted(str(p.relative_to(ws)) for d in (ws / "evidence", ws / "evidence" / "raw") if d.is_dir()
                       for p in d.iterdir() if p.is_file() and p.name.startswith(prefix))
        if not found:
            raise StatusError(f"no evidence file starts with '{prefix}' in evidence/ or evidence/raw/")
        files += [f for f in found if f not in files]
    if not files:
        raise StatusError("trailer needs at least one evidence file")
    for name, (repo, _) in sorted(changed_repos(st).items()):
        prefix = work_prefix(ws, repo)
        if prefix is None:
            continue
        co = checkout(st, name, repo)   # the commit happens where the branch is checked out
        if not co.is_dir():
            continue
        staged = [p for p in git(co, "diff", "--cached", "--name-only").splitlines() if under(p, prefix)]
        if staged:
            raise StatusError(f"{name}: workspace files are staged — unstage them "
                              f"(git -C {co} restore --staged {prefix}) and stage only the step's own "
                              f"files; work/ never goes into git: {', '.join(staged[:5])}")
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


def commit_msg_hook(co: Path) -> Path | None:
    """The commit-msg hook git would run in checkout co (core.hooksPath honoured), if executable."""
    rel = git(co, "rev-parse", "--git-path", "hooks/commit-msg").strip()
    hook = Path(rel) if os.path.isabs(rel) else co / rel
    return hook if hook.is_file() and os.access(hook, os.X_OK) else None


def cmd_subject(ws_arg: str, name: str, step: str, desc: str) -> int:
    ws, st = load(ws_arg)
    repos = all_repos(st)
    if name not in repos:
        raise StatusError(f"no repo named '{name}' among work-repo / repos-analyzed ({', '.join(sorted(repos))})")
    if not (step.isdigit() or step == "tests"):
        raise StatusError("the step is a number, or `tests` for the test-plan commit")
    task = st.field("task-id")
    co = checkout(st, name, repos[name])
    kind = f"step {step}:" if step.isdigit() else "tests:"
    forms = [f"{task} {kind} {desc}", f"{task}: {kind} {desc}", f"{task}: {task} {kind} {desc}"]
    hook = commit_msg_hook(co)
    if hook is None:
        precommit = co / ".pre-commit-config.yaml"
        if precommit.is_file() and "commit-msg" in precommit.read_text():
            print(f"warning: {name}: .pre-commit-config.yaml has a commit-msg stage that is not installed "
                  f"as a hook here — check the subject against it by hand", file=sys.stderr)
        print(forms[0])
        return 0
    tried = []
    for form in forms:
        with tempfile.NamedTemporaryFile("w", suffix=".msg", delete=False) as f:
            f.write(form + "\n")
        try:
            r = subprocess.run([str(hook), f.name], cwd=co, capture_output=True, text=True)
        finally:
            os.unlink(f.name)
        if r.returncode == 0:
            print(form)
            return 0
        tried.append(f"  {form!r}: {(r.stderr or r.stdout).strip() or f'exit {r.returncode}'}")
    print(f"ASK THE USER — {name}: its commit-msg hook ({hook}) rejects every checkpoint subject "
          f"`ses checkpoint resume` can read:", file=sys.stderr)
    print("\n".join(tried), file=sys.stderr)
    return NEEDS_DECISION


SEAL = "evidence/SEALED.sha256"
SEAL_LINE = re.compile(r"^([0-9a-f]{64})  (\S+)  sealed (\S+)$")
CITE = re.compile(r"(?<![\w/])evidence/([\w.-]+(?:/[\w.-]+)*)")


def sealed(ws: Path) -> dict[str, str]:
    """{path relative to ws: sha256} from evidence/SEALED.sha256."""
    f = ws / SEAL
    out: dict[str, str] = {}
    if f.is_file():
        for line in f.read_text().splitlines():
            m = SEAL_LINE.match(line)
            if m:
                out[m.group(2)] = m.group(1)
    return out


def cited_evidence(ws: Path) -> list[str]:
    """evidence/ files the stage documents cite, resolved to the files on disk."""
    out: list[str] = []
    for doc in ("research-notes.md", "fdd.md", "tdd.md", "grill-log.md"):
        p = ws / doc
        if not p.is_file():
            continue
        for ref in CITE.findall(p.read_text()):
            ref = ref.rstrip(".")
            cands = [ws / "evidence" / ref] if (ws / "evidence" / ref).is_file() else \
                [q for d in (ws / "evidence", ws / "evidence" / "raw") if d.is_dir()
                 for q in d.glob(f"{Path(ref).name}*") if q.is_file()]
            for q in cands:
                rel = str(q.relative_to(ws))
                if rel != SEAL and rel not in out:
                    out.append(rel)
    return sorted(out)


def cmd_seal(ws_arg: str, files: list[str]) -> int:
    ws, st = load(ws_arg)
    targets = [str((Path(f) if os.path.isabs(f) else ws / f).resolve().relative_to(ws.resolve()))
               for f in files] if files else cited_evidence(ws)
    if not targets:
        print("nothing to seal: no evidence/ file named, and none cited by the stage documents")
        return 0
    have = sealed(ws)
    today = date.today().isoformat()
    added, problems = [], []
    for rel in targets:
        p = ws / rel
        if not p.is_file():
            problems.append(f"MISSING  {rel}")
            continue
        digest = sha256(p)
        if rel in have:
            if have[rel] != digest:
                problems.append(f"ALTERED  {rel} (sealed with another hash — the evidence changed after it was cited)")
            continue
        added.append(f"{digest}  {rel}  sealed {today}")
    if problems:
        for b in problems:
            print(f"  {b}")
        raise StatusError(f"{len(problems)} evidence file(s) cannot be sealed")
    seal = ws / SEAL
    seal.parent.mkdir(parents=True, exist_ok=True)
    with open(seal, "a") as f:
        for line in added:
            f.write(line + "\n")
    st.set_field("evidence-seal", f"{sha256(seal)} ({len(sealed(ws))} file(s), {today})")
    st.save()
    print(f"sealed {len(added)} new file(s) ({len(sealed(ws))} in {SEAL}); put {SEAL} in the next "
          f"checkpoint trailer so the seal itself is in git")
    return 0


def task_token(task: str) -> re.Pattern[str]:
    """The task id as a whole token: T-1 matches "T-1 step 2" but not "T-12" or "T-1-hotfix"."""
    return re.compile(rf"(?<![\w-]){re.escape(task)}(?![\w-])")


def task_commits(repo: Path, ref_args: list[str], own: re.Pattern[str]) -> list[tuple[str, str, str]]:
    """[(sha, subject, message)] of this task's commits (subject carries the task id), newest first."""
    out = []
    for entry in git(repo, "log", "--format=%x1e%H%n%s%n%B", *ref_args).split("\x1e")[1:]:
        sha, _, rest = entry.partition("\n")
        subject, _, message = rest.partition("\n")
        if own.search(subject):
            out.append((sha, subject, message))
    return out


def recorded_evidence(ws: Path, st: Status) -> dict[str, str]:
    """{evidence path relative to ws: sha256} from this task's commits on its recorded branches."""
    own = task_token(st.field("task-id"))
    recorded: dict[str, str] = {}
    for _name, (repo, branch) in sorted(changed_repos(st).items()):
        for _sha, _subject, message in task_commits(repo, [branch], own):
            for digest, rel in TRAILER_RE.findall(message):
                recorded.setdefault(rel, digest)  # newest commit first: its hash wins
    return recorded


def seal_problems(ws: Path, st: Status) -> list[str]:
    out = []
    seal = sealed(ws)
    for rel, digest in sorted(seal.items()):
        p = ws / rel
        if not p.is_file():
            out.append(f"MISSING  {rel} (sealed design evidence)")
        elif sha256(p) != digest:
            out.append(f"ALTERED  {rel} (sealed design evidence no longer matches its hash)")
    if seal and "evidence-seal" in st.fields:
        if sha256(ws / SEAL) != st.field("evidence-seal").split()[0]:
            out.append(f"ALTERED  {SEAL} (the seal file no longer matches STATUS evidence-seal)")
    return out


def cmd_verify(ws_arg: str, delivery: bool = False) -> int:
    ws, st = load(ws_arg)
    repos = changed_repos(st)
    task = st.field("task-id")
    own = task_token(task)
    bad = []
    # writes outside the changed repos: any repo with no recorded branch must hold no task commit
    for name, repo in sorted(all_repos(st).items()):
        if name in repos or not repo.is_dir():
            continue
        stray = task_commits(repo, ["--all"], own)
        if stray:
            sha, subject, _ = stray[0]
            bad.append(f"OUT OF SCOPE {name}: {len(stray)} {task} commit(s) in a repo with no recorded "
                       f"task branch (e.g. {sha[:7]} {subject!r}) — a write outside the changed repos, "
                       f"or a branch never recorded (ses status field <ws> branch.{name} <branch>)")
    if "pipeline" in st.fields and st.field("pipeline") == "change-request" and len(repos) > 1:
        bad.append(f"SCOPE    a change request records branches in {len(repos)} repos ({', '.join(sorted(repos))})"
                   f" — it changes one repo; more is /change-request §1's escalation rule")
    if not repos:
        bad += seal_problems(ws, st)
        if bad:
            print(f"0 recorded evidence file(s), {len(bad)} problem(s)")
            for b in bad:
                print(f"  {b}")
            return 1
        n = len(sealed(ws))
        print("no task branches recorded (e.g. a document task) — no checkpoint evidence to verify"
              + (f"; {n} sealed design evidence file(s) ok" if n else ""))
        return 0
    recorded: dict[str, str] = {}
    for name, (repo, branch) in sorted(repos.items()):
        commits = task_commits(repo, [branch], own)
        for _sha, _subject, message in commits:
            for digest, rel in TRAILER_RE.findall(message):
                recorded.setdefault(rel, digest)  # newest commit first: its hash wins
        if delivery:
            if not commits:
                bad.append(f"EMPTY    {name}: {branch} holds no {task} commit — nothing to deliver from "
                           f"this repo (finish its work, or drop its branch.{name} with the user)")
            for sha, subject, message in commits:
                if not TRAILER_RE.search(message):
                    bad.append(f"NO EVIDENCE {name}:{sha[:7]} {subject!r} — a task commit without "
                               f"Evidence-SHA256 lines (ses checkpoint trailer)")
        prefix = work_prefix(ws, repo)
        if prefix is not None:
            for p in git(repo, "ls-tree", "-r", "--name-only", branch, "--", prefix).splitlines():
                bad.append(f"IN GIT   {name}:{p} (workspace file committed on {branch} — would be pushed)")
    for rel, digest in sorted(recorded.items()):
        p = ws / rel
        if not p.is_file():
            bad.append(f"MISSING  {rel} (hash recorded in a checkpoint commit)")
        elif sha256(p) != digest:
            bad.append(f"ALTERED  {rel} (content no longer matches its recorded hash)")
    seal = sealed(ws)
    bad += seal_problems(ws, st)
    ev = ws / "evidence"
    unrecorded = sorted(str(p.relative_to(ws)) for p in ev.rglob("*")
                        if p.is_file() and str(p.relative_to(ws)) not in recorded
                        and str(p.relative_to(ws)) not in seal and str(p.relative_to(ws)) != SEAL) \
        if ev.is_dir() else []
    print(f"{len(recorded)} recorded evidence file(s), {len(bad)} problem(s)")
    if seal:
        print(f"{len(seal)} sealed design evidence file(s) ({SEAL})")
    for b in bad:
        print(f"  {b}")
    if unrecorded:
        print(f"warning: {len(unrecorded)} evidence file(s) with no recorded hash "
              f"(fine for research evidence; step and test-plan evidence should be recorded):")
        for u in unrecorded[:20]:
            print(f"  {u}")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] not in ("resume", "subject", "trailer", "seal", "verify"):
        print(__doc__)
        return 1
    cmd, ws, rest = argv[0], argv[1], argv[2:]
    if cmd == "resume":
        return cmd_resume(ws)
    if cmd == "subject":
        if len(rest) < 3:
            raise StatusError("usage: subject <ws> <repo-name> <N | tests> <description>")
        return cmd_subject(ws, rest[0], rest[1], " ".join(rest[2:]))
    if cmd == "trailer":
        return cmd_trailer(ws, rest)
    if cmd == "seal":
        return cmd_seal(ws, rest)
    if rest not in ([], ["--delivery"]):
        raise StatusError("usage: verify <ws> [--delivery]")
    return cmd_verify(ws, delivery=bool(rest))


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except StatusError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
