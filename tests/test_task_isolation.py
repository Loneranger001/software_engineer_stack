"""Tests for task isolation: `ses worktree` (one worktree per task branch), and the
`ses checkpoint` checks that keep a task's writes inside its changed repos —
in the layout most users have: a non-git folder holding several repos."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
IMPL = """# Impl doc — T-7

## 2. Implementation steps

| # | Repo | Step | Files / objects | TDD § | Verify | Rollback |
|---|---|---|---|---|---|---|
| 1 | g1 | DDL | src/add_col.sql | §5 | T1 | revert |
| 2 | g1 | body | src/pkg.pkb | §4.1 | T2 | revert |

## 3. Test plan
"""


def py(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True).stdout.strip()


class Layout(unittest.TestCase):
    """f1/ (not a repo) holding g1, g2, each with a bare origin outside f1."""

    PIPELINE = "full"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        top = Path(self.tmp.name)
        self.f1 = top / "f1"
        self.f1.mkdir()
        for r in ("g1", "g2"):
            repo = self.f1 / r
            git(top, "init", "-q", "-b", "main", str(repo))
            git(repo, "config", "user.email", "t@example.com")
            git(repo, "config", "user.name", "t")
            (repo / "README").write_text(f"{r}\n")
            git(repo, "add", "README")
            git(repo, "commit", "-qm", "init")
            git(top, "init", "-q", "--bare", str(top / "origin" / f"{r}.git"))
            git(repo, "remote", "add", "origin", str(top / "origin" / f"{r}.git"))
            git(repo, "push", "-q", "origin", "main")
        self.g1, self.g2 = self.f1 / "g1", self.f1 / "g2"
        subprocess.run(["sh", str(SCRIPTS / "new-task.sh"), "T-7", "auto", self.PIPELINE, str(self.g1),
                        f"{self.g1},{self.g2}"], check=True, capture_output=True)
        self.ws = self.f1 / "work" / "T-7"
        (self.ws / "impl-doc.md").write_text(IMPL)

    def tearDown(self):
        self.tmp.cleanup()

    def wt(self, *args):
        return py(SCRIPTS / "worktree.py", *args)

    def cp(self, *args):
        return py(SCRIPTS / "checkpoint.py", *args)

    def field(self, name):
        return py(SCRIPTS / "status.py", "get", self.ws, name).stdout.strip()

    def commit(self, repo, path, subject, trailer=True):
        f = repo / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(subject + "\n")
        git(repo, "add", path)
        args = ["commit", "-qm", subject]
        if trailer:
            ev = self.ws / "evidence" / (path.replace("/", "_") + ".txt")
            ev.write_text("ok\n")
            args += ["-m", self.cp("trailer", self.ws, f"evidence/{ev.name}").stdout.strip()]
        git(repo, *args)


class WorktreeTest(Layout):
    def test_add_cuts_from_origin_and_leaves_the_users_checkout_alone(self):
        # the user's checkout is on another branch, with unpushed work and an uncommitted edit
        git(self.g1, "checkout", "-qb", "users-own")
        self.commit(self.g1, "mine.txt", "user's unpushed work", trailer=False)
        (self.g1 / "README").write_text("edited, not committed\n")
        r = self.wt("add", self.ws, "g1", "feature/T-7", "--base", "main")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        path = self.ws / "wt" / "g1"
        self.assertEqual(self.field("worktree.g1"), str(path))
        self.assertEqual(self.field("branch.g1"), "feature/T-7")
        self.assertEqual(self.field("base.g1"), "origin/main")
        self.assertEqual(git(path, "rev-parse", "--abbrev-ref", "HEAD"), "feature/T-7")
        self.assertFalse((path / "mine.txt").exists())          # not cut from the checkout
        self.assertEqual(git(self.g1, "rev-parse", "--abbrev-ref", "HEAD"), "users-own")
        self.assertEqual((self.g1 / "README").read_text(), "edited, not committed\n")

    def test_add_needs_a_base_the_user_named(self):
        status = self.ws / "STATUS.md"
        status.write_text(status.read_text().replace("- mainline.g1: main\n", ""))
        r = self.wt("add", self.ws, "g1", "feature/T-7")
        self.assertEqual(r.returncode, 1)
        self.assertIn("ask the user", r.stderr)

    def test_new_task_records_each_mainline_and_add_uses_it(self):
        self.assertEqual(self.field("mainline.g1"), "main")      # from origin, at scaffold time
        self.assertEqual(self.field("mainline.g2"), "main")
        r = self.wt("add", self.ws, "g1", "feature/T-7")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.field("base.g1"), "origin/main")

    def test_search_mainline_resolves_each_repo(self):
        # g2 releases from master: one --ref for all repos used to report it NOT SEARCHED
        git(self.g2, "push", "-q", "origin", "main:master")
        py(SCRIPTS / "status.py", "field", self.ws, "mainline.g2", "master")
        r = py(SCRIPTS / "xsearch.py", "--ws", self.ws, "--ref", "mainline", "--", "g1|g2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("## g1 (origin/main@", r.stdout)
        self.assertIn("## g2 (origin/master@", r.stdout)
        self.assertIn("| g2 | origin/master@", r.stdout)
        self.assertIn("`git -C g2 grep", r.stdout)               # rows name the repo, not its path
        status = self.ws / "STATUS.md"
        status.write_text(status.read_text().replace("- mainline.g2: master\n", ""))
        git(self.g2, "remote", "remove", "origin")
        r = py(SCRIPTS / "xsearch.py", "--ws", self.ws, "--ref", "mainline", "--", "g1")
        self.assertEqual(r.returncode, 1)
        self.assertIn("g2: NOT SEARCHED — no mainline known for g2", r.stdout)

    def test_add_is_idempotent_and_remove_keeps_the_branch(self):
        self.assertEqual(self.wt("add", self.ws, "g1", "feature/T-7", "--base", "main").returncode, 0)
        r = self.wt("add", self.ws, "g1", "feature/T-7")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("reused", r.stdout)
        (self.ws / "wt" / "g1" / "half.txt").write_text("x\n")
        self.assertEqual(self.wt("remove", self.ws, "g1").returncode, 1)   # git refuses: untracked work
        (self.ws / "wt" / "g1" / "half.txt").unlink()
        r = self.wt("remove", self.ws, "g1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.ws / "wt" / "g1").exists())
        self.assertEqual(self.field("branch.g1"), "feature/T-7")
        self.assertNotIn("worktree.g1", py(SCRIPTS / "status.py", "show", self.ws).stdout)
        git(self.g1, "rev-parse", "--verify", "feature/T-7")

    def test_branch_checked_out_elsewhere_is_the_users_call(self):
        git(self.g1, "checkout", "-qb", "feature/T-7")
        r = self.wt("add", self.ws, "g1", "feature/T-7", "--base", "main")
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("ASK THE USER", r.stderr)
        self.assertNotIn("worktree.g1", py(SCRIPTS / "status.py", "show", self.ws).stdout)

    def test_resume_reads_the_worktree_not_the_checkout(self):
        self.wt("add", self.ws, "g1", "feature/T-7", "--base", "main")
        path = self.ws / "wt" / "g1"
        self.commit(path, "src/add_col.sql", "T-7 step 1: add column")
        (self.g1 / "users-scratch.txt").write_text("not the task's\n")   # in the user's checkout
        (path / "src" / "pkg.pkb").write_text("half\n")
        r = self.cp("resume", self.ws)
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertIn("expected   src/pkg.pkb", r.stdout)
        self.assertNotIn("users-scratch.txt", r.stdout)

    def test_list_repos_skips_task_worktrees(self):
        self.wt("add", self.ws, "g1", "feature/T-7", "--base", "main")
        r = subprocess.run(["sh", str(SCRIPTS / "list-repos.sh"), str(self.f1), "--depth", "6"],
                           capture_output=True, text=True)
        self.assertEqual(r.stdout.split(), [str(self.g1), str(self.g2)])


class VerifyScopeTest(Layout):
    def setUp(self):
        super().setUp()
        self.wt("add", self.ws, "g1", "feature/T-7", "--base", "main")
        self.g1wt = self.ws / "wt" / "g1"

    def test_a_task_commit_in_an_analysis_only_repo_fails(self):
        self.commit(self.g1wt, "src/add_col.sql", "T-7 step 1: add column")
        git(self.g2, "checkout", "-qb", "feature/T-7")
        self.commit(self.g2, "loader.py", "T-7 step 3: quick fix in the loader", trailer=False)
        git(self.g2, "checkout", "-q", "main")          # off the checkout, still on a ref
        r = self.cp("verify", self.ws)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("OUT OF SCOPE g2", r.stdout)

    def test_delivery_fails_on_an_empty_branch_and_a_commit_without_evidence(self):
        self.assertEqual(self.cp("verify", self.ws).returncode, 0)
        r = self.cp("verify", self.ws, "--delivery")
        self.assertEqual(r.returncode, 1)
        self.assertIn("EMPTY    g1", r.stdout)
        self.commit(self.g1wt, "src/add_col.sql", "T-7 step 1: add column", trailer=False)
        r = self.cp("verify", self.ws, "--delivery")
        self.assertEqual(r.returncode, 1)
        self.assertIn("NO EVIDENCE g1:", r.stdout)
        self.assertNotIn("EMPTY", r.stdout)
        self.assertEqual(self.cp("verify", self.ws).returncode, 0)   # ordinary verify: hashes only

    def test_delivery_passes_with_evidenced_commits(self):
        self.commit(self.g1wt, "src/add_col.sql", "T-7 step 1: add column")
        r = self.cp("verify", self.ws, "--delivery")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_resume_names_another_tasks_branch(self):
        self.wt("remove", self.ws, "g1")
        git(self.g1, "checkout", "-qb", "feature/OTHER-1")
        other = self.f1 / "work" / "OTHER-1"
        subprocess.run(["sh", str(SCRIPTS / "new-task.sh"), "OTHER-1", "auto", "change-request",
                        str(self.g1)], check=True, capture_output=True)
        py(SCRIPTS / "status.py", "field", other, "branch.g1", "feature/OTHER-1")
        r = self.cp("resume", self.ws)
        self.assertEqual(r.returncode, 3)
        self.assertIn("task OTHER-1's branch", r.stdout)
        self.assertNotIn("switch or re-record", r.stdout)

    def test_resume_after_the_last_step_points_at_the_test_plan(self):
        self.commit(self.g1wt, "src/add_col.sql", "T-7 step 1: add column")
        self.commit(self.g1wt, "src/pkg.pkb", "T-7 step 2: body")
        r = self.cp("resume", self.ws)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("every impl-doc step is committed", r.stdout)


class ChangeRequestOneRepoTest(Layout):
    PIPELINE = "change-request"

    def test_a_second_repo_is_the_escalation_rule(self):
        self.assertEqual(self.wt("add", self.ws, "g1", "feature/T-7", "--base", "main").returncode, 0)
        r = self.wt("add", self.ws, "g2", "feature/T-7", "--base", "main")
        self.assertEqual(r.returncode, 3)
        self.assertIn("escalation rule", r.stderr)
        self.assertNotIn("branch.g2", py(SCRIPTS / "status.py", "show", self.ws).stdout)

    def test_validate_and_verify_reject_two_recorded_branches(self):
        self.wt("add", self.ws, "g1", "feature/T-7", "--base", "main")
        git(self.g2, "branch", "feature/T-7")
        py(SCRIPTS / "status.py", "field", self.ws, "branch.g2", "feature/T-7")
        v = py(SCRIPTS / "status.py", "validate", self.ws)
        self.assertEqual(v.returncode, 1)
        self.assertIn("escalation rule", v.stderr)
        r = self.cp("verify", self.ws)
        self.assertEqual(r.returncode, 1)
        self.assertIn("SCOPE    a change request records branches in 2 repos", r.stdout)


if __name__ == "__main__":
    unittest.main()
