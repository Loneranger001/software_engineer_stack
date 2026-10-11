#!/usr/bin/env python3
"""check_knowledge.py — keep knowledge/ honest.

Two checks, both run in CI and the pre-commit hook:

1. decisions.md "Applied changes": every entry must name at least one
   canonical framework file (repo-root path in backticks), every named file
   must exist, and each must have a commit touching it on or after the
   entry's date. This catches the failure where /retro records a change as
   applied but the edit landed in a generated install copy (copilot/,
   .github/se-stack/) and was lost on the next rebuild. Entries tagged
   `[pending-upstream]` are approved-but-not-applied and skip the git check.
   Limitation: it proves the file was touched after the date, not that the
   touch was this change — it catches lost edits, not wrong ones.

2. lessons.md: every lesson line matches the documented format with a known
   stage tag, so stage filtering never silently misses an entry.

Usage: check_knowledge.py [--stack-root PATH]
Exit codes: 0 ok, 1 problems found, 2 cannot check (e.g. shallow clone).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

CANONICAL_DIRS = ("skills", "agents", "templates", "checklists", "core",
                  "standards", "scripts", "knowledge", "docs", "examples", ".claude-plugin")
CANONICAL_FILES = ("README.md",)
GENERATED_PREFIXES = ("copilot/", ".github/prompts/", ".github/skills/", ".github/agents/",
                      ".github/copilot-instructions.md", ".github/se-stack/", "AGENTS.md")
STAGES = ("intake", "research", "tech-design", "grill", "impl-plan", "implement", "deliver",
          "change-request", "document", "understand", "verify", "any")
ENTRY_RE = re.compile(r"^- \[(\d{4}-\d{2}-\d{2})\] (.*)$")
LESSON_RE = re.compile(r"^- \[\d{4}-\d{2}-\d{2}\] \[stage:([a-z-]+)\] \[lang:(plsql|sql|ksh|python|-)\] "
                       r"\[repo:[^\]]+\] .+ \(task [^)]+\)$")


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def section(text: str, heading: str) -> list[str]:
    out, inside = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line[3:].strip().lower() == heading.lower()
            continue
        if inside:
            out.append(line)
    return out


def named_paths(entry: str) -> list[str]:
    """Backticked tokens that claim to be edited files.

    A token counts when it starts with a framework or generated directory, or
    ends in a file extension (so a bare `research/SKILL.md` is still caught).
    Prose like `evidence/raw/` or `work/<id>/` is a mention, not a claim.
    """
    paths = []
    for tok in re.findall(r"`([^`]+)`", entry):
        first = tok.split()[0].rstrip(",.;:")
        if first in CANONICAL_FILES:
            paths.append(first)
        elif "/" in first and (first.split("/")[0] in CANONICAL_DIRS
                               or first.startswith(GENERATED_PREFIXES)
                               or re.search(r"\.[A-Za-z0-9]+$", first)):
            paths.append(first)
    return paths


def check_decisions(root: Path) -> list[str]:
    problems = []
    lines = section((root / "knowledge" / "decisions.md").read_text(), "Applied changes")
    for line in lines:
        m = ENTRY_RE.match(line)
        if not m:
            continue
        day, body = m.group(1), m.group(2)
        label = f"decisions.md [{day}] {body[:70]}…"
        try:
            since = date.fromisoformat(day) - timedelta(days=1)  # timezone slack
        except ValueError:
            problems.append(f"{label}: invalid date")
            continue
        if body.startswith("[pending-upstream]"):
            continue
        paths = named_paths(body)
        if not paths:
            problems.append(f"{label}: names no edited file — add the repo-root path(s) in backticks")
            continue
        for p in paths:
            if p.startswith(GENERATED_PREFIXES):
                problems.append(f"{label}: `{p}` is generated output — name the canonical source file")
                continue
            if not (p in CANONICAL_FILES or p.split("/")[0] in CANONICAL_DIRS):
                problems.append(f"{label}: `{p}` is not a framework path (expected under "
                                f"{', '.join(CANONICAL_DIRS)})")
                continue
            if not (root / p).exists():
                problems.append(f"{label}: `{p}` does not exist")
                continue
            # committed history first; a staged or modified file counts too, so the
            # pre-commit hook passes on the commit that carries the edit
            touched = git(root, "log", f"--since={since.isoformat()}", "--format=%h", "-1", "--", p)
            if not touched:
                touched = git(root, "status", "--porcelain", "--", p)
            if not touched:
                problems.append(f"{label}: no commit touches `{p}` since {day} — the change is "
                                f"recorded as applied but the file never changed (lost edit?)")
    return problems


def check_lessons(root: Path) -> list[str]:
    problems = []
    text = (root / "knowledge" / "lessons.md").read_text()
    marker = "<!-- lessons below this line -->"
    body = text.split(marker, 1)[1] if marker in text else text
    for n, line in enumerate(body.splitlines(), 1):
        if not line.startswith("- "):
            continue
        m = LESSON_RE.match(line)
        if not m:
            problems.append(f"lessons.md: malformed lesson (format in the file header): {line[:90]}")
        elif m.group(1) not in STAGES:
            problems.append(f"lessons.md: unknown stage tag '{m.group(1)}' — skills filter on "
                            f"{'|'.join(STAGES)}: {line[:90]}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stack-root", type=Path, default=Path(__file__).resolve().parent.parent)
    root = ap.parse_args().stack_root.resolve()
    try:
        if git(root, "rev-parse", "--is-shallow-repository") == "true":
            print("error: shallow clone — check_knowledge needs full history "
                  "(actions/checkout with fetch-depth: 0)", file=sys.stderr)
            return 2
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"error: {root} is not a git checkout ({e})", file=sys.stderr)
        return 2
    problems = check_decisions(root) + check_lessons(root)
    for p in problems:
        print(f"problem: {p}", file=sys.stderr)
    if not problems:
        print("knowledge ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
