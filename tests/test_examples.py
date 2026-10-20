"""Keep shipped examples and split skills in the current format."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
SAMPLE = ROOT / "examples" / "sample-task"


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)


class SampleTaskTest(unittest.TestCase):
    def test_sample_status_has_current_structure(self):
        r = run(SCRIPTS / "status.py", "validate", SAMPLE, "--structure-only")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_full_validate_still_checks_paths(self):
        r = run(SCRIPTS / "status.py", "validate", SAMPLE)
        self.assertEqual(r.returncode, 1)
        self.assertIn("does not exist", r.stderr)

    def test_sample_handoff_summaries_pass(self):
        r = run(SCRIPTS / "handoff.py", "check", SAMPLE)
        self.assertEqual(r.returncode, 0, r.stderr)


class UnderstandSplitTest(unittest.TestCase):
    def test_skill_points_at_explain_md_and_it_has_the_moved_stages(self):
        skill = (ROOT / "skills" / "understand" / "SKILL.md").read_text()
        explain = (ROOT / "skills" / "understand" / "explain.md").read_text()
        self.assertIn("skills/understand/explain.md", skill)
        for heading in ("## 4. Explain in layers", "## 5. Q&A until the model holds", "## 6. Close and hand off"):
            self.assertIn(heading, explain)
            self.assertNotIn(heading, skill)
        self.assertIn("explain=done", explain)


if __name__ == "__main__":
    unittest.main()
