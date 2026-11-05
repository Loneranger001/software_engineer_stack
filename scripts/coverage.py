#!/usr/bin/env python3
"""coverage.py — is every acceptance row of a task verified? (run as `ses coverage`)

A row is met only by recorded evidence that it passed — not by a test that
was planned, a check that ran in static-fallback mode, or a pending live check
written into a next action. This walks the chain the gates rely on and shows,
row by row, where it stands:

  full pipeline:   TDD §7 row (A#, TS#, G#) → the impl-doc §3 T# whose Covers
                   column names it → that T#'s latest result in evidence/
  change request:  acceptance criterion A# in analysis.md → its latest
                   result in evidence/

In the full pipeline the rows are the UNION of TDD §7, the contract's
acceptance criteria (A#) and an approved FDD's test scenarios (TS#): a
contract or FDD row that never reached §7 is NOT-IN-TDD and not met — no test
plans it, so no T# could prove it.

Usage:
    coverage.py <ws>            the gate: every row → T# → recorded PASS
    coverage.py <ws> --plan     the plan check (/impl-plan): every row reaches §7
                                and has a T#; results are not read

Results come from the result table of each evidence/*.txt file
(templates/test-evidence.md, "## Result"): a table whose header has an
`Outcome` column, one row per test (T#) or criterion (A#), outcome PASS |
FAIL | PARTIAL | NOT-RUN. The latest result wins (the file's `- Date:` line,
then its name). A PASS whose Mode column says static-fallback counts as
PARTIAL: the code parsed, it did not run. A PASS needs an `Expected from`
cell naming where its expected value came from (hand-derived, spec, fixture,
contract…); a PASS without one, or whose expectation was computed by the code
under test, is NO-ORACLE — a test that re-runs the implementation's own logic
agrees with it whether it is right or not. A result counts only from an
evidence file whose hash a task commit recorded (ses checkpoint trailer) and
that still matches it; otherwise the row is UNRECORDED.

A row the user accepts unverified is waived in STATUS.md, never by editing
evidence:   ses status field <ws> waiver.<ID> "by <who> <date>: <reason>"
A waived row is met for the gate and listed, so the release note names it as
not verified.

Exit codes: 0 every row PASS or waived; 3 a row is not met; 1 error (a
document the chain needs is missing); 2 usage.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checkpoint import load, recorded_evidence, sha256  # noqa: E402
from status import StatusError  # noqa: E402

from doctables import ROW_ID, TEST_ID, col, rows_missing_from_tdd, section, tables, tdd_verification_ids  # noqa: E402

NOT_MET = 3
# worst first: a row takes the worst status of its tests
ORDER = ("NOT-IN-TDD", "NO-TEST", "FAIL", "NOT-RUN", "NO-RESULT", "UNRECORDED", "NO-ORACLE", "PARTIAL", "PASS")
# an expectation the code under test produced is no expectation at all
SELF_ORACLE = re.compile(r"\b(code under test|implementation|same (query|sql|function|logic))\b", re.I)


def tdd_rows(ws: Path) -> list[str]:
    if not (ws / "tdd.md").is_file():
        raise StatusError(f"no tdd.md in {ws} — coverage starts from its §7 Verification approach")
    rows = tdd_verification_ids(ws) or []
    if not rows:
        raise StatusError("tdd.md §7 has no rows keyed A#, TS# or G#")
    return rows


def impl_tests(ws: Path) -> dict[str, list[str]]:
    """{row ID: [T#, ...]} from impl-doc §3's T# and Covers columns."""
    doc = ws / "impl-doc.md"
    if not doc.is_file():
        raise StatusError(f"no impl-doc.md in {ws} — its §3 test plan maps rows to T#s (/impl-plan)")
    body = section(doc.read_text(), re.compile(r"test plan", re.I))
    out: dict[str, list[str]] = {}
    for header, trs in tables(body):
        t, c = col(header, "t#"), col(header, "covers")
        if t is None or c is None:
            continue
        for r in trs:
            if max(t, c) >= len(r):
                continue
            for test in TEST_ID.findall(r[t]):
                for rid in ROW_ID.findall(r[c]):
                    out.setdefault(rid, [])
                    if test not in out[rid]:
                        out[rid].append(test)
    return out


def cr_rows(ws: Path) -> list[str]:
    doc = ws / "analysis.md"
    if not doc.is_file():
        raise StatusError(f"no analysis.md in {ws} — its mini contract lists the acceptance criteria")
    rows: list[str] = []
    inside = False
    for line in doc.read_text().splitlines():
        if re.search(r"acceptance criteria", line, re.I):
            inside = True
            continue
        if inside and (re.match(r"^#", line) or re.match(r"^\s?[-*]\s+\*\*", line)):
            break
        if inside:
            m = re.match(r"^\s*(?:[-*]\s+|\|\s*)\**(A\d+)\b", line)
            if m and m.group(1) not in rows:
                rows.append(m.group(1))
    if not rows:
        raise StatusError("analysis.md lists no acceptance criteria A1…An under its mini contract")
    return rows


def results(ws: Path, recorded: dict[str, str]) -> dict[str, tuple[str, str, bool]]:
    """{T# or row ID: (outcome, evidence file, recorded)} — the latest result for each."""
    ev = ws / "evidence"
    files = []
    for f in sorted(ev.glob("*.txt")) if ev.is_dir() else []:
        text = f.read_text(errors="replace")
        m = re.search(r"^- Date:\s*(\S+)", text, re.M)
        files.append((m.group(1) if m else "", f.name, f, text))
    out: dict[str, tuple[str, str, bool]] = {}
    for _date, name, f, text in sorted(files):
        rel = f"evidence/{name}"
        ok = rel in recorded and sha256(f) == recorded[rel]
        for header, trs in tables(text):
            o, mode, exp = col(header, "outcome"), col(header, "mode"), col(header, "expectedfrom")
            if o is None or o == 0:
                continue
            for r in trs:
                if o >= len(r):
                    continue
                m = re.match(r"^[*`\s]*(PASS|FAIL|PARTIAL|NOT[-_ ]RUN)\b", r[o].upper())
                if not m:
                    continue
                outcome = re.sub(r"[-_ ]", "-", m.group(1))
                if outcome == "PASS" and mode is not None and mode < len(r) and "static" in r[mode].lower():
                    outcome = "PARTIAL"
                elif outcome == "PASS":
                    source = r[exp].strip(" `*") if exp is not None and exp < len(r) else ""
                    if source.lower() in ("", "-", "—", "n/a", "none") or SELF_ORACLE.search(source):
                        outcome = "NO-ORACLE"
                for key in TEST_ID.findall(r[0]) + ROW_ID.findall(r[0]):
                    out[key] = (outcome, rel, ok)
    return out


def status_of(res: tuple[str, str, bool] | None) -> str:
    if res is None:
        return "NO-RESULT"
    outcome, _rel, ok = res
    return outcome if ok else "UNRECORDED"


def main(argv: list[str]) -> int:
    plan = "--plan" in argv
    argv = [a for a in argv if a != "--plan"]
    if len(argv) != 1 or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv and argv[0] in ("-h", "--help") else 2
    ws, st = load(argv[0])
    task, pipeline = st.field("task-id"), st.field("pipeline")
    if pipeline not in ("full", "change-request"):
        print(f"coverage {task} ({pipeline}): no acceptance rows to verify in this pipeline")
        return 0
    if plan and pipeline != "full":
        print(f"coverage {task} ({pipeline}): --plan checks a full-pipeline test plan; nothing to plan here")
        return 0
    res = {} if plan else results(ws, recorded_evidence(ws, st))
    missing: dict[str, str] = {}
    if pipeline == "full":
        rows = tdd_rows(ws)
        for rid, source in rows_missing_from_tdd(ws):
            missing[rid] = source
            rows.append(rid)
        tests = impl_tests(ws)
    else:
        rows = cr_rows(ws)
        tests = {}
    lines, unmet, waived = [], [], []
    for rid in rows:
        if rid in missing:
            row, detail = "NOT-IN-TDD", f"{missing[rid]} defines it; tdd.md §7 has no row for it, so no test plans it"
        elif pipeline == "full":
            ts = tests.get(rid, [])
            if plan:
                row = "PLANNED" if ts else "NO-TEST"
                detail = ", ".join(ts) or "no T# in impl-doc §3 covers it"
                if not ts:
                    unmet.append(rid)
                lines.append(f"  {rid:<5} {row:<11} {detail}")
                continue
            parts = [(t, status_of(res.get(t)), res.get(t)) for t in ts]
            row = (min((p[1] for p in parts), key=ORDER.index) if parts else "NO-TEST")
            detail = "; ".join(f"{t} {s}" + (f" ({r[1]})" if r else "") for t, s, r in parts) \
                or "no T# in impl-doc §3 covers it"
        else:
            r = res.get(rid)
            row = status_of(r)
            detail = r[1] if r else "no result in evidence/"
        w = f"waiver.{rid}"
        if plan:
            unmet.append(rid)            # only NOT-IN-TDD reaches here in plan mode
        elif row != "PASS" and w in st.fields:
            waived.append(rid)
            detail = f"was {row}: {detail} — waived {st.field(w)}"
            row = "WAIVED"
        elif row != "PASS":
            unmet.append(rid)
        lines.append(f"  {rid:<5} {row:<11} {detail}")
    if plan:
        print(f"coverage plan {task}: {len(rows)} row(s) — {len(rows) - len(unmet)} planned, "
              f"{len(unmet)} without a test")
        print("\n".join(lines))
        if unmet:
            print(f"NOT PLANNED: {' '.join(unmet)} — give each a TDD §7 row and an impl-doc §3 T# whose "
                  f"Covers column names it")
            return NOT_MET
        return 0
    passed = len(rows) - len(unmet) - len(waived)
    print(f"coverage {task} ({pipeline}): {len(rows)} row(s) — {passed} PASS, {len(waived)} WAIVED, "
          f"{len(unmet)} not met")
    print("\n".join(lines))
    if waived:
        print(f"waived (release note: not verified): {' '.join(waived)}")
    if unmet:
        print(f"NOT MET: {' '.join(unmet)} — run each and record its result in evidence/ (a task commit's "
              f"trailer), or the user waives it: ses status field <ws> waiver.<ID> \"by <who> <date>: <reason>\"")
        if any(rid in missing for rid in unmet):
            print("NOT-IN-TDD rows: amend TDD §7 (and the impl-doc test plan) first — the design never "
                  "planned their verification")
        if any("NO-ORACLE" in l for l in lines):
            print("NO-ORACLE: fill the evidence Result table's `Expected from` cell with where the expected "
                  "value came from (hand-derived, spec, fixture) — never the code under test")
        return NOT_MET
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except StatusError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
