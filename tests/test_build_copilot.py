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
        self.assertEqual(bc.yaml_str("Use when: reading tickets"), '"Use when: reading tickets"')

    def test_leading_indicator_quoted(self):
        self.assertTrue(bc.yaml_str("- list-like").startswith('"'))


class PruneTest(unittest.TestCase):
    def test_removes_only_generated_orphans(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            gh = Path(tmp)
            for name, generated in (("kept", True), ("gone", True), ("handmade", False)):
                text = f"<!-- {bc.MARKER} -->\n" if generated else "hand-written\n"
                (gh / "skills" / name).mkdir(parents=True)
                (gh / "skills" / name / "SKILL.md").write_text(text)
                (gh / "skills" / name / "helper.py").write_text("x = 1\n")
                (gh / "prompts").mkdir(exist_ok=True)
                (gh / "prompts" / f"{name}.prompt.md").write_text(text)
            (gh / "agents").mkdir()
            bc.prune_generated(gh, ["kept"], [])
            self.assertTrue((gh / "skills" / "kept" / "SKILL.md").exists())
            self.assertFalse((gh / "skills" / "gone").exists())
            self.assertTrue((gh / "skills" / "handmade" / "helper.py").exists())
            self.assertFalse((gh / "prompts" / "gone.prompt.md").exists())
            self.assertTrue((gh / "prompts" / "handmade.prompt.md").exists())


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


class SelfContainedTest(unittest.TestCase):
    def test_every_bundle_reference_resolves(self):
        import re
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            subprocess.run(["git", "init", "-q", str(target)], check=True)
            r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_copilot.py"),
                                "--target", str(target), "--self-contained"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr[-2000:])
            gh = target / ".github"
            missing, literal = set(), set()
            for f in gh.rglob("*.md"):
                text = f.read_text()
                if "${CLAUDE_PLUGIN_ROOT}" in text and "knowledge" not in f.parts:
                    literal.add(str(f.relative_to(target)))
                for ref in re.findall(r"\.github/se-stack/([A-Za-z0-9_./-]+)", text):
                    ref = ref.rstrip(".,;:)")
                    if ref and not (gh / "se-stack" / ref).exists():
                        missing.add(f"{f.relative_to(target)} -> {ref}")
            self.maxDiff = None
            self.assertEqual(sorted(missing), [])
            self.assertEqual(sorted(literal), [])


if __name__ == "__main__":
    unittest.main()
