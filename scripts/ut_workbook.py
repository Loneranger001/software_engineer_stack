#!/usr/bin/env python3
"""ut_workbook.py — the unit-test results workbook, rendered from a task's evidence (run as `ses ut-workbook`).

The workbook is a VIEW of evidence the framework already holds, never a second
record: every cell comes from a file in the task workspace, and its outcomes
are the ones `ses coverage` reads. Nothing in it is typed by hand, so it
cannot claim a PASS the gate does not — and editing it afterwards would make
it a document nobody can rebuild. Rebuild it instead: the same evidence gives
the same bytes (same SHA-256).

Layout (one consolidated .xlsx):
  Summary   one row per test case — TC link, test ID, what it covers, type,
            description, test data, expected result, actual result, data
            check, outcome, mode, where the expected value came from, notes
  TC<n>     one sheet per test case, linked both ways with the Summary: the
            case's record, the values that differ, then the data itself —
            every table the test captured laid out in cells (a .csv/.tsv, or
            SQL*Plus/SQLcl output in its default layout), the fields its Check
            names highlighted and each checked value green (as expected) or
            red (differs); other output one line per row. Only what cells
            cannot hold (a binary file, or rows past --max-rows) is a link
            to the file instead.
  Evidence  every file the workbook was built from, with its SHA-256 and
            whether a task commit recorded it — the proof, kept off the TC sheets

Test cases, in order:
  full pipeline    the T# rows of impl-doc.md §3 test plan  → sheet TC<n> for T<n>
  change request   the A# criteria of analysis.md           → sheet TC<n> for A<n>

Per test case, from the evidence file holding its LATEST result (the file
`ses coverage` picks):
  Result table      Outcome, Mode, Expected from, Assertion checked
  Test cases table  (templates/test-evidence.md "## Test cases", one row per
                    T# or A#) Description, Test data, Expected result,
                    Actual result, Check — the fields to check (ut_data.py
                    has its syntax), Captured — the evidence/ files with the
                    data the test read and produced, each optionally
                    labelled ("Actual rows: evidence/raw/….csv"); a label
                    starting "Expected" marks the expected table, one
                    starting data/input/before/seed/setup/fixture the input
Missing there, the plan fills in what it can (impl-doc §3 Type, How run, Test
data and Expected, marked "planned"; the Result table's Assertion checked as
the actual result), and the gap is reported.

Gaps — what the workbook cannot show for a test case: no result; no Test cases
row; an empty Test data, Expected result or Actual result, or one that says only
"pass"; no captured file; a captured file that is missing or outside
evidence/; a Check that cannot be read or names a field no captured table
has; captured data that contradicts a recorded PASS; and, when building, a
captured file whose hash no task commit recorded (or that changed since).
Fill them while the evidence is still uncommitted — `--check`, before the
test-plan commit. After the commit hashes it, only a re-run under a new run
name can. A task scaffolded before 0.17.0 (STATUS.md `ses-version`) has no
Test cases tables to read: its gaps are listed but do not fail.

Usage:
    ut_workbook.py <ws> --check
          is every test case's record complete? Writes nothing; reads
          uncommitted evidence as it stands.
    ut_workbook.py <ws> [--out <file.xlsx>] [--ods] [--max-rows N]
          write the workbook (default <ws>/deliverables/<task-id>-unit-test-results.xlsx).
          Outcomes are `ses coverage`'s: an unrecorded result shows as UNRECORDED.
          --ods       also convert it to .ods with LibreOffice (soffice), headless
          --max-rows  rows shown per captured file (default 2000); the sheet
                      links the full file for the rest. Checks run on every row.

Exit codes: 0 complete; 3 a gap (0.17.0+ tasks; the workbook is still
written, gaps marked); 1 error; 2 usage; 127 --ods without LibreOffice (the
.xlsx is written).
"""
from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checkpoint import load, recorded_evidence, sha256  # noqa: E402
from coverage import results, status_of, strict_oracle  # noqa: E402
from doctables import ROW_ID, TEST_ID, col, section, strip_comments, tables  # noqa: E402
from status import StatusError  # noqa: E402

import ut_data  # noqa: E402
import xlsx  # noqa: E402
from xlsx import (BAD, CHECK_HEAD, EYE, FAIL, GOOD, GRID, GRID_HEAD, HEADER, KEY, KEY_HEAD, LINK, LINK_PLAIN,  # noqa: E402
                  MONO, NOTE, PASS, SECTION, TEXT, TITLE, WARN)

