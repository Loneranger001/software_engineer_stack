#!/usr/bin/env python3
"""review.py — keep every reviewer report on disk and gate on it (run as `ses review`).

A reviewer (doc-fact-checker, code-reviewer, scope-auditor) returns its report
to the calling skill. Without a file, no later gate — and no resumed session —
can tell that a review ran, what it found, or HOW it ran: by the plugin's
custom agent, by a fresh subagent, or by the author re-reading its own work
(core/reviewers.md options 1–3). The last is the weakest, and the user must be
told when it is all there was.

Usage:
    review.py record  <ws> <reviewer> <target> --mode <mode> [--scope TEXT] [<report-file> | -]
        Saves the report (a file, or stdin with `-` / no file) as
        <ws>/reviews/<reviewer>-<target>-<n>.md (n = next free number), and
        records STATUS field review.<reviewer>.<target> =
        "<VERDICT> (<mode>, <date>, reviews/<file>)". The report keeps its own
        VERDICT line(s); a MODE line is written above them.
    review.py require <ws> <reviewer> <target>
        Exit 3 unless the LATEST report for <reviewer>/<target> passes: every
        VERDICT line in it says PASS (doc-fact-checker, scope-auditor) or
        APPROVE (code-reviewer). Prints the verdict and the mode — a
        self-pass is named, so the gate can tell the user.
    review.py list    <ws>
        The latest report per reviewer/target: verdict, mode, file.

    <reviewer>  doc-fact-checker | code-reviewer | scope-auditor
    <target>    what was reviewed, lower-case [a-z0-9._-]: fdd, tdd, tdd-grill,
                a repo name (code-reviewer: one report per changed repo),
                delivery (scope-auditor at /deliver), cr (a change request), …
    <mode>      custom-agent | subagent | self-pass   (core/reviewers.md options 1, 2, 3)

Exit codes: 0 ok, 1 error, 2 usage, 3 the review gate is not met.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from status import Status, StatusError, resolve  # noqa: E402

REVIEWERS = ("doc-fact-checker", "code-reviewer", "scope-auditor")
MODES = ("custom-agent", "subagent", "self-pass")
PASSING = {"PASS", "APPROVE"}
TARGET_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
VERDICT_RE = re.compile(r"^\s*VERDICT:\s*([A-Z-]+)", re.M)
MODE_RE = re.compile(r"^\s*MODE:\s*([a-z-]+)", re.M)
NOT_MET = 3


def workspace(ws_arg: str) -> tuple[Path, Status]:
    st = Status(resolve(ws_arg))
    return Path(st.path).parent, st


def check_names(reviewer: str, target: str) -> None:
    if reviewer not in REVIEWERS:
        raise StatusError(f"unknown reviewer '{reviewer}' ({' | '.join(REVIEWERS)})")
    if not TARGET_RE.match(target):
        raise StatusError(f"target '{target}' must be lower-case letters, digits, . _ - (e.g. tdd, inv-core)")


def reports(ws: Path, reviewer: str, target: str) -> list[Path]:
    """Reports for reviewer/target, oldest first by their number."""
    d = ws / "reviews"
    pat = re.compile(rf"^{re.escape(reviewer)}-{re.escape(target)}-(\d+)\.md$")
    found = [(int(m.group(1)), p) for p in d.glob("*.md") if (m := pat.match(p.name))] if d.is_dir() else []
    return [p for _n, p in sorted(found)]


def verdicts(text: str) -> list[str]:
    return VERDICT_RE.findall(text)


def cmd_record(argv: list[str]) -> int:
    mode = scope = None
    rest = []
    i = 0
    while i < len(argv):
        if argv[i] == "--mode" and i + 1 < len(argv):
            mode, i = argv[i + 1], i + 2
        elif argv[i] == "--scope" and i + 1 < len(argv):
            scope, i = argv[i + 1], i + 2
        else:
            rest.append(argv[i])
            i += 1
    if len(rest) not in (3, 4) or mode is None:
        raise StatusError("usage: record <ws> <reviewer> <target> --mode <mode> [--scope TEXT] [<report-file> | -]")
    ws, st = workspace(rest[0])
    reviewer, target = rest[1], rest[2]
    check_names(reviewer, target)
    if mode not in MODES:
        raise StatusError(f"--mode must be one of {' | '.join(MODES)} (core/reviewers.md options 1-3)")
    src = rest[3] if len(rest) == 4 else "-"
    text = sys.stdin.read() if src == "-" else Path(src).read_text()
    found = verdicts(text)
    if not found:
        raise StatusError("the report has no 'VERDICT: …' line — keep the reviewer's report format "
                          "(com.github.copilot/agents/<reviewer>.agent.md)")
    existing = reports(ws, reviewer, target)
    n = int(re.search(r"-(\d+)\.md$", existing[-1].name).group(1)) + 1 if existing else 1
    out = ws / "reviews" / f"{reviewer}-{target}-{n}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    header = f"# {reviewer} — {target} — report {n}\n\nMODE: {mode}\nDATE: {stamp}\n"
    if scope:
        header += f"REVIEW-SCOPE: {scope}\n"
    out.write_text(header + "\n" + text.rstrip("\n") + "\n")
    verdict = "/".join(dict.fromkeys(found))
    rel = out.relative_to(ws)
    st.set_field(f"review.{reviewer}.{target}", f"{verdict} ({mode}, {stamp[:10]}, {rel})")
    st.save()
    print(f"recorded {rel}: {verdict} ({mode})")
    if mode == "self-pass":
        print("note: self-pass — the author re-read its own work (core/reviewers.md option 3); "
              "say so to the user at the gate")
    return 0


def latest(ws: Path, reviewer: str, target: str) -> tuple[Path, list[str], str] | None:
    found = reports(ws, reviewer, target)
    if not found:
        return None
    text = found[-1].read_text()
    m = MODE_RE.search(text)
    return found[-1], verdicts(text), (m.group(1) if m else "unknown")


def cmd_require(argv: list[str]) -> int:
    if len(argv) != 3:
        raise StatusError("usage: require <ws> <reviewer> <target>")
    ws, _st = workspace(argv[0])
    reviewer, target = argv[1], argv[2]
    check_names(reviewer, target)
    last = latest(ws, reviewer, target)
    if last is None:
        print(f"review gate NOT met: no {reviewer} report for {target} in {ws / 'reviews'} — run the "
              f"review (core/reviewers.md) and keep it: ses review record <ws> {reviewer} {target} --mode <mode>")
        return NOT_MET
    path, found, mode = last
    rel = path.relative_to(ws)
    if not found or not all(v in PASSING for v in found):
        print(f"review gate NOT met: latest {reviewer} report for {target} ({rel}) says "
              f"{'/'.join(found) or 'no VERDICT'} — resolve its findings and review again")
        return NOT_MET
    extra = (" — a self-pass: the author re-read its own work; tell the user" if mode == "self-pass" else "")
    print(f"review gate ok: {reviewer} {target} {'/'.join(dict.fromkeys(found))} ({mode}, {rel}){extra}")
    return 0


def cmd_list(argv: list[str]) -> int:
    if len(argv) != 1:
        raise StatusError("usage: list <ws>")
    ws, _st = workspace(argv[0])
    d = ws / "reviews"
    keys = sorted({(m.group(1), m.group(2)) for p in (d.glob("*.md") if d.is_dir() else [])
                   if (m := re.match(rf"^({'|'.join(REVIEWERS)})-(.+)-\d+\.md$", p.name))})
    if not keys:
        print("no reviewer reports recorded")
        return 0
    for reviewer, target in keys:
        path, found, mode = latest(ws, reviewer, target)
        print(f"{reviewer:<17} {target:<16} {'/'.join(dict.fromkeys(found)) or '?':<9} {mode:<12} "
              f"{path.relative_to(ws)}")
    return 0


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "record":
        return cmd_record(rest)
    if cmd == "require":
        return cmd_require(rest)
    if cmd == "list":
        return cmd_list(rest)
    print(__doc__)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except StatusError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
