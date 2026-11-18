"""Tests for scripts/ut_workbook.py (`ses ut-workbook`) and the stdlib XLSX writer it uses."""
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}

IMPL = """# Impl doc — T-9

## 3. Test plan

| T# | Covers | Type | Test data | How run | Expected |
|---|---|---|---|---|---|
| T1 | A1 | unit | fixture seed.sql: 3 accounts | utPLSQL ut.run('ut_bal') | 1 row ACC-2 |
| T2 | A2, G1 | integration | 2 equal accounts | pytest tests/test_rec.py | no rows |
"""
TDD = """# TDD — T-9

## 7. Verification approach

| Criterion | Test type | Sketch |
|---|---|---|
| A1 | unit | x |
| A2 | unit | y |
| G1 | unit | z |
"""
ANALYSIS = """# CR-9 — analysis

## Mini scope contract

- **Change**: x
- **Acceptance criteria**:
  - A1 a difference of 0.01 → exit 0
  - A2 a difference of 0.02 → exit 1
- **Rollback**: revert
"""


def evidence(rows, cases, date="2026-11-16T10:00Z"):
    res = "\n".join(f"| {t} | {o} | live | hand-derived | {a} |" for t, o, a in rows)
    tc = "\n".join("| " + " | ".join(c) + " |" for c in cases)
    return (f"# Test Evidence\n\n- Date: {date}\n\n## Result\n\n"
            "| Test or criterion | Outcome | Mode | Expected from | Assertion checked |\n"
            f"|---|---|---|---|---|\n{res}\n\n## Test cases\n\n"
            "| Test | Description | Test data | Expected result | Actual result | Captured |\n"
            f"|---|---|---|---|---|---|\n{tc}\n")


