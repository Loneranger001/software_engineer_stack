#!/usr/bin/env python3
"""handoff.py — read and check the handoff summary at the top of a stage document.

Each stage document (scope-contract.md, research-notes.md, fdd.md, tdd.md)
opens with a bounded summary between these markers:

    <!-- handoff:start -->
    ## Handoff summary
    - Contract version: 2
    ...
    <!-- handoff:end -->

Later stages read the summary instead of the whole document and open full
sections only where they need detail. That only works if the summary cannot
silently drift from the body, so `check` enforces it. impl-doc.md has no
summary: it is terse and agent-only, and /implement reads it whole, so
`check` skips it. In a full or change-request workspace the FDD is optional:
a workspace check covers fdd.md only once STATUS.md records it approved (the
`fdd` field), so an abandoned draft never blocks a later gate. Name the file
to check a draft.

Usage:
    handoff.py show  <doc.md>        print the summary block only
    handoff.py check <doc.md|ws>...  validate one document, or every stage
                                     document present in a workspace dir

`check` fails (exit 1) when a summary is:
  - missing, or longer than MAX_LINES lines;
  - missing an ID the body defines or traces — the first cell of a table row
    (S1, N2, A3, Q1, ...);
  - missing its `- Contract version: <n>` line, or naming a version other
    than the workspace's scope-contract.md `- Version: <n>` (a summary built
    on an older contract is stale).
`check` also fails a tdd.md whose §7 Verification approach leaves out an
acceptance criterion of scope-contract.md (A#) or a test scenario of an
approved fdd.md (TS#): the test plan is built from §7, so a row missing there
is never tested, and `ses coverage` would never see it.
Exit codes: 0 ok, 1 problems found, 2 usage error.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from doctables import rows_missing_from_tdd  # noqa: E402

DOCS = ("scope-contract.md", "research-notes.md", "fdd.md", "tdd.md")
NO_SUMMARY = ("impl-doc.md",)  # read whole; a summary would only repeat its step table
MAX_LINES = 40
START, END = "<!-- handoff:start -->", "<!-- handoff:end -->"
ID_ROW = re.compile(r"^\|\s*([A-Z]{1,2}\d+)\s*\|", re.M)
VERSION = re.compile(r"^- Contract version:\s*v?(\S+)", re.M)
CONTRACT_VERSION = re.compile(r"^- Version:\s*v?(\d+)", re.M)


def split(text: str) -> tuple[str | None, str]:
    """Return (summary, body). Body excludes the summary block and HTML comments."""
    if START not in text or END not in text:
        return None, text
    head, rest = text.split(START, 1)
    summary, tail = rest.split(END, 1)
    body = re.sub(r"<!--.*?-->", "", head + tail, flags=re.S)
    return summary.strip("\n"), body


def contract_version(doc: Path) -> str | None:
    contract = doc.parent / "scope-contract.md"
    if not contract.is_file():
        return None
    m = CONTRACT_VERSION.search(contract.read_text())
    return m.group(1) if m else None


def fdd_in_play(ws: Path) -> bool:
    """Whether a workspace check covers ws/fdd.md: always in a standalone
    func-design workspace, else only once the STATUS `fdd` field says approved."""
    status = ws / "STATUS.md"
    if not status.is_file():
        return True
    text = status.read_text()
    pipeline = re.search(r"^- pipeline:\s*(\S+)", text, re.M)
    if not pipeline or pipeline.group(1) == "func-design":
        return True
    fdd = re.search(r"^- fdd:\s*(.*)$", text, re.M)
    return bool(fdd and fdd.group(1).strip().startswith("approved"))


def problems(doc: Path) -> list[str]:
    text = doc.read_text()
    summary, body = split(text)
    if summary is None:
        return [f"{doc}: no handoff summary ({START} … {END}) — write it before the gate"]
    out = []
    n = len(summary.splitlines())
    if n > MAX_LINES:
        out.append(f"{doc}: handoff summary is {n} lines (max {MAX_LINES}) — summarize, don't copy")
    ids = sorted(set(ID_ROW.findall(body)), key=lambda s: (s[0], int(re.sub(r"\D", "", s))))
    missing = [i for i in ids if not re.search(rf"\b{re.escape(i)}\b", summary)]
    if missing:
        out.append(f"{doc}: summary omits ID(s) the body defines or traces: {', '.join(missing)}")
    m = VERSION.search(summary)
    if not m:
        out.append(f"{doc}: summary has no '- Contract version: <n>' line")
    else:
        want = contract_version(doc)
        if want is not None and m.group(1) != want:
            out.append(f"{doc}: summary is based on contract v{m.group(1)} but scope-contract.md "
                       f"is v{want} — the document (and its summary) is stale")
    if doc.name == "tdd.md":
        gaps = rows_missing_from_tdd(doc.parent)
        if gaps:
            out.append(f"{doc}: §7 Verification approach has no row for " +
                       ", ".join(f"{i} ({src})" for i, src in gaps) +
                       " — every acceptance criterion and approved test scenario needs a §7 row")
    return out


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] not in ("show", "check"):
        print(__doc__)
        return 2
    cmd, targets = argv[0], [Path(a) for a in argv[1:]]
    if cmd == "show":
        if len(targets) != 1 or not targets[0].is_file():
            print("usage: handoff.py show <doc.md>", file=sys.stderr)
            return 2
        summary, _ = split(targets[0].read_text())
        if summary is None:
            print(f"{targets[0]}: no handoff summary — read the document's sections instead",
                  file=sys.stderr)
            return 1
        print(summary)
        return 0
    docs: list[Path] = []
    for t in targets:
        if t.is_dir():
            for d in DOCS:
                if not (t / d).is_file():
                    continue
                if d == "fdd.md" and not fdd_in_play(t):
                    print(f"skipped {t / d}: an FDD draft (not approved in STATUS.md) — name it to check it")
                    continue
                docs.append(t / d)
        elif t.is_file() and t.name in NO_SUMMARY:
            print(f"skipped {t}: it has no handoff summary by design — agents read it whole")
        elif t.is_file():
            docs.append(t)
        else:
            print(f"error: no such file or directory: {t}", file=sys.stderr)
            return 2
    if not docs:
        if all(t.is_dir() or t.name in NO_SUMMARY for t in targets):
            # e.g. a change-request or document workspace: nothing to hold to a summary
            print("no stage documents (scope-contract/research-notes/fdd/tdd) — nothing to check")
            return 0
        print("error: no stage documents found", file=sys.stderr)
        return 2
    found = [p for d in docs for p in problems(d)]
    for p in found:
        print(f"problem: {p}", file=sys.stderr)
    if not found:
        print(f"handoff summaries ok ({len(docs)} document(s))")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
