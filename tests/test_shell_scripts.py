"""Tests for scripts/lessons.sh and scripts/capture.sh."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LESSONS = """# Lessons

> - [YYYY-MM-DD] [stage:<stage>] [lang:-] [repo:-] header example, never printed (task X)

<!-- lessons below this line -->
- [2026-01-01] [stage:implement] [lang:-] [repo:-] Implement lesson. (task A)
- [2026-01-02] [stage:verify] [lang:plsql] [repo:billing] Verify PL/SQL lesson. (task B)
- [2026-01-03] [stage:any] [lang:-] [repo:-] Any-stage lesson. (task C)
- [2026-01-04] [stage:research] [lang:ksh] [repo:a.b] Research ksh lesson. (task D)
"""


class LessonsTest(unittest.TestCase):
    def setUp(self):
        # a framework root of its own: lessons.sh reads ../knowledge/lessons.md
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "scripts").mkdir()
        (root / "knowledge").mkdir()
        shutil.copy(ROOT / "scripts" / "lessons.sh", root / "scripts")
        (root / "knowledge" / "lessons.md").write_text(LESSONS)
        self.script = str(root / "scripts" / "lessons.sh")

    def tearDown(self):
        self.tmp.cleanup()

    def run_lessons(self, *args):
        return subprocess.run(["sh", self.script, *args], capture_output=True, text=True)

    def test_stage_plus_any(self):
        out = self.run_lessons("implement").stdout
        self.assertIn("Implement lesson", out)
        self.assertIn("Any-stage lesson", out)
        self.assertNotIn("Verify PL/SQL", out)
        self.assertNotIn("header example", out)
        self.assertIn("(2 lesson(s)", out)

    def test_lang_pulls_other_stages(self):
        out = self.run_lessons("implement", "--lang", "plsql,sql").stdout
        self.assertIn("Verify PL/SQL lesson", out)
        self.assertNotIn("Research ksh", out)

    def test_repo_matches_literally(self):
        out = self.run_lessons("intake", "--repo", "a.b").stdout
        self.assertIn("Research ksh lesson", out)
        out = self.run_lessons("intake", "--repo", "axb").stdout
        self.assertNotIn("Research ksh lesson", out)

    def test_zero_is_reported(self):
        out = self.run_lessons("grill").stdout
        self.assertIn("Any-stage lesson", out)
        out = subprocess.run(["sh", "-c", f"sh {self.script} grill | tail -1"],
                             capture_output=True, text=True).stdout
        self.assertIn("(1 lesson(s) for stage:grill)", out)

    def test_bad_stage_rejected(self):
        self.assertEqual(self.run_lessons("x;rm").returncode, 2)


class CaptureTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ev = Path(self.tmp.name) / "evidence"

    def tearDown(self):
        self.tmp.cleanup()

    def capture(self, *args, env=None):
        return subprocess.run(["sh", str(ROOT / "scripts" / "capture.sh"), str(self.ev), *args],
                              capture_output=True, text=True,
                              env=dict(os.environ, **(env or {})))

    def test_full_log_kept_summary_bounded(self):
        r = self.capture("big", "--tail", "5", "--", "sh", "-c", "seq 1 500")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(len((self.ev / "raw" / "big.log").read_text().splitlines()), 500)
        self.assertIn("last 5 of 500 lines", r.stdout)
        self.assertNotIn("\n250\n", r.stdout)
        self.assertLess(len(r.stdout.splitlines()), 12)

    def test_exit_code_propagates_and_grep_finds_early_error(self):
        r = self.capture("fail", "--tail", "2", "--grep", "ORA-",
                         "--", "sh", "-c", "echo ORA-00942 early; seq 1 50; exit 3")
        self.assertEqual(r.returncode, 3)
        self.assertIn("exit: 3", r.stdout)
        self.assertIn("1:ORA-00942 early", r.stdout)

    def test_connect_string_redacted_in_command_line(self):
        r = self.capture("conn", "--", "echo", "scott/tiger@dev", env={"SES_DB_CONN": "scott/tiger@dev"})
        first = r.stdout.splitlines()[0]
        self.assertNotIn("tiger", first)
        self.assertIn("<SES_DB_CONN>", first)

    def test_stdin_is_closed(self):
        r = subprocess.run(["sh", str(ROOT / "scripts" / "capture.sh"), str(self.ev), "cat", "--", "cat"],
                           input="should not be read\n", capture_output=True, text=True, timeout=10)
        self.assertEqual(r.returncode, 0)
        self.assertIn("output: 0 line(s)", r.stdout)

    def test_bad_name_rejected(self):
        self.assertEqual(self.capture("../x", "--", "true").returncode, 2)


if __name__ == "__main__":
    unittest.main()
