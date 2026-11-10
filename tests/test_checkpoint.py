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

    def test_subject_fits_the_commit_msg_hook_and_resume_reads_it(self):
        self.assertEqual(self.cp("subject", self.ws, "repo-a", "1", "add column").stdout.strip(),
                         "T-7 step 1: add column")        # no hook: the plain form
        hook = self.repo / ".git" / "hooks" / "commit-msg"
        hook.write_text("#!/bin/sh\nhead -1 \"$1\" | grep -Eq '^[A-Z][A-Z0-9]*-[0-9]+: .{5,}' || "
                        "{ echo 'subject must match <KEY>: <text>' >&2; exit 1; }\n")
        hook.chmod(0o755)
        r = self.cp("subject", self.ws, "repo-a", "1", "add column")
        self.assertEqual(r.returncode, 0, r.stderr)
        subject = r.stdout.strip()
        self.assertEqual(subject, "T-7: step 1: add column")
        self.assertEqual(self.cp("subject", self.ws, "repo-a", "tests", "test plan").stdout.strip(),
                         "T-7: tests: test plan")
        (self.repo / "a.sql").write_text("x\n")
        (self.ws / "evidence" / "step1-ddl.txt").write_text("ok\n")
        trailer = self.cp("trailer", self.ws, "evidence/step1-ddl.txt").stdout.strip()
        git(self.repo, "add", "a.sql")
        git(self.repo, "commit", "-qm", subject, "-m", trailer)   # the hook accepts it
        self.assertIn("last checkpoint commit is step 1", self.cp("resume", self.ws).stdout)

    def test_subject_asks_when_the_hook_rejects_every_form(self):
        hook = self.repo / ".git" / "hooks" / "commit-msg"
        hook.write_text("#!/bin/sh\necho 'subject must start with [JIRA-1]' >&2; exit 1\n")
        hook.chmod(0o755)
        r = self.cp("subject", self.ws, "repo-a", "2", "body")
        self.assertEqual(r.returncode, 3)
        self.assertIn("ASK THE USER", r.stderr)
        self.assertIn("must start with [JIRA-1]", r.stderr)

    def test_resume_ignores_verification_byproducts(self):
        self.commit_step1()
        (self.repo / "src" / "__pycache__").mkdir()
        (self.repo / "src" / "__pycache__" / "x.cpython-313.pyc").write_bytes(b"\0")
        (self.repo / ".pytest_cache").mkdir()
        (self.repo / ".pytest_cache" / "v").write_text("x\n")
        r = self.cp("resume", self.ws)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("(2 verification by-product(s) ignored)", r.stdout)

    def test_trailer_prefix_takes_every_file_of_the_step(self):
        (self.ws / "evidence" / "raw").mkdir()
        for name in ("evidence/step4-x.txt", "evidence/raw/step4-a.log", "evidence/raw/step4-b.log",
                     "evidence/raw/step5-c.log"):
            (self.ws / name).write_text(name + "\n")
        out = self.cp("trailer", self.ws, "--prefix", "step4-").stdout
        self.assertEqual(out.count("Evidence-SHA256:"), 3)
        self.assertNotIn("step5-c.log", out)
        self.assertEqual(self.cp("trailer", self.ws, "--prefix", "step9-").returncode, 1)

    def test_seal_hashes_cited_design_evidence_and_verify_checks_it(self):
        (self.ws / "evidence" / "raw").mkdir()
        (self.ws / "evidence" / "research-probe.txt").write_text("207000 duplicates\n")
        (self.ws / "evidence" / "raw" / "research-probe.log").write_text("raw\n")
        (self.ws / "tdd.md").write_text("Rerun duplicates lines (`evidence/research-probe`).\n")
        r = self.cp("seal", self.ws)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("sealed 2 new file(s)", r.stdout)
        self.assertIn("evidence-seal:", (self.ws / "STATUS.md").read_text())
        self.assertIn("2 sealed design evidence file(s)", self.cp("verify", self.ws).stdout)
        (self.ws / "evidence" / "research-probe.txt").write_text("edited\n")
        r = self.cp("verify", self.ws)
        self.assertEqual(r.returncode, 1)
        self.assertIn("ALTERED  evidence/research-probe.txt (sealed design evidence", r.stdout)
        self.assertEqual(self.cp("seal", self.ws).returncode, 1)   # an altered file is never re-sealed

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

    def test_verify_ignores_other_tasks_trailers_inherited_from_mainline(self):
        # an earlier task's checkpoint commit, merged to mainline before this branch was cut
        git(self.repo, "checkout", "-q", "-")
        (self.repo / "old.sql").write_text("x\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "T-1 step 1: old work",
            "-m", "Evidence-SHA256: " + "0" * 64 + " evidence/step1-old.txt")
        git(self.repo, "checkout", "-q", "feature/T-7")
        git(self.repo, "merge", "-q", "--ff-only", "-")
        self.commit_step1()
        r = self.cp("verify", self.ws)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("1 recorded evidence file(s), 0 problem(s)", r.stdout)
        self.assertNotIn("step1-old", r.stdout)

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


class WorkspaceStaysOutOfGitTest(unittest.TestCase):
    """A standalone repo keeps work/ inside itself — it must never reach a commit."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "solo"
        git(Path(self.tmp.name), "init", "-q", str(self.repo))
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "t")
        (self.repo / "README").write_text("x\n")
        git(self.repo, "add", "README")
        git(self.repo, "commit", "-qm", "init")
        r = subprocess.run(["sh", str(SCRIPTS / "new-task.sh"), "S-1", "auto", "full", str(self.repo)],
                           capture_output=True, text=True, check=True)
        self.assertIn("kept out of git", r.stdout)
        self.ws = self.repo / "work" / "S-1"
        git(self.repo, "checkout", "-qb", "feature/S-1")
        run(SCRIPTS / "status.py", "field", self.ws, "branch.solo", "feature/S-1")
        (self.ws / "evidence" / "step1.txt").write_text("ok\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_new_task_excludes_work_locally(self):
        status = subprocess.run(["git", "-C", str(self.repo), "status", "--porcelain", "-uall"],
                                capture_output=True, text=True).stdout
        self.assertEqual(status, "")
        self.assertIn("/work/", (self.repo / ".git" / "info" / "exclude").read_text())
        self.assertFalse((self.repo / ".gitignore").exists())   # the team's file is left alone

    def test_trailer_refuses_staged_workspace_files(self):
        git(self.repo, "add", "-f", "work/S-1/evidence/step1.txt")
        r = run(SCRIPTS / "checkpoint.py", "trailer", self.ws, "evidence/step1.txt")
        self.assertEqual(r.returncode, 1)
        self.assertIn("workspace files are staged", r.stderr)

    def test_verify_fails_when_workspace_reaches_a_branch(self):
        git(self.repo, "add", "-f", "work/S-1/STATUS.md")
        git(self.repo, "commit", "-qm", "S-1 step 1: oops")
        r = run(SCRIPTS / "checkpoint.py", "verify", self.ws)
        self.assertEqual(r.returncode, 1)
        self.assertIn("IN GIT   solo:work/S-1/STATUS.md", r.stdout)


if __name__ == "__main__":
    unittest.main()