def py(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def sheets(path, styles=False):
    """{sheet name: (cell texts by ref, hyperlink locations by ref)} read straight from the XML;
    with styles, (texts, links, style index by ref, external link targets by ref)."""
    with zipfile.ZipFile(path) as z:
        wb = ElementTree.fromstring(z.read("xl/workbook.xml"))
        names = [s.get("name") for s in wb.find("m:sheets", NS)]
        out = {}
        for i, name in enumerate(names, 1):
            root = ElementTree.fromstring(z.read(f"xl/worksheets/sheet{i}.xml"))
            cells = {c.get("r"): "".join(t.text or "" for t in c.iter(f"{{{NS['m']}}}t"))
                     for c in root.iter(f"{{{NS['m']}}}c")}
            links = {h.get("ref"): h.get("location") for h in root.iter(f"{{{NS['m']}}}hyperlink") if h.get("location")}
            if not styles:
                out[name] = (cells, links)
                continue
            style = {c.get("r"): int(c.get("s", 0)) for c in root.iter(f"{{{NS['m']}}}c")}
            rid = f"{{{NS['r']}}}id"
            ids = {h.get("ref"): h.get(rid) for h in root.iter(f"{{{NS['m']}}}hyperlink") if h.get(rid)}
            rels = f"xl/worksheets/_rels/sheet{i}.xml.rels"
            targets = {}
            if ids:
                rel = {r.get("Id"): (r.get("Target"), r.get("TargetMode")) for r in ElementTree.fromstring(z.read(rels))}
                targets = {ref: rel[i] for ref, i in ids.items()}
            out[name] = (cells, links, style, targets)
        return out


def find(cells, text):
    """The ref of the first cell whose text is exactly `text`."""
    return next(r for r, v in sorted(cells.items(), key=lambda kv: (int(re.sub(r"\D", "", kv[0])), kv[0]))
                if v == text)


class WorkbookBase(unittest.TestCase):
    PIPELINE = "full"
    TASK = "T-9"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.repo = base / "repo"
        git(base, "init", "-q", "-b", "main", str(self.repo))
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "t")
        (self.repo / "README").write_text("x\n")
        git(self.repo, "add", "README")
        git(self.repo, "commit", "-qm", "init")
        subprocess.run(["sh", str(SCRIPTS / "new-task.sh"), self.TASK, "auto", self.PIPELINE, str(self.repo)],
                       check=True, capture_output=True)
        self.ws = self.repo / "work" / self.TASK
        self.ev = self.ws / "evidence"
        git(self.repo, "checkout", "-qb", f"feature/{self.TASK}")
        py(SCRIPTS / "status.py", "field", self.ws, "branch.repo", f"feature/{self.TASK}")
        py(SCRIPTS / "status.py", "field", self.ws, "ses-version", "0.17.0")
        self.out = self.ws / "deliverables" / f"{self.TASK}-unit-test-results.xlsx"

    def tearDown(self):
        self.tmp.cleanup()

    def capture(self, name, text, ext="csv"):
        r = subprocess.run(["sh", str(SCRIPTS / "capture.sh"), str(self.ev), name, "--ext", ext, "--",
                            "printf", "%s", text], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return f"evidence/raw/{name}.{ext}"

    def commit(self, *files):
        trailer = py(SCRIPTS / "checkpoint.py", "trailer", self.ws, *files)
        self.assertEqual(trailer.returncode, 0, trailer.stderr)
        git(self.repo, "commit", "-q", "--allow-empty", "-m", f"{self.TASK} tests: test plan", "-m",
            trailer.stdout.strip())

    def ut(self, *args):
        return py(SCRIPTS / "ut_workbook.py", self.ws, *args)


class FullPipelineTest(WorkbookBase):
    def setUp(self):
        super().setUp()
        (self.ws / "impl-doc.md").write_text(IMPL)
        (self.ws / "tdd.md").write_text(TDD)
        self.t1 = self.capture("tests-2026-11-16-T1-actual", "ACCOUNT,DIFF\nACC-2,0.01\n")
        self.t2 = self.capture("tests-2026-11-16-T2-run", "1 passed\n", ext="log")

    def complete(self):
        (self.ev / "tests-2026-11-16.txt").write_text(evidence(
            [("T1", "PASS", "1 row"), ("T2", "PASS", "pytest 1 passed")],
            [("T1", "a 0.01 difference is reported", "seed.sql: 3 accounts", "1 row: ACC-2, 0.01",
              "1 row: ACC-2, 0.01", self.t1),
             ("T2", "equal balances report nothing", "2 equal accounts", "no rows", "no rows", self.t2)]))

    def test_check_passes_on_complete_uncommitted_evidence(self):
        self.complete()
        r = self.ut("--check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertRegex(r.stdout, r"TC1\s+T1\s+PASS")
        self.assertFalse(self.out.exists(), "--check writes nothing")

    def test_check_lists_every_gap(self):
        (self.ev / "tests-2026-11-16.txt").write_text(evidence(
            [("T1", "PASS", "1 row")],
            [("T1", "x", "", "1 row", "pass", "evidence/raw/nope.csv, evidence/../STATUS.md")]))
        r = self.ut("--check")
        self.assertEqual(r.returncode, 3, r.stdout)
        out = r.stdout
        self.assertIn("TC1 (T1): no Test data", out)
        self.assertIn("Actual result says only 'pass'", out)
        self.assertIn("captured file missing: evidence/raw/nope.csv", out)
        self.assertIn("captured file outside evidence/", out)
        self.assertIn("TC2 (T2): no result in evidence/", out)

    def test_build_renders_summary_linked_to_tc_sheets(self):
        self.complete()
        self.commit("evidence/tests-2026-11-16.txt", self.t1, self.t2)
        r = self.ut()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        wb = sheets(self.out)
        self.assertEqual(list(wb), ["Summary", "TC1", "TC2", "Evidence"])
        cells, links = wb["Summary"]
        header = [cells[f"{c}7"] for c in "ABCDEFGHIJ"]
        self.assertEqual(header, ["TC", "Test", "Covers", "Type", "Description", "Test data", "Expected result",
                                  "Actual result", "Data check", "Outcome"])
        self.assertEqual((cells["A8"], cells["B8"], cells["F8"], cells["H8"], cells["J8"]),
                         ("TC1", "T1", "seed.sql: 3 accounts", "1 row: ACC-2, 0.01", "PASS"))
        self.assertEqual(links, {"A8": "'TC1'!A1", "A9": "'TC2'!A1"})
        tc1, back = wb["TC1"]
        self.assertEqual(back, {"A1": "'Summary'!A8", "B1": "'Evidence'!A1"})
        values = set(tc1.values())
        self.assertTrue({"ACCOUNT", "DIFF", "ACC-2", "0.01"} <= values, "the CSV is laid out in cells")
        self.assertIn("1 passed", set(wb["TC2"][0].values()), "a log is one line per row")
        ev = wb["Evidence"][0]
        self.assertIn(self.t1, ev.values())
        self.assertEqual(ev[find(ev, self.t1).replace("D", "F")], "yes", "its hash is in a task commit")

    def test_outcome_is_the_gates_unrecorded_until_committed(self):
        self.complete()
        r = self.ut()
        self.assertRegex(r.stdout, r"TC1\s+T1\s+UNRECORDED")
        self.assertIn("captured file recorded by no task commit", r.stdout)
        self.assertEqual(r.returncode, 3)
        self.assertEqual(sheets(self.out)["Summary"][0]["J8"], "UNRECORDED")

    def test_same_evidence_same_bytes(self):
        self.complete()
        self.commit("evidence/tests-2026-11-16.txt", self.t1, self.t2)
        other = Path(self.tmp.name) / "again.xlsx"
        self.assertEqual(self.ut().returncode, 0)
        self.assertEqual(self.ut("--out", other).returncode, 0)
        self.assertEqual(self.out.read_bytes(), other.read_bytes())

    def test_latest_result_and_its_test_cases_row_win(self):
        self.complete()
        self.commit("evidence/tests-2026-11-16.txt", self.t1, self.t2)
        t1b = self.capture("tests-2026-11-17-T1-actual", "ACCOUNT,DIFF\nACC-9,0.02\n")
        (self.ev / "tests-2026-11-17.txt").write_text(evidence(
            [("T1", "FAIL", "1 row, wrong account")],
            [("T1", "rerun", "seed.sql", "1 row: ACC-2, 0.01", "1 row: ACC-9, 0.02", t1b)],
            date="2026-11-17T10:00Z"))
        self.commit("evidence/tests-2026-11-17.txt", t1b)
        self.ut()
        wb = sheets(self.out)
        self.assertEqual((wb["Summary"][0]["J8"], wb["Summary"][0]["H8"]), ("FAIL", "1 row: ACC-9, 0.02"))
        self.assertIn("ACC-9", set(wb["TC1"][0].values()))
        self.assertIn("evidence/tests-2026-11-17.txt", set(wb["Evidence"][0].values()))

    def test_waiver_of_a_covered_row_is_noted(self):
        self.complete()
        self.commit("evidence/tests-2026-11-16.txt", self.t1, self.t2)
        py(SCRIPTS / "status.py", "field", self.ws, "waiver.G1", "by asif 2026-11-16: UAT")
        self.ut()
        self.assertIn("G1 waived by asif 2026-11-16: UAT", sheets(self.out)["Summary"][0]["M9"])

    def test_long_capture_is_cut_and_named(self):
        big = self.capture("tests-2026-11-16-T1-big", "".join(f"line {i}\n" for i in range(50)), ext="log")
        (self.ev / "tests-2026-11-16.txt").write_text(evidence(
            [("T1", "PASS", "1 row"), ("T2", "PASS", "ok")],
            [("T1", "x", "seed", "1 row", "1 row", big), ("T2", "y", "seed", "no rows", "no rows", self.t2)]))
        self.ut("--max-rows", "10")
        cells, _l, _s, targets = sheets(self.out, styles=True)["TC1"]
        values = list(cells.values())
        self.assertIn("line 9", values)
        self.assertNotIn("line 10", values)
        self.assertTrue(any("40 more row(s) not shown" in v for v in values))
        self.assertIn(("../evidence/raw/tests-2026-11-16-T1-big.log", "External"), targets.values(),
                      "the rest is a link to the full file")

    def test_control_characters_never_break_the_xml(self):
        dirty = self.capture("tests-2026-11-16-T1-dirty", "\x1b[32mok\x1b[0m\x07 done\n", ext="log")
        (self.ev / "tests-2026-11-16.txt").write_text(evidence(
            [("T1", "PASS", "1 row"), ("T2", "PASS", "ok")],
            [("T1", "x", "seed", "1 row", "1 row", dirty), ("T2", "y", "seed", "no rows", "no rows", self.t2)]))
        self.assertNotEqual(self.ut().returncode, 1)
        self.assertIn("ok done", sheets(self.out)["TC1"][0].values())

    def test_legacy_task_lists_gaps_without_failing(self):
        py(SCRIPTS / "status.py", "field", self.ws, "ses-version", "0.16.0")
        (self.ev / "tests-2026-11-16.txt").write_text(
            "# Test Evidence\n\n- Date: 2026-11-16T10:00Z\n\n## Result\n\n"
            "| Test or criterion | Outcome | Mode | Expected from | Assertion checked |\n|---|---|---|---|---|\n"
            "| T1 | PASS | live | fixture | 1 row |\n| T2 | PASS | live | fixture | 0 rows |\n")
        r = self.ut()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("a task begun before 0.17.0", r.stdout)
        cells = sheets(self.out)["Summary"][0]
        self.assertEqual(cells["F8"], "fixture seed.sql: 3 accounts (planned)")
        self.assertEqual(cells["H8"], "1 row (assertion checked)")

    def check_case(self, check, captured, outcome="PASS"):
        """T1 with the given Check and Captured cells (T2 complete), as the evidence file."""
        (self.ev / "tests-2026-11-16.txt").write_text(evidence(
            [("T1", outcome, "3 rows"), ("T2", "PASS", "ok")],
            [("T1", "costs", "seed", "as in the expected table", "3 rows", captured),
             ("T2", "y", "seed", "no rows", "no rows", self.t2)]).replace(
            "| Actual result | Captured |", "| Actual result | Check | Captured |").replace(
            "|---|---|---|---|---|---|\n", "|---|---|---|---|---|---|---|\n").replace(
            f"| 3 rows | {captured} |", f"| 3 rows | {check} | {captured} |").replace(
            f"| no rows | {self.t2} |", f"| no rows | | {self.t2} |"))

    def test_check_highlights_fields_and_colours_values(self):
        sys.path.insert(0, str(SCRIPTS))
        import xlsx
        before = self.capture("tests-2026-11-16-T1-data", "ITEM,STATUS\n100,N\n200,N\n")
        after = self.capture("tests-2026-11-16-T1-actual", "ITEM,STATUS,COST\n100,P,10.5\n200,N,.5\n")
        self.check_case("STATUS=P, COST", f"Items before: {before}, Items after: {after}")
        r = self.ut("--check")
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertIn("contradicts the recorded PASS: 1 checked value(s) differ", r.stdout)
        self.ut()
        cells, _links, style, _t = sheets(self.out, styles=True)["TC1"]
        self.assertIn("Items before", cells.values())        # the label names the block
        headings = {style[ref] for ref, v in cells.items() if v == "STATUS"} - {xlsx.GRID}   # not the Differences row
        self.assertEqual(headings, {xlsx.GRID_HEAD, xlsx.CHECK_HEAD}, "the input table is shown, never checked")
        self.assertIn(xlsx.GOOD, [style[ref] for ref, v in cells.items() if v == "P"])
        self.assertIn(xlsx.BAD, [style[ref] for ref, v in cells.items() if v == "N"])
        self.assertEqual(style[find(cells, "10.5")], xlsx.EYE, "a field named without a value is checked by eye")
        self.assertIn("Differences (1)", cells.values())
        summary = sheets(self.out)["Summary"][0]
        self.assertEqual(summary["I8"], "1 of 2 checked value(s) differ; 2 value(s) to check by eye")

    def test_expected_table_matches_rows_on_its_other_columns(self):
        sys.path.insert(0, str(SCRIPTS))
        import xlsx
        log = ("\nITEM       LOC        UNIT_COST\n---------- ---------- ---------\n"
               "100        1               10.5\n100        2               10.4\n\n"
               "ITEM       LOC        UNIT_COST\n---------- ---------- ---------\n"
               "300        1                  1\n\n3 rows selected.\n")
        actual = self.capture("tests-2026-11-16-T1-actual", log, ext="log")
        expected = self.capture("tests-2026-11-16-T1-expected", "ITEM,LOC,UNIT_COST\n100,2,10.40\n100,1,10.50\n200,1,.5\n")
        self.check_case("UNIT_COST", f"{actual}, {expected}", outcome="FAIL")
        self.assertEqual(self.ut("--check").returncode, 0, "a FAIL that the data confirms is no gap")
        self.ut()
        cells, _l, style, _t = sheets(self.out, styles=True)["TC1"]
        self.assertEqual(style[find(cells, "ITEM")], xlsx.KEY_HEAD)
        self.assertEqual(style[find(cells, "10.4")], xlsx.GOOD, "matched on ITEM and LOC, not on position")
        self.assertEqual(style[find(cells, "10.5")], xlsx.GOOD)
        self.assertEqual(style[find(cells, "1")], xlsx.GRID)     # the LOC of the first row: a key, not checked
        self.assertIn("3 rows selected.", cells.values(), "text after the table stays text")
        diffs = {v for v in cells.values()}
        self.assertTrue({"ITEM=200, LOC=1", "ITEM=300, LOC=1"} <= diffs, "a missing and an extra row both differ")
        self.assertEqual(sheets(self.out)["Summary"][0]["I8"], "2 of 4 checked value(s) differ")

    def test_check_naming_an_absent_field_is_a_gap(self):
        actual = self.capture("tests-2026-11-16-T1-actual", "ITEM,COST\n1,2\n")
        self.check_case("STATUS=P", actual)
        r = self.ut("--check")
        self.assertEqual(r.returncode, 3)
        self.assertIn("the Check names STATUS, which no captured table has", r.stdout)

    def test_what_cells_cannot_hold_is_linked(self):
        (self.ev / "raw" / "tests-2026-11-16-T1-archive.gz").write_bytes(b"\x1f\x8b\x08\x00binary")
        self.check_case("", "evidence/raw/tests-2026-11-16-T1-archive.gz")
        self.ut()
        cells, _l, _s, targets = sheets(self.out, styles=True)["TC1"]
        self.assertIn("Not shown in cells: it is a binary file.", cells.values())
        self.assertIn(("../evidence/raw/tests-2026-11-16-T1-archive.gz", "External"), targets.values())

    def test_missing_impl_doc_is_an_error(self):
        (self.ws / "impl-doc.md").unlink()
        self.assertEqual(self.ut().returncode, 1)


class ChangeRequestTest(WorkbookBase):
    PIPELINE = "change-request"
    TASK = "CR-9"

    def test_criteria_are_the_test_cases(self):
        (self.ws / "analysis.md").write_text(ANALYSIS)
        a1 = self.capture("cr-A1-actual", "DIFF,EXIT\n0.01,0\n")
        (self.ev / "cr-verify.txt").write_text(evidence(
            [("A1", "PASS", "exit 0")],
            [("A1", "", "1 account, diff 0.01", "exit 0", "exit 0", a1)]))
        self.commit("evidence/cr-verify.txt", a1)
        r = self.ut()
        self.assertEqual(r.returncode, 3, r.stdout)          # A2 has no result
        wb = sheets(self.out)
        self.assertEqual(list(wb), ["Summary", "TC1", "TC2", "Evidence"])
        cells = wb["Summary"][0]
        self.assertEqual((cells["B8"], cells["E8"], cells["J8"]), ("A1", "a difference of 0.01 → exit 0", "PASS"))
        self.assertEqual(cells["J9"], "NO-RESULT")


class OtherPipelineTest(WorkbookBase):
    PIPELINE = "document"
    TASK = "DOC-9"

    def test_nothing_to_render(self):
        r = self.ut()
        self.assertEqual(r.returncode, 0)
        self.assertIn("runs no tests", r.stdout)


class XlsxWriterTest(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(SCRIPTS))
        import xlsx
        self.xlsx = xlsx

    def test_sheet_names_follow_excel_rules(self):
        wb = self.xlsx.Workbook()
        for bad in ("", "x" * 32, "a/b", "a:b", "'quoted'"):
            with self.assertRaises(ValueError, msg=bad):
                wb.add_sheet(bad)
        wb.add_sheet("TC1")
        with self.assertRaises(ValueError):
            wb.add_sheet("tc1")

    def test_cells_are_text_never_formulas(self):
        wb = self.xlsx.Workbook("t")
        sh = wb.add_sheet("S")
        sh.set(1, 1, "=HYPERLINK(\"http://x\")")
        sh.set(1, 30, "a" * 40000)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "w.xlsx"
            wb.save(out)
            xml = zipfile.ZipFile(out).read("xl/worksheets/sheet1.xml").decode()
        self.assertNotIn("<f>", xml)
        self.assertIn('t="inlineStr"', xml)
        self.assertIn('r="AD1"', xml)
        self.assertLessEqual(max(len(m) for m in re.findall(r">(a+)", xml)), 32767)

    def test_column_letters(self):
        self.assertEqual([self.xlsx.col_letter(n) for n in (1, 26, 27, 52, 703)], ["A", "Z", "AA", "AZ", "AAA"])

    @unittest.skipUnless(__import__("importlib").util.find_spec("openpyxl"), "openpyxl not installed")
    def test_opens_in_openpyxl(self):
        import openpyxl
        wb = self.xlsx.Workbook("t")
        s = wb.add_sheet("Summary")
        s.link(2, 1, "TC1", "TC1")
        s.freeze_rows, s.autofilter = 1, "A1:B2"
        wb.add_sheet("TC1").set(1, 1, "x")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "w.xlsx"
            wb.save(out)
            book = openpyxl.load_workbook(out)
        self.assertEqual(book.sheetnames, ["Summary", "TC1"])
        self.assertEqual(book["Summary"]["A2"].hyperlink.location, "'TC1'!A1")
        self.assertEqual(book["Summary"].freeze_panes, "A2")


class DataTest(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(SCRIPTS))
        import ut_data
        self.d = ut_data

    def test_sqlplus_tables_become_grids(self):
        lines = ["SQL> select ...", "", "NAME                N", "---------- ----------", "a                   1",
                 "bb                 22", "", "NAME                N", "---------- ----------", "c                   3",
                 "", "3 rows selected.",
                 "", "COUNT(*)", "----------", "         7", "Elapsed: 00:00:00.01"]
        blocks = self.d.tables(lines)
        self.assertEqual([b.kind for b in blocks], ["text", "grid", "text", "grid", "text"])
        self.assertEqual(blocks[1].rows, [["NAME", "N"], ["a", "1"], ["bb", "22"], ["c", "3"]], "page break merged")
        self.assertEqual(blocks[3].rows, [["COUNT(*)"], ["7"]])
        self.assertEqual(blocks[4].rows, [["Elapsed: 00:00:00.01"]])

    def test_a_line_that_does_not_fit_ends_the_table(self):
        blocks = self.d.tables(["A    B", "---- ----", "x    y", "a long line of prose", "z    w"])
        self.assertEqual(blocks[0].rows, [["A", "B"], ["x", "y"]])
        self.assertEqual(blocks[1].kind, "text")

    def test_check_syntax(self):
        checks, errors = self.d.parse("STATUS=P; NAME='a, b'; COST ;NOTE='it''s'; GONE=")
        self.assertEqual(errors, [])
        self.assertEqual([(c.column, c.value) for c in checks],
                         [("STATUS", "P"), ("NAME", "a, b"), ("COST", None), ("NOTE", "it's"), ("GONE", "")])
        self.assertTrue(self.d.parse("=x")[1])

    def test_values_compare_as_numbers_text_and_null(self):
        same = self.d.same
        self.assertTrue(same("0.5", ".5") and same("10.50", "10.5") and same("1e3", "1000"))
        self.assertTrue(same("NULL", "") and same("", "(null)"))
        self.assertFalse(same("P", "p") or same("0", "") or same("10.5", "10.4") or same("007", "7 "[:-1] + "x"))

    def test_without_a_check_the_expected_table_is_compared_in_order(self):
        actual = self.d.Captured("Actual", "a", "actual", [self.d.Block("grid", [["A", "B"], ["1", "x"], ["2", "y"]])], 3)
        exp = self.d.Captured("Expected", "e", "expected", [self.d.Block("grid", [["A", "B"], ["1", "x"], ["2", "z"],
                                                                                 ["3", "w"]])], 4)
        res = self.d.compare([actual, exp], [])
        self.assertEqual(res.matched, 3)
        self.assertEqual([(d[1], d[2]) for d in res.differ], [("row 3", "—"), ("row 2", "B")])
        self.assertEqual(res.summary(), ("2 of 5 checked value(s) differ", "FAIL"))


class CaptureExtTest(unittest.TestCase):
    def test_ext_names_the_raw_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            ev = Path(tmp) / "evidence"
            r = subprocess.run(["sh", str(SCRIPTS / "capture.sh"), str(ev), "t1", "--ext", "csv", "--",
                                "printf", "a,b\\n1,2\\n"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual((ev / "raw" / "t1.csv").read_text(), "a,b\n1,2\n")
            self.assertFalse((ev / "raw" / "t1.log").exists())
            bad = subprocess.run(["sh", str(SCRIPTS / "capture.sh"), str(ev), "t2", "--ext", "../x", "--", "true"],
                                 capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)


if __name__ == "__main__":
    unittest.main()