GAPS = 3
MAX_ROWS = 2000
MAX_DIFFS = 500
SINCE = (0, 17)
EMPTY = re.compile(r"^(|-+|—|–|tbd|\?+|\{.*\})$", re.I)
NO_VALUE = re.compile(r"^(pass(ed|es)?|ok|success(ful)?|as expected|works?|fine|correct)\.?$", re.I)
CAPTURED = re.compile(r"(?:([^,;:|`<>]+?)\s*:\s*)?`?(evidence/[A-Za-z0-9._/-]+)")
SUMMARY_COLS = [("TC", 8), ("Test", 7), ("Covers", 12), ("Type", 12), ("Description", 34), ("Test data", 34),
                ("Expected result", 34), ("Actual result", 34), ("Data check", 26), ("Outcome", 13), ("Mode", 14),
                ("Expected from", 24), ("Notes", 44)]
HEADER_ROW = 7
RECORD_SPAN = 8                  # a TC sheet's record values span columns B..H
MARK_STYLE = {"match": GOOD, "differ": BAD, "eye": EYE}
LEGEND = ("Blue headings: the fields checked · grey headings: the columns that match rows to the expected "
          "table · green: as expected · red: differs · amber: check by eye")


@dataclass
class Case:
    id: str
    covers: str = "—"
    type: str = "—"
    how: str = "—"
    plan_data: str = ""
    plan_expected: str = ""
    plan_desc: str = ""
    outcome: str = "NO-RESULT"
    evidence: str = ""
    recorded: bool = False
    date: str = ""
    mode: str = ""
    expected_from: str = ""
    assertion: str = ""
    desc: str = ""
    data: str = ""
    expected: str = ""
    actual: str = ""
    check: str = ""
    files: list[ut_data.Captured] = field(default_factory=list)
    result: ut_data.Result = field(default_factory=ut_data.Result)
    gaps: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def tc(self) -> str:
        return "TC" + re.sub(r"\D", "", self.id)

    @property
    def data_check(self) -> tuple[str, str]:
        return self.result.summary()


def blank(s: str) -> bool:
    return bool(EMPTY.match(s.strip(" `*")))


def version_at_least(st, want: tuple[int, int]) -> bool:
    if "ses-version" not in st.fields:
        return False
    m = re.match(r"^(\d+)\.(\d+)", st.field("ses-version"))
    return not m or (int(m.group(1)), int(m.group(2))) >= want


# --- the test cases ------------------------------------------------------------

def plan_cases(ws: Path) -> list[Case]:
    """Full pipeline: the T# rows of impl-doc.md §3, in order."""
    doc = ws / "impl-doc.md"
    if not doc.is_file():
        raise StatusError(f"no impl-doc.md in {ws} — its §3 test plan lists the test cases (/impl-plan)")
    body = strip_comments(section(doc.read_text(), re.compile(r"test plan", re.I)))
    out: dict[str, Case] = {}
    for header, rows in tables(body):
        t = col(header, "t#")
        if t is None:
            continue
        idx = {k: col(header, k) for k in ("covers", "type", "testdata", "howrun", "expected")}
        for r in rows:
            ids = TEST_ID.findall(r[t]) if t < len(r) else []
            if not ids or ids[0] in out:
                continue
            get = {k: (r[i] if i is not None and i < len(r) else "") for k, i in idx.items()}
            out[ids[0]] = Case(ids[0], covers=get["covers"] or "—", type=get["type"] or "—",
                               how=get["howrun"] or "—", plan_data=get["testdata"], plan_expected=get["expected"])
    if not out:
        raise StatusError("impl-doc.md §3 has no T# rows — the test plan lists the test cases")
    return list(out.values())


