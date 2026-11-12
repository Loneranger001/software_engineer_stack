"""Tests for scripts/review.py: reviewer reports kept on disk, with their mode, and gated on."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVIEW = [sys.executable, str(ROOT / "scripts" / "review.py")]


def run(*args, stdin=None):
    return subprocess.run([*REVIEW, *map(str, args)], capture_output=True, text=True, input=stdin)


class ReviewTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self.tmp.name) / "work" / "T-1"
        self.ws.mkdir(parents=True)
        (self.ws / "STATUS.md").write_text("# STATUS — T-1\n\n- task-id: T-1\n- pipeline: full\n\n"
                                           "## Stage gates\n\nintake: pending\n\n## Next action\n\nx\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_report_fails_the_gate(self):
        r = run("require", self.ws, "doc-fact-checker", "tdd")
        self.assertEqual(r.returncode, 3)
        self.assertIn("no doc-fact-checker report for tdd", r.stdout)

    def test_latest_report_decides(self):
        r = run("record", self.ws, "doc-fact-checker", "tdd", "--mode", "subagent", "-",
                stdin="VERDICT: FINDINGS\n[WRONG] §4.2 …\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.ws / "reviews" / "doc-fact-checker-tdd-1.md").is_file())
        self.assertEqual(run("require", self.ws, "doc-fact-checker", "tdd").returncode, 3)
        run("record", self.ws, "doc-fact-checker", "tdd", "--mode", "subagent", stdin="VERDICT: PASS\n")
        r = run("require", self.ws, "doc-fact-checker", "tdd")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("PASS (subagent, reviews/doc-fact-checker-tdd-2.md)", r.stdout)
        status = (self.ws / "STATUS.md").read_text()
        self.assertIn("- review.doc-fact-checker.tdd: PASS (subagent, ", status)

    def test_self_pass_is_named(self):
        run("record", self.ws, "scope-auditor", "delivery", "--mode", "self-pass", stdin="VERDICT: PASS\n")
        r = run("require", self.ws, "scope-auditor", "delivery")
        self.assertEqual(r.returncode, 0)
        self.assertIn("self-pass: the author re-read its own work; tell the user", r.stdout)
        self.assertIn("self-pass", run("list", self.ws).stdout)

    def test_every_verdict_in_a_report_must_pass(self):
        run("record", self.ws, "code-reviewer", "repo-a", "--mode", "custom-agent",
            stdin="VERDICT: APPROVE\n…\nVERDICT: FINDINGS\n[SEV-1 blocker] x\n")
        self.assertEqual(run("require", self.ws, "code-reviewer", "repo-a").returncode, 3)

    def test_bad_input_is_refused(self):
        self.assertEqual(run("record", self.ws, "doc-fact-checker", "tdd", "--mode", "vibes",
                             stdin="VERDICT: PASS\n").returncode, 1)
        self.assertEqual(run("record", self.ws, "doc-fact-checker", "tdd", "--mode", "subagent",
                             stdin="looks fine to me\n").returncode, 1)
        self.assertEqual(run("record", self.ws, "linter", "tdd", "--mode", "subagent",
                             stdin="VERDICT: PASS\n").returncode, 1)
        self.assertEqual(run("require", self.ws, "doc-fact-checker", "TDD").returncode, 1)
        self.assertFalse((self.ws / "reviews").exists())


if __name__ == "__main__":
    unittest.main()
