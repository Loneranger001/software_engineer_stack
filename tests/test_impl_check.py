"""Tests for scripts/impl_check.py: an impl doc names every file it runs, and every row is planned."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

TDD = """# TDD

## 7. Verification approach

| Criterion | Test type | Sketch |
|---|---|---|
| A1 | unit | x |
| G2 | integration | y |
"""
IMPL = """# Impl doc — T-3

## 2. Implementation steps

| # | Repo | Step | Files / objects | TDD § | Verify | Rollback |
|---|---|---|---|---|---|---|
| 1 | repo | schema | ddl/t.sql, deploy/rollback/T-3.sql | §5 | compile | `@deploy/rollback/T-3.sql` |
| 2 | repo | body | src/p.pkb, test/t_p.sql | §4 | T1 | git revert |

## 3. Test plan

| T# | Covers | Type | How run | Expected |
|---|---|---|---|---|
| T1 | A1 | unit | `cd deploy && sqlplus @run_tests.sql` | PASS lines |
| T2 | G2 | integration | `sqlplus @test/t_view.sql` | 7 columns |

## 4. Deployment

| # | Env | Command / action | Verify |
|---|---|---|---|
| 1 | dev | `sqlplus @deploy/release/T-3.sql` | INVALID=0 |

## 5. Rollback (whole change)

1. repo: `@deploy/rollback/T-3.sql`
"""


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


class ImplCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.repo = base / "repo"
        git(base, "init", "-q", "-b", "main", str(self.repo))
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "t")
        (self.repo / "deploy").mkdir()
        (self.repo / "deploy" / "run_tests.sql").write_text("@@../test/t_p.sql\n")   # exists at base
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        subprocess.run(["sh", str(SCRIPTS / "new-task.sh"), "T-3", "auto", "full", str(self.repo)],
                       check=True, capture_output=True)
        self.ws = self.repo / "work" / "T-3"
        (self.ws / "tdd.md").write_text(TDD)

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, impl):
        (self.ws / "impl-doc.md").write_text(impl)
        return subprocess.run([sys.executable, str(SCRIPTS / "impl_check.py"), str(self.ws)],
                              capture_output=True, text=True)

    def test_files_no_step_creates_are_found(self):
        # the trial's gap: T2's test file and the release script are written by no step
        r = self.check(IMPL)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("§3 T2 names test/t_view.sql", r.stdout)
        self.assertIn("§4 names deploy/release/T-3.sql", r.stdout)
        self.assertNotIn("run_tests.sql", r.stdout)          # exists at base, run from deploy/
        self.assertNotIn("rollback/T-3.sql", r.stdout)       # step 1 writes it

    def test_complete_plan_passes(self):
        fixed = IMPL.replace("src/p.pkb, test/t_p.sql", "src/p.pkb, test/t_p.sql, test/t_view.sql, deploy/release/T-3.sql")
        r = self.check(fixed)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("2 §7 row(s) planned", r.stdout)

    def test_step_without_its_own_rollback_and_unknown_repo(self):
        bad = IMPL.replace("| T1 | git revert |", "| T1 | — |").replace("| 2 | repo |", "| 2 | other-repo |")
        r = self.check(bad)
        self.assertEqual(r.returncode, 3)
        self.assertIn("step 2: no Rollback of its own", r.stdout)
        self.assertIn("step 2: 'other-repo' is not a repo of this task", r.stdout)

    def test_unplanned_row_and_workspace_tooling(self):
        bad = IMPL.replace("| T2 | G2 | integration | `sqlplus @test/t_view.sql` |",
                           "| T2 | §6 | integration | `ksh <ws>/evidence/tools/probe.ksh` |")
        r = self.check(bad)
        self.assertEqual(r.returncode, 3)
        self.assertIn("G2: no §3 T# covers it", r.stdout)
        self.assertIn("warning: WORKSPACE T2", r.stdout)


if __name__ == "__main__":
    unittest.main()