def criteria_cases(ws: Path) -> list[Case]:
    """Change request: the acceptance criteria A1…An of analysis.md, with their text."""
    doc = ws / "analysis.md"
    if not doc.is_file():
        raise StatusError(f"no analysis.md in {ws} — its mini contract lists the acceptance criteria")
    out: dict[str, Case] = {}
    inside = False
    for line in strip_comments(doc.read_text()).splitlines():
        if re.search(r"acceptance criteria", line, re.I):
            inside = True
            continue
        if inside and (re.match(r"^#", line) or re.match(r"^\s?[-*]\s+\*\*", line)):
            break
        m = re.match(r"^\s*(?:[-*]\s+|\|\s*)\**(A\d+)\b\**\s*[:.|—–-]?\s*(.*)$", line) if inside else None
        if m and m.group(1) not in out:
            text = re.sub(r"\s*\|\s*", " — ", m.group(2).strip().strip("|").strip())
            out[m.group(1)] = Case(m.group(1), covers=m.group(1), plan_desc=text)
    if not out:
        raise StatusError("analysis.md lists no acceptance criteria A1…An under its mini contract")
    return list(out.values())


# --- the evidence ---------------------------------------------------------------

def row_for(text: str, key: str, heading: re.Pattern[str] | None, needs: str) -> tuple[list[str], list[str]] | None:
    """(header, row) of the last table row whose first cell names `key`, in tables having column `needs`."""
    body = strip_comments(section(text, heading) if heading else text)
    found = None
    for header, rows in tables(body):
        if col(header, needs) in (None, 0):
            continue
        for r in rows:
            if r and key in TEST_ID.findall(r[0]) + ROW_ID.findall(r[0]):
                found = (header, r)
    return found


def cell(found: tuple[list[str], list[str]] | None, name: str) -> str:
    if not found:
        return ""
    header, r = found
    i = col(header, name)
    return r[i].strip() if i is not None and i < len(r) else ""


def label_for(case_id: str, rel: str) -> str:
    """tests-2026-11-16-T1-actual-rows.csv → "Actual rows"."""
    stem = Path(rel).stem
    m = re.search(rf"(?:^|-){re.escape(case_id)}-(.+)$", stem)
    words = re.sub(r"[-_]+", " ", m.group(1) if m else stem).strip()
    return words[:1].upper() + words[1:]


def fill(case: Case, ws: Path, res: dict, recorded: dict[str, str], texts: dict[str, str], check: bool) -> None:
    r = res.get(case.id)
    if r is None:
        case.outcome = "NO-RESULT"
        case.gaps.append("no result in evidence/ — run it")
        return
    case.outcome = r[0] if check else status_of(r)
    case.evidence, case.recorded = r[1], r[2]
    if case.evidence not in texts:
        texts[case.evidence] = (ws / case.evidence).read_text(errors="replace")
    text = texts[case.evidence]
    m = re.search(r"^- Date:\s*(\S+)", text, re.M)
    case.date = m.group(1) if m else ""
    result = row_for(text, case.id, None, "outcome")
    case.mode = cell(result, "mode")
    case.expected_from = cell(result, "expectedfrom")
    case.assertion = cell(result, "assertion")
    tc = row_for(text, case.id, re.compile(r"^test cases", re.I), "actual")
    if tc is None:
        case.gaps.append(f"no Test cases row in {case.evidence}")
    case.desc = cell(tc, "description")
    case.data = cell(tc, "testdata")
    case.expected = cell(tc, "expected")
    case.actual = cell(tc, "actual")
    case.check = "" if blank(cell(tc, "check")) else cell(tc, "check")
    for label, attr, fallback in (("Test data", "data", case.plan_data), ("Expected result", "expected",
                                  case.plan_expected), ("Actual result", "actual", case.assertion)):
        value = getattr(case, attr)
        if blank(value):
            if tc is not None:
                case.gaps.append(f"no {label}")
            if fallback and not blank(fallback):
                setattr(case, attr, fallback + (" (planned)" if attr != "actual" else " (assertion checked)"))
            else:
                setattr(case, attr, "")
        elif NO_VALUE.match(value.strip(" `*")):
            case.gaps.append(f"{label} says only '{value.strip()}' — state the value")
    for label, rel in CAPTURED.findall(cell(tc, "captured")):
        rel = rel.rstrip(".,;")
        p = (ws / rel).resolve()
        if ".." in Path(rel).parts or not p.is_relative_to((ws / "evidence").resolve()):
            case.gaps.append(f"captured file outside evidence/: {rel}")
            continue
        if not p.is_file():
            case.gaps.append(f"captured file missing: {rel}")
            continue
        label = label.strip() or label_for(case.id, rel)
        blocks, lines = ut_data.read(p)
        case.files.append(ut_data.Captured(label, rel, ut_data.role_of(label), blocks, lines))
        if not check and recorded.get(rel) != sha256(p):
            state = "changed since a task commit recorded it" if rel in recorded else "recorded by no task commit"
            case.gaps.append(f"captured file {state}: {rel}")
    if tc is not None and not case.files and not any(g.startswith("captured file") for g in case.gaps):
        case.gaps.append("no Captured file — the TC sheet has no data to show")
    checks, errors = ut_data.parse(case.check)
    case.gaps += errors
    case.result = ut_data.compare(case.files, checks)
    if case.result.unknown:
        case.gaps.append("the Check names " + ", ".join(case.result.unknown)
                         + ", which no captured table has (a CSV, or SQL*Plus output with its headings)")
    if case.result.differ and case.outcome == "PASS":
        case.gaps.append(f"the captured data contradicts the recorded PASS: {len(case.result.differ)} "
                         f"checked value(s) differ ({case.tc}) — the code, the outcome or the expected value "
                         f"is wrong; find which")


