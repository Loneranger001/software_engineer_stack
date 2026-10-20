"""Tests for scripts/status.py against workspaces scaffolded by new-task.sh."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATUS = [sys.executable, str(ROOT / "scripts" / "status.py")]


def run(*args):
    return subprocess.run([*STATUS, *args], capture_output=True, text=True)


class StatusTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        (base / "repo" / ".git").mkdir(parents=True)
        subprocess.run(["sh", str(ROOT / "scripts" / "new-task.sh"), "T-1", str(base), "full",
                        str(base / "repo")], check=True, capture_output=True)
        self.ws = str(base / "work" / "T-1")
        self.status_md = Path(self.ws) / "STATUS.md"

    def tearDown(self):
        self.tmp.cleanup()

    def test_fresh_workspace_validates(self):
        r = run("validate", self.ws)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_require_blocks_unmet_gate(self):
        r = run("require", self.ws, "intake=approved")
        self.assertEqual(r.returncode, 3)
        self.assertIn("GATE NOT MET", r.stderr)

    def test_set_then_require_passes_with_dated_note(self):
        r = run("set", self.ws, "intake=approved", "--note", "by asif, contract v1", "--next", "Run /research.")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(run("require", self.ws, "intake=approved").returncode, 0)
        self.assertRegex(self.status_md.read_text(),
                         r"\nintake: approved \(\d{4}-\d{2}-\d{2}; by asif, contract v1\)\n")
        self.assertEqual(run("get", self.ws, "next").stdout.strip(), "Run /research.")

    def test_status_stays_minimal(self):
        run("set", self.ws, "intake=approved")
        run("field", self.ws, "branch.repo", "feature/T-1")
        text = self.status_md.read_text()
        self.assertNotIn("## Log", text)
        self.assertLess(len(text.splitlines()), 30)
        self.assertEqual(run("set", self.ws, "research=done", "--log", "x").returncode, 1)

    def test_legacy_repos_section_still_read(self):
        text = self.status_md.read_text()
        repo = run("get", self.ws, "repos-analyzed").stdout.strip()
        legacy = "\n".join(l for l in text.splitlines() if not l.startswith("- repos-analyzed:"))
        legacy = legacy.replace("## Stage gates", f"## Repos analyzed\n\n  - {repo}\n\n## Stage gates")
        self.status_md.write_text(legacy + "\n")
        self.assertEqual(run("get", self.ws, "repos-analyzed").stdout.strip(), repo)

    def test_approved_satisfies_done_but_not_reverse(self):
        run("set", self.ws, "intake=approved")
        self.assertEqual(run("require", self.ws, "intake=done").returncode, 0)
        run("set", self.ws, "research=done")
        self.assertEqual(run("require", self.ws, "research=approved").returncode, 3)

    def test_waiver_with_note(self):
        run("set", self.ws, "grill=waived by user 2026-10-11: hotfix")
        self.assertEqual(run("require", self.ws, "grill=done,waived").returncode, 0)
        self.assertEqual(run("require", self.ws, "grill=done").returncode, 3)

    def test_unknown_stage_is_error_not_pass(self):
        r = run("require", self.ws, "bogus=done")
        self.assertEqual(r.returncode, 1)
        r = run("set", self.ws, "bogus=done")
        self.assertEqual(r.returncode, 1)

    def test_bad_state_rejected(self):
        self.assertEqual(run("set", self.ws, "intake=finished").returncode, 1)
        self.assertIn("intake: pending", self.status_md.read_text())

    def test_fields_and_repos(self):
        run("field", self.ws, "branch.repo", "feature/T-1")
        self.assertEqual(run("get", self.ws, "branch.repo").stdout.strip(), "feature/T-1")
        repos = run("get", self.ws, "repos-analyzed").stdout.split()
        self.assertEqual(len(repos), 1)
        self.assertTrue(repos[0].endswith("/repo"))

    def test_validate_catches_skipped_gate(self):
        run("set", self.ws, "tech-design=approved")
        r = run("validate", self.ws)
        self.assertEqual(r.returncode, 1)
        self.assertIn("earlier stage 'intake' is pending", r.stderr)

    def test_unparsed_content_survives_rewrite(self):
        self.status_md.write_text(self.status_md.read_text() + "\n## Notes\n\nhand-written note\n")
        run("set", self.ws, "intake=approved")
        self.assertIn("hand-written note", self.status_md.read_text())


if __name__ == "__main__":
    unittest.main()
