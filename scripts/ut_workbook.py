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
            description, test data, expected result, actual result, outcome,
            mode, where the expected value came from, evidence file, notes
  TC<n>     one sheet per test case, linked both ways with the Summary: the
            case's full record, then each file it captured (a .csv/.tsv laid
            out in cells, any other file one line per row), each with its
            SHA-256 and whether a task commit recorded it

Test cases, in order:
  full pipeline    the T# rows of impl-doc.md §3 test plan  → sheet TC<n> for T<n>
  change request   the A# criteria of analysis.md           → sheet TC<n> for A<n>

Per test case, from the evidence file holding its LATEST result (the file
`ses coverage` picks):
  Result table      Outcome, Mode, Expected from, Assertion checked
  Test cases table  (templates/test-evidence.md "## Test cases", one row per
                    T# or A#) Description, Test data, Expected result,
                    Actual result, Captured — the evidence/ files with the
                    data the test read and produced, normally
                    evidence/raw/<run>-T<n>-<what>.csv from `ses capture --ext csv`
Missing there, the plan fills in what it can (impl-doc §3 Type, How run, Test
data and Expected, marked "planned"; the Result table's Assertion checked as
the actual result), and the gap is reported.

Gaps — what the workbook cannot show for a test case: no result; no Test cases
row; an empty Test data, Expected result or Actual result, or one that says only
"pass"; no captured file; a captured file that is missing or outside
evidence/; and, when building, a captured file whose hash no task commit
recorded (or that changed since). Fill them while the evidence is still
uncommitted — `--check`, before the test-plan commit. After the commit hashes
it, only a re-run under a new run name can. A task scaffolded before 0.17.0
(STATUS.md `ses-version`) has no Test cases tables to read: its gaps are
listed but do not fail.

Usage:
    ut_workbook.py <ws> --check
          is every test case's record complete? Writes nothing; reads
          uncommitted evidence as it stands.
    ut_workbook.py <ws> [--out <file.xlsx>] [--ods] [--max-rows N]
          write the workbook (default <ws>/deliverables/<task-id>-unit-test-results.xlsx).
          Outcomes are `ses coverage`'s: an unrecorded result shows as UNRECORDED.
          --ods       also convert it to .ods with LibreOffice (soffice), headless
          --max-rows  rows shown per captured file (default 2000); the rest is
                      named, and stays in the file the sheet cites

Exit codes: 0 complete; 3 a gap (0.17.0+ tasks; the workbook is still
written, gaps marked); 1 error; 2 usage; 127 --ods without LibreOffice (the
.xlsx is written).
"""
from __future__ import annotations

import csv
import io
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checkpoint import load, recorded_evidence, sha256  # noqa: E402
from coverage import results, status_of, strict_oracle  # noqa: E402
from doctables import ROW_ID, TEST_ID, col, section, strip_comments, tables  # noqa: E402
from status import StatusError  # noqa: E402

import xlsx  # noqa: E402
from xlsx import FAIL, GRID, GRID_HEAD, HEADER, KEY, LINK, LINK_PLAIN, MONO, NOTE, PASS, SECTION, TEXT, TITLE, WARN  # noqa: E402

GAPS = 3
MAX_ROWS = 2000
SINCE = (0, 17)
EMPTY = re.compile(r"^(|-+|—|–|tbd|\?+|\{.*\})$", re.I)
NO_VALUE = re.compile(r"^(pass(ed|es)?|ok|success(ful)?|as expected|works?|fine|correct)\.?$", re.I)
CAPTURED = re.compile(r"evidence/[A-Za-z0-9._/-]+")
SUMMARY_COLS = [("TC", 8), ("Test", 7), ("Covers", 12), ("Type", 12), ("Description", 34), ("Test data", 34),
                ("Expected result", 34), ("Actual result", 34), ("Outcome", 13), ("Mode", 14),
                ("Expected from", 24), ("Evidence", 30), ("Notes", 44)]
HEADER_ROW = 7


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
    captured: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def tc(self) -> str:
        return "TC" + re.sub(r"\D", "", self.id)


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
    for rel in CAPTURED.findall(cell(tc, "captured")):
        rel = rel.rstrip(".,;")
        p = (ws / rel).resolve()
        if ".." in Path(rel).parts or not p.is_relative_to((ws / "evidence").resolve()):
            case.gaps.append(f"captured file outside evidence/: {rel}")
        elif not p.is_file():
            case.gaps.append(f"captured file missing: {rel}")
        else:
            case.captured.append(rel)
            if not check and recorded.get(rel) != sha256(p):
                state = "changed since a task commit recorded it" if rel in recorded else "recorded by no task commit"
                case.gaps.append(f"captured file {state}: {rel}")
    if tc is not None and not case.captured and not any(g.startswith("captured file") for g in case.gaps):
        case.gaps.append("no Captured file — the TC sheet has no data to show")


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


def read_rows(path: Path, max_rows: int) -> tuple[bool, list[list[str]], int]:
    """(is a grid, rows shown, total rows) of a captured file."""
    data = path.read_bytes().decode("utf-8", errors="replace").replace("\x00", "")
    if path.suffix.lower() in (".csv", ".tsv"):
        try:
            rows = list(csv.reader(io.StringIO(data), dialect="excel-tab" if path.suffix.lower() == ".tsv" else "excel"))
            return True, rows[:max_rows], len(rows)
        except csv.Error:
            pass
    lines = data.splitlines()
    return False, [[line] for line in lines[:max_rows]], len(lines)


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
    sh.set(5, 1, "Rendered by ses ut-workbook from the task's evidence/ files; outcomes are those ses coverage "
                 "reads. Rebuild it — never edit it.", NOTE)
    for i, (name, width) in enumerate(SUMMARY_COLS, 1):
        sh.set(HEADER_ROW, i, name, HEADER)
        sh.width(i, width)
    for n, c in enumerate(cases, HEADER_ROW + 1):
        sh.link(n, 1, c.tc, c.tc, "A1", LINK)
        values = [c.id, c.covers, c.type, c.desc or c.plan_desc or f"{c.type}: {c.how}", c.data, c.expected,
                  c.actual, c.outcome, c.mode or "—", c.expected_from or "—", c.evidence or "—",
                  "; ".join(c.notes + [f"gap: {g}" for g in c.gaps]) or "—"]
        for i, v in enumerate(values, 2):
            sh.set(n, i, v or "—", outcome_style(c.outcome) if i == 9 else TEXT)
    sh.freeze_rows = HEADER_ROW
    sh.autofilter = f"A{HEADER_ROW}:{xlsx.col_letter(len(SUMMARY_COLS))}{HEADER_ROW + len(cases)}"
    return sh


def case_sheet(wb: xlsx.Workbook, ws: Path, case: Case, summary_row: int, recorded: dict[str, str],
               texts: dict[str, str], max_rows: int) -> None:
    sh = wb.add_sheet(case.tc)
    sh.width(1, 24)
    sh.width(2, 60)
    for c in range(3, 27):
        sh.width(c, 18)
    sh.link(1, 1, "← Summary", "Summary", f"A{summary_row}", LINK_PLAIN)
    sh.set(2, 1, f"{case.tc} — {case.id}: {case.desc or case.plan_desc or case.how}", TITLE)
    ev = "—"
    if case.evidence:
        ev = f"{case.evidence} — sha256 {sha256(ws / case.evidence)} — " + \
             ("recorded by a task commit" if case.recorded else "NOT recorded by a task commit")
    record = [("Test case", case.tc), ("Test", case.id), ("Covers", case.covers), ("Type", case.type),
              ("How run", case.how), ("Description", case.desc or case.plan_desc or "—"),
              ("Test data", case.data), ("Expected result", case.expected),
              ("Expected from", case.expected_from), ("Actual result", case.actual),
              ("Assertion checked", case.assertion), ("Outcome", case.outcome), ("Mode", case.mode),
              ("Ran", case.date), ("Evidence", ev), ("Notes", "; ".join(case.notes) or "—"),
              ("Gaps", "; ".join(case.gaps) or "none")]
    row = 4
    for key, value in record:
        sh.set(row, 1, key, KEY)
        sh.set(row, 2, value or "—", outcome_style(case.outcome) if key == "Outcome" else TEXT)
        row += 1
    blocks = [(rel, f"Captured {i} of {len(case.captured)}: {rel}") for i, rel in enumerate(case.captured, 1)]
    if not blocks and case.evidence:
        blocks = [(case.evidence, f"Evidence file (this test lists no captured data): {case.evidence}")]
    for rel, title in blocks:
        p = ws / rel
        grid, rows, total = read_rows(p, max_rows)
        state = "recorded" if recorded.get(rel) == sha256(p) else "NOT recorded by a task commit"
        row += 1
        sh.set(row, 1, title, SECTION)
        sh.set(row + 1, 1, f"sha256 {sha256(p)} — {state} — {total} row(s)", NOTE)
        row += 2
        for i, r in enumerate(rows):
            if row >= xlsx.MAX_ROWS - 2:
                break
            if grid:
                sh.row(row, r, GRID_HEAD if i == 0 else GRID)
            else:
                sh.set(row, 1, r[0], MONO)
            row += 1
        if total > len(rows):
            sh.set(row, 1, f"… {total - len(rows)} more row(s) not shown — the full file is {rel}", NOTE)
            row += 1


def build(path: Path, ws: Path, st, cases: list[Case], recorded: dict[str, str], texts: dict[str, str],
          max_rows: int) -> None:
    wb = xlsx.Workbook(f"Unit test results — {st.field('task-id')}")
    summary_sheet(wb, st, cases)
    for n, case in enumerate(cases, HEADER_ROW + 1):
        case_sheet(wb, ws, case, n, recorded, texts, max_rows)
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
        detail = f"{len(c.captured)} captured" + (f"; {len(c.gaps)} gap(s)" if c.gaps else "")
        print(f"  {c.tc:<5} {c.id:<4} {c.outcome:<11} {c.evidence or '—':<34} {detail}")

    code = 0
    if not check:
        out = Path(opts["--out"]) if opts["--out"] else ws / "deliverables" / f"{task}-unit-test-results.xlsx"
        if out.suffix.lower() != ".xlsx":
            print(f"error: --out must end in .xlsx: {out}", file=sys.stderr)
            return 2
        build(out, ws, st, cases, recorded, texts, max_rows)
        print(f"wrote {out} ({1 + len(cases)} sheets, sha256 {sha256(out)})")
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