def explain(case: Case, st) -> None:
    """Notes that say what an outcome other than PASS means, and any waiver of a row the case covers."""
    why = {"PARTIAL": "static fallback: the code parsed, it did not run",
           "NO-ORACLE": "a PASS with no independent Expected from",
           "UNRECORDED": "the evidence file's hash is in no task commit, or changed since",
           "NOT-RUN": "the test could not run"}
    if case.outcome in why:
        case.notes.append(why[case.outcome])
    for rid in dict.fromkeys(ROW_ID.findall(case.covers) or [case.id]):
        if f"waiver.{rid}" in st.fields:
            case.notes.append(f"{rid} waived {st.field('waiver.' + rid)}")


# --- the workbook ---------------------------------------------------------------

def outcome_style(outcome: str) -> int:
    return PASS if outcome == "PASS" else FAIL if outcome == "FAIL" else WARN


def check_style(state: str) -> int:
    return {"PASS": PASS, "FAIL": FAIL, "WARN": WARN}.get(state, TEXT)


def file_target(ws: Path, rel: str, out: Path) -> str:
    """The captured file, relative to the workbook's folder (where Excel resolves a relative link)."""
    target = os.path.relpath(ws / rel, out.parent).replace(os.sep, "/")
    return quote(target, safe="/._-~")


def summary_sheet(wb: xlsx.Workbook, st, cases: list[Case]) -> xlsx.Sheet:
    sh = wb.add_sheet("Summary")
    task, pipeline = st.field("task-id"), st.field("pipeline")
    branches = ", ".join(f"{k[len('branch.'):]} → {st.field(k)}" for k in st.fields if k.startswith("branch.")) or "—"
    counts: dict[str, int] = {}
    for c in cases:
        counts[c.outcome] = counts.get(c.outcome, 0) + 1
    asof = max((c.date for c in cases if c.date), default="—")
    sh.set(1, 1, f"Unit test results — {task}", TITLE)
    sh.set(2, 1, f"Pipeline: {pipeline} · Branches: {branches}")
    sh.set(3, 1, f"As of: {asof} (latest evidence)")
    sh.set(4, 1, f"Result: {len(cases)} test case(s) — " + ", ".join(f"{n} {o}" for o, n in sorted(counts.items())))
    sh.set(5, 1, "Rendered by ses ut-workbook from the task's evidence; outcomes are those ses coverage reads. "
                 "Each TC sheet holds the test's data; the Evidence sheet holds the hashes. Rebuild it — never "
                 "edit it.", NOTE)
    for i, (name, width) in enumerate(SUMMARY_COLS, 1):
        sh.set(HEADER_ROW, i, name, HEADER)
        sh.width(i, width)
    for n, c in enumerate(cases, HEADER_ROW + 1):
        sh.link(n, 1, c.tc, c.tc, "A1", LINK)
        check_text, check_state = c.data_check
        values = [c.id, c.covers, c.type, c.desc or c.plan_desc or f"{c.type}: {c.how}", c.data, c.expected,
                  c.actual, check_text, c.outcome, c.mode or "—", c.expected_from or "—",
                  "; ".join(c.notes + [f"gap: {g}" for g in c.gaps]) or "—"]
        for i, v in enumerate(values, 2):
            style = outcome_style(c.outcome) if i == 10 else check_style(check_state) if i == 9 else TEXT
            sh.set(n, i, v or "—", style)
    sh.freeze_rows = HEADER_ROW
    sh.autofilter = f"A{HEADER_ROW}:{xlsx.col_letter(len(SUMMARY_COLS))}{HEADER_ROW + len(cases)}"
    return sh


