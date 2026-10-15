"""Tests for scripts/build_copilot.py helpers and the --check mode."""
import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
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
            # prompt files are retired output: every generated one goes, hand-made ones stay
            self.assertFalse((gh / "prompts" / "gone.prompt.md").exists())
            self.assertFalse((gh / "prompts" / "kept.prompt.md").exists())
            self.assertTrue((gh / "prompts" / "handmade.prompt.md").exists())

    def test_empty_prompts_dir_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            gh = Path(tmp)
            (gh / "prompts").mkdir()
            (gh / "prompts" / "intake.prompt.md").write_text(f"<!-- {bc.MARKER} -->\n")
            bc.prune_generated(gh, ["intake"], [])
            self.assertFalse((gh / "prompts").exists())


class MergeKnowledgeTest(unittest.TestCase):
    def test_local_entries_kept_once(self):
        canonical = "# L\n- [2026-01-01] a\n"
        existing = "# L\n- [2026-01-01]  a\n- [2026-02-02] local\n"
        merged = bc.merge_knowledge_file(canonical, existing)
        self.assertEqual(merged.count("local"), 1)
        self.assertEqual(merged.count("] a"), 1)


class SubstituteTest(unittest.TestCase):
    TEXT = "see `${CLAUDE_PLUGIN_ROOT}/agents/scope-auditor.md` and ${CLAUDE_PLUGIN_ROOT}/skills/x/a.md"

    def test_plain_root(self):
        out = bc.substitute(self.TEXT, bc.Refs.at("/opt/stack"))
        self.assertIn("/opt/stack/agents/scope-auditor.md`", out)
        self.assertIn("/opt/stack/skills/x/a.md", out)

    def test_plugin_points_at_agent_md(self):
        self.assertIn("<plugin-root>/agents/scope-auditor.agent.md`", bc.substitute(self.TEXT, bc.PLUGIN_REFS))

    def test_bundle_points_at_github_dirs(self):
        out = bc.substitute(self.TEXT, bc.BUNDLE_REFS)
        self.assertIn(".github/agents/scope-auditor.agent.md`", out)
        self.assertIn(".github/skills/x/a.md", out)


class AgentFrontmatterTest(unittest.TestCase):
    def test_claude_tools_mapped_to_copilot_aliases(self):
        fm = {"name": "r", "description": "d", "tools": "Read, Grep, Glob, Bash"}
        self.assertIn('tools: ["read", "search", "execute"]\n', bc.agent_frontmatter(fm))

    def test_no_tools_line_when_unset(self):
        self.assertNotIn("tools:", bc.agent_frontmatter({"name": "r", "description": "d"}))


def scratch_stack(tmp: Path) -> Path:
    stack = tmp / "stack"
    shutil.copytree(ROOT, stack, ignore=shutil.ignore_patterns(".git", "work", "__pycache__"))
    return stack


def build(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True)


def missing_refs(scan: Path, token: str, base: Path) -> list[str]:
    """Paths written as <token>/<path> under scan that do not exist under base."""
    bad = []
    for f in scan.rglob("*.md"):
        for m in re.finditer(re.escape(token) + r"/([\w./-]+)", f.read_text()):
            rel = m.group(1).rstrip(".").rstrip("/")
            if rel and rel != ".generated" and not (base / rel).exists():
                bad.append(f"{f.relative_to(scan)} -> {token}/{rel}")
    return sorted(set(bad))


class ReferenceIntegrityTest(unittest.TestCase):
    """Every framework path a generated file names must exist in that layout."""

    def test_plugin_and_self_contained_refs_resolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            stack = scratch_stack(Path(tmp))
            work = Path(tmp) / "work-repo"
            work.mkdir()
            r = build(str(stack / "scripts" / "build_copilot.py"), "--stack-root", str(stack),
                      "--target", str(work), "--self-contained")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(missing_refs(stack / "copilot", "<plugin-root>", stack / "copilot"), [])
            self.assertEqual(missing_refs(work / ".github", ".github", work / ".github"), [])


class CheckModeTest(unittest.TestCase):
    def test_committed_output_is_current(self):
        r = build(str(ROOT / "scripts" / "build_copilot.py"), "--check")
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])

    def test_orphan_in_generated_dir_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            stack = scratch_stack(Path(tmp))
            (stack / ".github" / "skills" / "intake" / "stale.md").write_text("old\n")
            r = build(str(stack / "scripts" / "build_copilot.py"), "--stack-root", str(stack), "--check")
            self.assertEqual(r.returncode, 1)
            self.assertIn("no longer generated: .github/skills/intake/stale.md", r.stderr)


class PreflightTest(unittest.TestCase):
    def test_handwritten_file_blocks_before_any_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            stack = scratch_stack(Path(tmp))
            work = Path(tmp) / "work-repo"
            (work / ".github").mkdir(parents=True)
            (work / ".github" / "copilot-instructions.md").write_text("team rules\n")
            r = build(str(stack / "scripts" / "build_copilot.py"), "--stack-root", str(stack),
                      "--target", str(work))
            self.assertNotEqual(r.returncode, 0)
            self.assertEqual([p.name for p in (work / ".github").rglob("*")], ["copilot-instructions.md"])


if __name__ == "__main__":
    unittest.main()
