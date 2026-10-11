"""Tests for scripts/build_copilot.py helpers and the --check mode."""
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build_copilot", ROOT / "scripts" / "build_copilot.py")
bc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bc)


class YamlStrTest(unittest.TestCase):
    def test_plain_left_alone(self):
        self.assertEqual(bc.yaml_str("Start a new task. Use when ready"), "Start a new task. Use when ready")

    def test_colon_space_quoted(self):
        self.assertEqual(bc.yaml_str("Use when: reading Jira"), '"Use when: reading Jira"')

    def test_leading_indicator_quoted(self):
        self.assertTrue(bc.yaml_str("- list-like").startswith('"'))


class MergeKnowledgeTest(unittest.TestCase):
    def test_local_entries_kept_once(self):
        canonical = "# L\n- [2026-01-01] a\n"
        existing = "# L\n- [2026-01-01]  a\n- [2026-02-02] local\n"
        merged = bc.merge_knowledge_file(canonical, existing)
        self.assertEqual(merged.count("local"), 1)
        self.assertEqual(merged.count("] a"), 1)


class CheckModeTest(unittest.TestCase):
    def test_committed_output_is_current(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_copilot.py"), "--check"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])


if __name__ == "__main__":
    unittest.main()