def grid(sh: xlsx.Sheet, row: int, b: ut_data.Block, limit: int) -> int:
    for ri, r in enumerate(b.rows[:limit + 1]):
        for ci, v in enumerate(r):
            if ri == 0:
                style = CHECK_HEAD if ci in b.checked else KEY_HEAD if ci in b.keys else GRID_HEAD
            else:
                style = MARK_STYLE.get(b.marks.get((ri, ci)), GRID)
            sh.set(row, ci + 1, v, style)
        row += 1
    return row


def column_widths(case: Case) -> dict[int, float]:
    """Each column as wide as the data it shows (8-50 characters); the record's key column at least 24."""
    need: dict[int, int] = {}
    for f in case.files:
        for b in f.blocks:
            if b.kind != "grid":
                continue
            for r in b.rows[:200]:
                for ci, v in enumerate(r, 1):
                    need[ci] = max(need.get(ci, 0), len(v))
    for d in case.result.differ[:MAX_DIFFS]:                 # the Differences table shares the columns
        for ci, v in enumerate(d, 1):
            need[ci] = max(need.get(ci, 0), len(v))
    out = {1: max(24.0, min(50, need.get(1, 0) + 2))}
    for c in range(2, max([RECORD_SPAN, *need]) + 1):
        out[c] = float(max(12 if c <= RECORD_SPAN else 8, min(50, need.get(c, 0) + 2)))
    return out


def case_sheet(wb: xlsx.Workbook, ws: Path, case: Case, summary_row: int, out: Path, max_rows: int) -> None:
    sh = wb.add_sheet(case.tc)
    widths = column_widths(case)
    for c, w in widths.items():
        sh.width(c, w)
    per_line = sum(widths[c] for c in range(2, RECORD_SPAN + 1)) * 1.1
    sh.link(1, 1, "← Summary", "Summary", f"A{summary_row}", LINK_PLAIN)
    sh.link(1, 2, "Evidence and hashes →", "Evidence", "A1", LINK_PLAIN)
    sh.set(2, 1, f"{case.tc} — {case.id}: {case.desc or case.plan_desc or case.how}", TITLE)
    check_text, check_state = case.data_check
    record = [("Test case", case.tc, TEXT), ("Test", case.id, TEXT), ("Covers", case.covers, TEXT),
              ("Type", case.type, TEXT), ("How run", case.how, TEXT),
              ("Description", case.desc or case.plan_desc or "—", TEXT), ("Test data", case.data, TEXT),
              ("Expected result", case.expected, TEXT), ("Expected from", case.expected_from, TEXT),
              ("Actual result", case.actual, TEXT), ("Check", case.check, TEXT),
              ("Data check", check_text, check_style(check_state)), ("Assertion checked", case.assertion, TEXT),
              ("Outcome", case.outcome, outcome_style(case.outcome)), ("Mode", case.mode, TEXT),
              ("Ran", case.date, TEXT), ("Notes", "; ".join(case.notes) or "—", TEXT),
              ("Gaps", "; ".join(case.gaps) or "none", TEXT)]
    row = 4
    for key, value, style in record:
        value = value or "—"
        sh.set(row, 1, key, KEY)
        sh.set(row, 2, value, style)
        for c in range(3, RECORD_SPAN + 1):       # the merged cell keeps its border across
            sh.set(row, c, "", style)
        sh.merge(row, 2, RECORD_SPAN)
        lines = sum(max(1, math.ceil(len(part) / per_line)) for part in value.split("\n"))
        if lines > 1:
            sh.height(row, 15 * lines)
        row += 1
    if case.result.differ:
        row += 1
        sh.set(row, 1, f"Differences ({len(case.result.differ)})", SECTION)
        row += 1
        sh.row(row, ["Where", "Row", "Field", "Expected", "Actual"], GRID_HEAD)
        row += 1
        for where, which, fld, want, got in case.result.differ[:MAX_DIFFS]:
            sh.row(row, [where, which, fld, want], GRID)
            sh.set(row, 5, got, BAD)
            row += 1
        if len(case.result.differ) > MAX_DIFFS:
            sh.set(row, 1, f"… {len(case.result.differ) - MAX_DIFFS} more — every one is red in the data below", NOTE)
            row += 1
    if not case.files and case.evidence:          # nothing captured: the output the evidence file recorded
        text = (ws / case.evidence).read_text(errors="replace")
        body = section(text, re.compile(r"^output", re.I)) or text
        lines = [l for l in body.splitlines() if not l.strip().startswith("```")]
        row += 1
        sh.set(row, 1, "Output recorded in the evidence file — this test lists no captured data", SECTION)
        row += 1
        for line in lines[:max_rows]:
            sh.set(row, 1, line, MONO)
            row += 1
    for f in case.files:
        row += 1
        sh.set(row, 1, f.label, SECTION)
        role = {"expected": "the expected result", "input": "the test's input — shown, not checked"}.get(f.role, "")
        sh.set(row + 1, 1, f"From {f.rel}" + (f" — {role}" if role else ""), NOTE)
        row += 2
        if any(b.checked for b in f.blocks):
            sh.set(row, 1, LEGEND, NOTE)
            row += 1
        total = sum(len(b.rows) for b in f.blocks if b.kind != "file")
        shown = 0
        for b in f.blocks:
            if b.kind == "file":
                sh.set(row, 1, f"Not shown in cells: {b.reason}.", NOTE)
                sh.link_file(row + 1, 1, f"Open {Path(f.rel).name}", file_target(ws, f.rel, out))
                row += 2
                continue
            room = max_rows - shown
            if room <= 0 or row >= xlsx.MAX_ROWS - max_rows - 10:
                break
            if b.kind == "grid":
                n = min(len(b.rows), room + 1)          # the headings, then up to `room` rows
                row = grid(sh, row, b, n - 1) + 1
            else:
                n = min(len(b.rows), room)
                for r in b.rows[:n]:
                    sh.set(row, 1, r[0], MONO)
                    row += 1
            shown += n
        if total > shown:
            ran = "; the Check ran on every row" if any(b.checked for b in f.blocks) else ""
            sh.set(row, 1, f"… {total - shown} more row(s) not shown{ran} —", NOTE)
            sh.link_file(row, 2, f"open the full {Path(f.rel).name}", file_target(ws, f.rel, out))
            row += 1


