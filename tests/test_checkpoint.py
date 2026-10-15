"""Tests for scripts/checkpoint.py (resume classification, evidence trailers, verify)."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
IMPL = """# Implementation Document — T-7

## 2. Implementation steps

| # | Repo | Step | Files / objects | Verification | Rollback |
|---|---|---|---|---|---|
| 1 | repo-a | DDL | src/sql/add_col.sql | compile | drop |
| 2 | repo-a | body | `src/plsql/pkg.pkb`, src/plsql/pkg.pks | utPLSQL | revert |

## 3. Test plan
"""


def run(*args, cwd=None):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, cwd=cwd)


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


class CheckpointTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        for r in ("repo-a", "repo-b"):
            repo = base / r
            git(base, "init", "-q", str(repo))
            git(repo, "config", "user.email", "t@example.com")
            git(repo, "config", "user.name", "t")
            (repo / "README").write_text("x\n")
            git(repo, "add", "-A")
            git(repo, "commit", "-qm", "init")
        self.repo = base / "repo-a"
        subprocess.run(["sh", str(SCRIPTS / "new-task.sh"), "T-7", "auto", "full", str(self.repo),
                        f"{base / 'repo-a'},{base / 'repo-b'}"], check=True, capture_output=True)
        self.ws = base / "work" / "T-7"
        (self.ws / "impl-doc.md").write_text(IMPL)
        git(self.repo, "checkout", "-qb", "feature/T-7")
        run(SCRIPTS / "status.py", "field", self.ws, "branch.repo-a", "feature/T-7")

    def tearDown(self):
        self.tmp.cleanup()

    def cp(self, *args):
        return run(SCRIPTS / "checkpoint.py", *args)

    def commit_step1(self):
        (self.repo / "src" / "sql").mkdir(parents=True)
        (self.repo / "src" / "sql" / "add_col.sql").write_text("alter table t add c number;\n")
        (self.ws / "evidence" / "step1-ddl.txt").write_text("compile ok\n")
        trailer = self.cp("trailer", self.ws, "evidence/step1-ddl.txt").stdout.strip()
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "T-7 step 1: add column", "-m", trailer)
        return trailer

    def test_first_run_is_clean(self):
        r = self.cp("resume", self.ws)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("CLEAN — resume at step 1", r.stdout)

    def test_half_done_step_is_classified_and_needs_decision(self):
        self.commit_step1()
        (self.repo / "src" / "plsql").mkdir()
        (self.repo / "src" / "plsql" / "pkg.pkb").write_text("half\n")
        (self.repo / "notes.txt").write_text("stray\n")
        r = self.cp("resume", self.ws)
        self.assertEqual(r.returncode, 3)
        self.assertIn("expected   src/plsql/pkg.pkb", r.stdout)
        self.assertIn("UNEXPECTED notes.txt", r.stdout)
        self.assertIn("keep and finish step 2", r.stdout)

    def test_clean_after_commit_resumes_next_step(self):
        self.commit_step1()
        r = self.cp("resume", self.ws)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("CLEAN — resume at step 2", r.stdout)

    def test_wrong_branch_checked_out_needs_decision(self):
        git(self.repo, "checkout", "-qb", "other")
        r = self.cp("resume", self.ws)
        self.assertEqual(r.returncode, 3)
        self.assertIn("checked out 'other'", r.stdout)

    def test_trailer_format(self):
        trailer = self.commit_step1()
        self.assertRegex(trailer, r"^Evidence-SHA256: [0-9a-f]{64} evidence/step1-ddl\.txt$")

    def test_verify_passes_then_detects_tamper_and_loss(self):
        self.commit_step1()
        self.assertEqual(self.cp("verify", self.ws).returncode, 0)
        ev = self.ws / "evidence" / "step1-ddl.txt"
        ev.write_text("compile ok (edited later)\n")
        r = self.cp("verify", self.ws)
        self.assertEqual(r.returncode, 1)
        self.assertIn("ALTERED  evidence/step1-ddl.txt", r.stdout)
        ev.unlink()
        self.assertIn("MISSING  evidence/step1-ddl.txt", self.cp("verify", self.ws).stdout)

    def test_unrecorded_evidence_is_a_warning(self):
        self.commit_step1()
        (self.ws / "evidence" / "research-volumes.txt").write_text("n=10\n")
        r = self.cp("verify", self.ws)
        self.assertEqual(r.returncode, 0)
        self.assertIn("research-volumes.txt", r.stdout)

    def test_no_branches_recorded_verify_is_a_noop(self):
        status = self.ws / "STATUS.md"
        status.write_text("\n".join(l for l in status.read_text().splitlines()
                                    if not l.startswith("- branch.")) + "\n")
        r = self.cp("verify", self.ws)
        self.assertEqual(r.returncode, 0)
        self.assertIn("no task branches recorded", r.stdout)


if __name__ == "__main__":
    unittest.main()
