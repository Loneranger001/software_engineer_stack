"""Tests for scripts/coverage.py: TDD §7 row → impl-doc T# → recorded evidence result."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

TDD = """# TDD — T-9

## 7. Verification approach

| Criterion (A#, TS# from the FDD, or G# from /grill) | Test type (unit / integration / regression) | Sketch |
|---|---|---|
| A1 | integration | dev run |
| G2 | unit | pytest |

## 8. Operational impact
"""
IMPL = """# Impl doc — T-9

## 2. Implementation steps

| # | Repo | Step | Files / objects | TDD § | Verify | Rollback |
|---|---|---|---|---|---|---|
| 1 | repo | change | src/x.py | §4 | T1 | revert |

## 3. Test plan

| T# | Covers | Type | How run | Expected |
|---|---|---|---|---|
| T1 | A1 | integration | `awk -F'|' '{print NF}' f \\| sort -u` | 4 |
| T2 | G2, §6 regression | unit | pytest | pass |
"""
ANALYSIS = """# CR-9 — analysis

## Mini scope contract

- **Change**: x
- **Acceptance criteria**:
  - A1 a difference of 0.01 → exit 0
  - A2 a difference of 0.02 → exit 1
- **Rollback**: revert
"""


def results(date, *rows):
    body = "\n".join(f"| {t} | {o} | {m} | — |" for t, o, m in rows)
    return (f"# Test Evidence\n\n- Date: {date}\n\n## Result\n\n"
            f"| Test or criterion | Outcome | Mode | Assertion checked |\n|---|---|---|---|\n{body}\n")


def py(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


class CoverageBase(unittest.TestCase):
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
        git(self.repo, "checkout", "-qb", f"feature/{self.TASK}")
        py(SCRIPTS / "status.py", "field", self.ws, "branch.repo", f"feature/{self.TASK}")
        self.n = 0

    def tearDown(self):
        self.tmp.cleanup()

    def evidence(self, name, text, record=True):
        (self.ws / "evidence" / name).write_text(text)
        if record:
            self.n += 1
            trailer = py(SCRIPTS / "checkpoint.py", "trailer", self.ws, f"evidence/{name}").stdout.strip()
            git(self.repo, "commit", "-q", "--allow-empty", "-m", f"{self.TASK} tests: run {self.n}", "-m", trailer)

    def coverage(self):
        return py(SCRIPTS / "coverage.py", self.ws)


class FullPipelineTest(CoverageBase):
    def setUp(self):
        super().setUp()
        (self.ws / "tdd.md").write_text(TDD)
        (self.ws / "impl-doc.md").write_text(IMPL)

    def test_not_run_is_not_met(self):
        self.evidence("tests-20261105.txt", results("2026-11-05T05:00Z", ("T1", "PASS", "live"),
                                                   ("T2", "NOT RUN — needs dev DB", "—")))
        r = self.coverage()
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertRegex(r.stdout, r"A1\s+PASS")
        self.assertRegex(r.stdout, r"G2\s+NOT-RUN")
        self.assertIn("NOT MET: G2", r.stdout)

    def test_all_pass_is_met(self):
        self.evidence("tests-20261105.txt", results("2026-11-05T05:00Z", ("T1", "PASS", "live"),
                                                   ("T2", "PASS", "live")))
        r = self.coverage()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("2 PASS, 0 WAIVED, 0 not met", r.stdout)

    def test_static_fallback_pass_is_partial(self):
        self.evidence("tests-20261105.txt", results("2026-11-05T05:00Z", ("T1", "PASS", "static-fallback"),
                                                   ("T2", "PASS", "live")))
        r = self.coverage()
        self.assertEqual(r.returncode, 3)
        self.assertRegex(r.stdout, r"A1\s+PARTIAL")

    def test_unrecorded_or_altered_evidence_does_not_count(self):
        self.evidence("tests-20261105.txt", results("2026-11-05T05:00Z", ("T1", "PASS", "live"),
                                                   ("T2", "PASS", "live")), record=False)
        r = self.coverage()
        self.assertEqual(r.returncode, 3)
        self.assertRegex(r.stdout, r"A1\s+UNRECORDED")
        self.evidence("tests-20261106.txt", results("2026-11-06T05:00Z", ("T1", "PASS", "live"),
                                                   ("T2", "PASS", "live")))
        self.assertEqual(self.coverage().returncode, 0)
        (self.ws / "evidence" / "tests-20261106.txt").write_text(
            results("2026-11-06T05:00Z", ("T1", "PASS", "live"), ("T2", "PASS", "live")) + "edited\n")
        self.assertEqual(self.coverage().returncode, 3)

    def test_latest_result_wins_by_date(self):
        self.evidence("tests-b.txt", results("2026-11-05T05:00Z", ("T1", "FAIL", "live"), ("T2", "PASS", "live")))
        self.evidence("tests-a.txt", results("2026-11-06T05:00Z", ("T1", "PASS", "live")))
        r = self.coverage()
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_row_without_a_test_is_no_test(self):
        (self.ws / "impl-doc.md").write_text(IMPL.replace("| T2 | G2, §6 regression |", "| T2 | §6 regression |"))
        self.evidence("tests-20261105.txt", results("2026-11-05T05:00Z", ("T1", "PASS", "live"),
                                                   ("T2", "PASS", "live")))
        r = self.coverage()
        self.assertEqual(r.returncode, 3)
        self.assertRegex(r.stdout, r"G2\s+NO-TEST\s+no T# in impl-doc §3 covers it")

    def test_waiver_meets_the_gate_and_is_listed(self):
        self.evidence("tests-20261105.txt", results("2026-11-05T05:00Z", ("T1", "PASS", "live"),
                                                   ("T2", "NOT-RUN", "—")))
        py(SCRIPTS / "status.py", "field", self.ws, "waiver.G2", "by asif 2026-11-05: verify at UAT")
        r = self.coverage()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertRegex(r.stdout, r"G2\s+WAIVED\s+was NOT-RUN")
        self.assertIn("waived (release note: not verified): G2", r.stdout)

    def test_missing_tdd_is_an_error(self):
        (self.ws / "tdd.md").unlink()
        r = self.coverage()
        self.assertEqual(r.returncode, 1)
        self.assertIn("no tdd.md", r.stderr)


class ChangeRequestTest(CoverageBase):
    PIPELINE = "change-request"
    TASK = "CR-9"

    def test_criteria_are_read_from_the_mini_contract(self):
        (self.ws / "analysis.md").write_text(ANALYSIS)
        self.evidence("cr-reconcile.txt", results("2026-11-05T05:00Z", ("A1", "PASS", "live")))
        r = self.coverage()
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("2 row(s)", r.stdout)
        self.assertRegex(r.stdout, r"A2\s+NO-RESULT")
        self.evidence("cr-reconcile-2.txt", results("2026-11-05T06:00Z", ("A2", "PASS", "live")))
        self.assertEqual(self.coverage().returncode, 0)


class OtherPipelineTest(CoverageBase):
    PIPELINE = "document"
    TASK = "D-9"

    def test_nothing_to_cover(self):
        r = self.coverage()
        self.assertEqual(r.returncode, 0)
        self.assertIn("no acceptance rows", r.stdout)


if __name__ == "__main__":
    unittest.main()