def evidence_sheet(wb: xlsx.Workbook, ws: Path, cases: list[Case], recorded: dict[str, str]) -> None:
    sh = wb.add_sheet("Evidence")
    for i, (name, width) in enumerate([("TC", 8), ("Test", 7), ("What", 24), ("File", 52), ("SHA-256", 70),
                                       ("Recorded by a task commit", 26)], 1):
        sh.set(3, i, name, HEADER)
        sh.width(i, width)
    sh.set(1, 1, "Evidence — the files this workbook was built from", TITLE)
    sh.set(2, 1, "Each hash is checked against the task's commits (ses checkpoint verify); a rebuild from the same "
                 "files gives the same workbook.", NOTE)
    row = 4
    for c in cases:
        items = ([("Result and test record", c.evidence)] if c.evidence else []) + [(f.label, f.rel) for f in c.files]
        for what, rel in items:
            digest = sha256(ws / rel)
            ok = recorded.get(rel) == digest
            sh.link(row, 1, c.tc, c.tc, "A1", LINK)
            sh.row(row, [c.id, what, rel, digest], TEXT, start=2)
            sh.set(row, 6, "yes" if ok else ("changed since" if rel in recorded else "no"), PASS if ok else WARN)
            row += 1
    sh.freeze_rows = 3


def build(path: Path, ws: Path, st, cases: list[Case], recorded: dict[str, str], max_rows: int) -> None:
    wb = xlsx.Workbook(f"Unit test results — {st.field('task-id')}")
    summary_sheet(wb, st, cases)
    for n, case in enumerate(cases, HEADER_ROW + 1):
        case_sheet(wb, ws, case, n, path, max_rows)
    evidence_sheet(wb, ws, cases, recorded)
    wb.save(path)
    with zipfile.ZipFile(path) as z:            # read it back: every part must parse
        for name in z.namelist():
            ElementTree.fromstring(z.read(name))


def soffice() -> str | None:
    for exe in ("soffice", "libreoffice"):
        if shutil.which(exe):
            return shutil.which(exe)
    mac = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
    return str(mac) if mac.is_file() else None


