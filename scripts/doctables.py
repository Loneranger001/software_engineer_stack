"""doctables.py — read the tables of a task's stage documents (shared by coverage, handoff, impl-check).

Not a command: `ses coverage`, `ses handoff` and `ses impl-check` import it, so
the three read an acceptance row, a test scenario or a TDD §7 row the same way.

The acceptance rows of a full-pipeline task live in three documents, and each
must reach the TDD's §7 Verification approach, which the test plan and
`ses coverage` work from:

  scope-contract.md  "## Acceptance criteria"          A1, A2, …
  fdd.md (approved)  "## 14. Functional test scenarios" TS1, TS2, …
  tdd.md             "## 7. Verification approach"      A#, TS#, G# — one or more
                                                        IDs in a row's first cell
"""
from __future__ import annotations

import re
from pathlib import Path

ROW_ID = re.compile(r"\b(?:A|TS|G)\d+\b")
TEST_ID = re.compile(r"\bT\d+\b")
VERIFICATION = re.compile(r"^7\.|verification approach", re.I)


def cells(line: str) -> list[str]:
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    """[(header cells, rows)] for every Markdown table in text."""
    out: list[tuple[list[str], list[list[str]]]] = []
    cur: tuple[list[str], list[list[str]]] | None = None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("|") and s.endswith("|") and len(s) > 1:
            row = cells(s)
            if cur is None:
                cur = (row, [])
            elif not all(re.fullmatch(r":?-{3,}:?", c) for c in row if c):
                cur[1].append(row)
        elif cur is not None:
            out.append(cur)
            cur = None
    if cur is not None:
        out.append(cur)
    return out


def section(text: str, heading: re.Pattern[str]) -> str:
    """The body under the first heading matching `heading`, up to the next heading of its level or above."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(#+)\s+(.*)$", line)
        if m and heading.search(m.group(2)):
            level = len(m.group(1))
            body = []
            for nxt in lines[i + 1:]:
                h = re.match(r"^(#+)\s", nxt)
                if h and len(h.group(1)) <= level:
                    break
                body.append(nxt)
            return "\n".join(body)
    return ""


def col(header: list[str], name: str) -> int | None:
    for i, h in enumerate(header):
        if h.lower().replace(" ", "").startswith(name):
            return i
    return None


def strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def first_cell_ids(body: str, pattern: re.Pattern[str]) -> list[str]:
    """IDs named in the first cell of the first table in body, in order, without repeats."""
    out: list[str] = []
    for _header, rows in tables(strip_comments(body))[:1]:
        for r in rows:
            out += [i for i in pattern.findall(r[0]) if i not in out]
    return out


def tdd_verification_ids(ws: Path) -> list[str] | None:
    """A#/TS#/G# named in tdd.md §7, or None when there is no tdd.md or no §7 table yet."""
    doc = ws / "tdd.md"
    if not doc.is_file():
        return None
    body = section(doc.read_text(), VERIFICATION)
    if not tables(strip_comments(body)):
        return None
    return first_cell_ids(body, ROW_ID)


def contract_criteria(ws: Path) -> list[str]:
    """A# rows of scope-contract.md's Acceptance criteria table ([] without a contract)."""
    doc = ws / "scope-contract.md"
    if not doc.is_file():
        return []
    return first_cell_ids(section(doc.read_text(), re.compile(r"acceptance criteria", re.I)),
                          re.compile(r"\bA\d+\b"))


def fdd_approved(ws: Path) -> bool:
    status = ws / "STATUS.md"
    if not status.is_file():
        return False
    m = re.search(r"^- fdd:\s*(.*)$", status.read_text(), re.M)
    return bool(m and m.group(1).strip().startswith("approved"))


def fdd_scenarios(ws: Path) -> list[str]:
    """TS# rows of an APPROVED fdd.md's §14 test scenarios ([] without one; a draft never counts)."""
    doc = ws / "fdd.md"
    if not doc.is_file() or not fdd_approved(ws):
        return []
    return first_cell_ids(section(doc.read_text(), re.compile(r"functional test scenarios", re.I)),
                          re.compile(r"\bTS\d+\b"))


def rows_missing_from_tdd(ws: Path) -> list[tuple[str, str]]:
    """[(ID, source document)] for every contract A# and approved-FDD TS# that tdd.md §7 does not
    name — rows the test plan and `ses coverage` would otherwise never see. [] while §7 does not exist."""
    tdd = tdd_verification_ids(ws)
    if tdd is None:
        return []
    out = [(a, "scope-contract.md") for a in contract_criteria(ws) if a not in tdd]
    out += [(t, "fdd.md") for t in fdd_scenarios(ws) if t not in tdd]
    return out
