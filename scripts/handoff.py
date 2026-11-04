#!/usr/bin/env python3
"""handoff.py — read and check the handoff summary at the top of a stage document.

Each stage document (scope-contract.md, research-notes.md, fdd.md, tdd.md,
impl-doc.md) opens with a bounded summary between these markers:

    <!-- handoff:start -->
    ## Handoff summary
    - Contract version: 2
    ...
    <!-- handoff:end -->

Later stages read the summary instead of the whole document and open full
sections only where they need detail. That only works if the summary cannot
silently drift from the body, so `check` enforces it.

Usage:
    handoff.py show  <doc.md>        print the summary block only
    handoff.py check <doc.md|ws>...  validate one document, or every stage
                                     document present in a workspace dir

`check` fails (exit 1) when a summary is:
  - missing, or longer than MAX_LINES lines;
  - missing an ID the body defines or traces — the first cell of a table row
    (S1, N2, A3, Q1, T4, ...) — or, for impl-doc.md, a numbered step
    (written `step <N>` in the summary);
  - missing its `- Contract version: <n>` line, or naming a version other
    than the workspace's scope-contract.md `- Version: <n>` (a summary built
    on an older contract is stale).
Exit codes: 0 ok, 1 problems found, 2 usage error.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

DOCS = ("scope-contract.md", "research-notes.md", "fdd.md", "tdd.md", "impl-doc.md")
MAX_LINES = 40
START, END = "<!-- handoff:start -->", "<!-- handoff:end -->"
ID_ROW = re.compile(r"^\|\s*([A-Z]{1,2}\d+)\s*\|", re.M)
STEP_ROW = re.compile(r"^\|\s*(\d+)\s*\|", re.M)
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


def section(body: str, title_re: str) -> str:
    m = re.search(rf"^##+ [^\n]*{title_re}[^\n]*\n(.*?)(?=^## |\Z)", body, re.S | re.M | re.I)
    return m.group(1) if m else ""


def contract_version(doc: Path) -> str | None:
    contract = doc.parent / "scope-contract.md"
    if not contract.is_file():
        return None
    m = CONTRACT_VERSION.search(contract.read_text())
    return m.group(1) if m else None


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
    if doc.name == "impl-doc.md":
        steps = sorted(set(STEP_ROW.findall(section(body, "Implementation steps"))), key=int)
        miss = [s for s in steps if not re.search(rf"\bstep {s}\b", summary, re.I)]
        if miss:
            out.append(f"{doc}: summary omits step(s): {', '.join('step ' + s for s in miss)}")
    m = VERSION.search(summary)
    if not m:
        out.append(f"{doc}: summary has no '- Contract version: <n>' line")
    else:
        want = contract_version(doc)
        if want is not None and m.group(1) != want:
            out.append(f"{doc}: summary is based on contract v{m.group(1)} but scope-contract.md "
                       f"is v{want} — the document (and its summary) is stale")
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
            docs += [t / d for d in DOCS if (t / d).is_file()]
        elif t.is_file():
            docs.append(t)
        else:
            print(f"error: no such file or directory: {t}", file=sys.stderr)
            return 2
    if not docs:
        if all(t.is_dir() for t in targets):
            # e.g. a change-request or document workspace: nothing to hold to a summary
            print("no stage documents (scope-contract/research-notes/fdd/tdd/impl-doc) — nothing to check")
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