def to_ods(path: Path) -> Path | None:
    exe = soffice()
    if exe is None:
        print("error: LibreOffice (soffice) not found — the .xlsx is written; for .ods install it:\n"
              "  macOS:         brew install --cask libreoffice\n"
              "  Debian/Ubuntu: sudo apt-get install libreoffice-calc\n"
              "  RHEL/Oracle:   sudo dnf install libreoffice-calc", file=sys.stderr)
        return None
    with tempfile.TemporaryDirectory() as profile:   # its own profile: a running LibreOffice cannot swallow the job
        r = subprocess.run([exe, f"-env:UserInstallation={Path(profile).as_uri()}", "--headless",
                            "--convert-to", "ods", "--outdir", str(path.parent), str(path)],
                           capture_output=True, text=True, timeout=300)
    ods = path.with_suffix(".ods")
    if r.returncode != 0 or not ods.is_file() or ods.stat().st_size == 0:
        raise StatusError(f"LibreOffice did not convert {path.name}: {(r.stderr or r.stdout).strip()}")
    return ods


# --- main -----------------------------------------------------------------------

def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    args, opts = [], {"--check": False, "--ods": False, "--out": None, "--max-rows": str(MAX_ROWS)}
    it = iter(argv)
    for a in it:
        if a in ("--check", "--ods"):
            opts[a] = True
        elif a in ("--out", "--max-rows"):
            opts[a] = next(it, None)
            if opts[a] is None:
                print(f"error: {a} needs a value", file=sys.stderr)
                return 2
        elif a.startswith("-"):
            print(f"error: unknown option {a}", file=sys.stderr)
            return 2
        else:
            args.append(a)
    if len(args) != 1 or not str(opts["--max-rows"]).isdigit() or int(opts["--max-rows"]) < 1:
        print(__doc__)
        return 2
    check, max_rows = opts["--check"], int(opts["--max-rows"])
    ws, st = load(args[0])
    task, pipeline = st.field("task-id"), st.field("pipeline")
    if pipeline not in ("full", "change-request"):
        print(f"ut-workbook {task} ({pipeline}): this pipeline runs no tests — nothing to render")
        return 0
    strict = version_at_least(st, SINCE)
    cases = plan_cases(ws) if pipeline == "full" else criteria_cases(ws)
    recorded = recorded_evidence(ws, st)
    res = results(ws, recorded, strict_oracle(st))
    texts: dict[str, str] = {}
    for c in cases:
        fill(c, ws, res, recorded, texts, check)
        explain(c, st)

    counts: dict[str, int] = {}
    for c in cases:
        counts[c.outcome] = counts.get(c.outcome, 0) + 1
    print(f"ut-workbook{' check' if check else ''} {task} ({pipeline}): {len(cases)} test case(s) — "
          + ", ".join(f"{n} {o}" for o, n in sorted(counts.items())))
    for c in cases:
        detail = f"{len(c.files)} captured" + (f"; {c.data_check[0]}" if c.data_check[0] else "") \
            + (f"; {len(c.gaps)} gap(s)" if c.gaps else "")
        print(f"  {c.tc:<5} {c.id:<4} {c.outcome:<11} {c.evidence or '—':<34} {detail}")

    code = 0
    if not check:
        out = Path(opts["--out"]) if opts["--out"] else ws / "deliverables" / f"{task}-unit-test-results.xlsx"
        if out.suffix.lower() != ".xlsx":
            print(f"error: --out must end in .xlsx: {out}", file=sys.stderr)
            return 2
        build(out, ws, st, cases, recorded, max_rows)
        print(f"wrote {out} ({2 + len(cases)} sheets, sha256 {sha256(out)})")
        if opts["--ods"]:
            ods = to_ods(out)
            if ods is None:
                code = 127
            else:
                print(f"wrote {ods} (LibreOffice conversion; the .xlsx is the reproducible copy)")

    gapped = [c for c in cases if c.gaps]
    if gapped:
        label = "GAPS" if strict else "GAPS (a task begun before 0.17.0 — listed, not failed)"
        print(f"{label}:")
        for c in gapped:
            print(f"  {c.tc} ({c.id}): " + "; ".join(c.gaps))
        if strict:
            print("Fill each in the evidence file before the test-plan commit hashes it (a Test cases row per "
                  "test, its data captured into evidence/raw/). Committed evidence is never edited: re-run the "
                  "test under a new run name, with its own tests: commit.")
            code = code or GAPS
    return code


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except StatusError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
