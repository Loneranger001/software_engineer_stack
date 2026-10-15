"""Tests for scripts/check_knowledge.py using throwaway git repos."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSONS_HEAD = "# Lessons\n\n<!-- lessons below this line -->\n"


def git(repo, *args, date=None):
    env = None
    if date:
        import os
        env = dict(os.environ, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, env=env)


class CheckKnowledgeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "t")
        (self.repo / "scripts").mkdir()
        shutil.copy(ROOT / "scripts" / "check_knowledge.py", self.repo / "scripts")
        (self.repo / "skills" / "research").mkdir(parents=True)
        (self.repo / "skills" / "research" / "SKILL.md").write_text("v1\n")
        (self.repo / "knowledge").mkdir()
        (self.repo / "knowledge" / "lessons.md").write_text(LESSONS_HEAD)
        self.write_decisions("")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init", date="2026-01-01T12:00:00")

    def tearDown(self):
        self.tmp.cleanup()

    def write_decisions(self, entries):
        (self.repo / "knowledge" / "decisions.md").write_text(
            "# Decisions\n\n## Applied changes\n\n" + entries)

    def check(self):
        return subprocess.run([sys.executable, str(self.repo / "scripts" / "check_knowledge.py"),
                               "--stack-root", str(self.repo)], capture_output=True, text=True)

    def test_lost_edit_detected(self):
        # the 2026-08-12 failure: entry recorded, skill file never changed
        self.write_decisions("- [2026-08-12] Added preflight in `skills/research/SKILL.md` — task X\n")
        git(self.repo, "commit", "-qam", "record decision", date="2026-08-12T12:00:00")
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("lost edit", r.stderr)

    def test_applied_edit_passes(self):
        (self.repo / "skills" / "research" / "SKILL.md").write_text("v2\n")
        self.write_decisions("- [2026-08-12] Added preflight in `skills/research/SKILL.md` — task X\n")
        git(self.repo, "commit", "-qam", "apply", date="2026-08-12T12:00:00")
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_uncommitted_edit_passes_for_pre_commit(self):
        (self.repo / "skills" / "research" / "SKILL.md").write_text("v2\n")
        self.write_decisions("- [2099-01-01] Added preflight in `skills/research/SKILL.md` — task X\n")
        self.assertEqual(self.check().returncode, 0)

    def test_entry_must_name_a_file(self):
        self.write_decisions("- [2026-08-12] Improved research — task X\n")
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("names no edited file", r.stderr)

    def test_generated_path_rejected(self):
        self.write_decisions("- [2026-08-12] Edit in `copilot/skills/research/SKILL.md` — task X\n")
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("generated output", r.stderr)

    def test_file_removed_later_keeps_its_entry_valid(self):
        (self.repo / "scripts" / "old_tool.py").write_text("x\n")
        self.write_decisions("- [2026-08-12] Added `scripts/old_tool.py` — task X\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "add tool", date="2026-08-12T12:00:00")
        git(self.repo, "rm", "-q", "scripts/old_tool.py")
        git(self.repo, "commit", "-qm", "remove tool", date="2026-09-01T12:00:00")
        self.assertEqual(self.check().returncode, 0, self.check().stderr)
        self.write_decisions("- [2026-08-12] Added `scripts/never_existed.py` — task X\n")
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("does not exist", r.stderr)

    def test_bare_skill_path_still_flagged(self):
        self.write_decisions("- [2026-08-12] Added preflight in `research/SKILL.md` — task X\n")
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("not a framework path", r.stderr)

    def test_prose_directory_mention_ignored(self):
        (self.repo / "skills" / "research" / "SKILL.md").write_text("v2\n")
        self.write_decisions("- [2099-01-01] Raw logs go to `evidence/raw/` and `work/<id>/` "
                             "via `skills/research/SKILL.md` — task X\n")
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_pending_upstream_skips_git_check(self):
        self.write_decisions("- [2026-08-12] [pending-upstream] preflight — work/X/deliverables/framework-edits.patch\n")
        self.assertEqual(self.check().returncode, 0)

    def test_malformed_and_unknown_stage_lessons(self):
        (self.repo / "knowledge" / "lessons.md").write_text(
            LESSONS_HEAD
            + "- [2026-08-12] [stage:grill] [lang:-] [repo:-] Ask about nulls. (task X)\n"
            + "- [2026-08-12] [stage:testing] [lang:-] [repo:-] Bad tag. (task X)\n"
            + "- free text lesson\n")
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("unknown stage tag 'testing'", r.stderr)
        self.assertIn("malformed lesson", r.stderr)
        self.assertNotIn("stage:grill", r.stderr)


if __name__ == "__main__":
    unittest.main()
