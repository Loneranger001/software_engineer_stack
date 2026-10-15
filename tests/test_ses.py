"""Tests for bin/ses: script dispatch and per-harness setup."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SES = ROOT / "bin" / "ses"
SKILLS = sorted(d.name for d in (ROOT / "skills").iterdir() if (d / "SKILL.md").is_file())
AGENTS = ("code-reviewer", "doc-fact-checker", "scope-auditor")


def ses(*args, cwd=None):
    return subprocess.run([sys.executable, str(SES), *map(str, args)],
                          capture_output=True, text=True, cwd=cwd)


class DispatchTest(unittest.TestCase):
    def test_root_is_the_framework(self):
        self.assertEqual(ses("root").stdout.strip(), str(ROOT))

    def test_root_resolves_through_a_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            link = Path(tmp) / "ses"
            link.symlink_to(SES)
            r = subprocess.run([sys.executable, str(link), "root"], capture_output=True, text=True)
            self.assertEqual(r.stdout.strip(), str(ROOT))

    def test_every_command_maps_to_a_script(self):
        help_text = ses("help").stdout
        cmds = [l.split()[0] for l in help_text.split("Commands:", 1)[1].splitlines() if l.strip()]
        self.assertIn("status", cmds)
        for cmd in cmds:
            with tempfile.TemporaryDirectory() as tmp:   # a script that ignores --help must not litter
                r = ses(cmd, "--help", cwd=tmp)
                self.assertNotIn("No such file", r.stderr, cmd)
                self.assertEqual(list(Path(tmp).iterdir()), [], f"`ses {cmd} --help` created files")

    def test_gate_exit_code_propagates(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            subprocess.run(["git", "init", "-q", str(base / "repo")], check=True)
            r = ses("new-task", "T-1", "auto", "full", base / "repo")
            self.assertEqual(r.returncode, 0, r.stderr)
            ws = Path(r.stdout.split("created ", 1)[1].strip())   # standalone repo: work/ inside it
            self.assertTrue((ws / "STATUS.md").is_file())
            self.assertEqual(ses("status", "require", ws, "intake=approved").returncode, 3)
            self.assertEqual(ses("status", "set", ws, "intake=approved").returncode, 0)
            self.assertEqual(ses("status", "require", ws, "intake=approved").returncode, 0)

    def test_unknown_command_fails(self):
        self.assertEqual(ses("bogus").returncode, 2)


class SetupTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def setup_(self, harness, *extra):
        r = ses("setup", harness, "--home", self.home, *extra)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def assert_skill_links(self, skills_dir):
        for name in SKILLS:
            link = self.home / skills_dir / name
            self.assertTrue(link.is_symlink(), link)
            self.assertEqual(link.resolve(), ROOT / "skills" / name)

    def test_default_links_only_ses(self):
        self.setup_("copilot")
        self.assertEqual((self.home / ".local" / "bin" / "ses").resolve(), SES)
        self.assertFalse((self.home / ".copilot").exists())   # the plugin ships skills and agents

    def test_codex_registers_reviewer_agents(self):
        self.setup_("codex")
        self.assertFalse((self.home / ".agents").exists())     # skills come from the plugin
        for name in AGENTS:
            text = (self.home / ".codex" / "agents" / f"{name}.toml").read_text()
            self.assertIn(f'name = "{name}"', text)
            self.assertIn('sandbox_mode = "read-only"', text)
            self.assertIn(f"agents/{name}.md", text)
            if sys.version_info >= (3, 11):
                import tomllib
                parsed = tomllib.loads(text)
                self.assertEqual(parsed["name"], name)
                self.assertTrue(parsed["developer_instructions"].strip())

    def test_skills_mode_per_harness(self):
        self.setup_("codex", "--skills")
        self.assert_skill_links(".agents/skills")
        self.setup_("copilot", "--skills")
        self.assert_skill_links(".copilot/skills")
        for name in AGENTS:
            self.assertEqual((self.home / ".copilot" / "agents" / f"{name}.agent.md").resolve(),
                             ROOT / "com.github.copilot" / "agents" / f"{name}.agent.md")
        self.setup_("claude", "--skills")
        self.assert_skill_links(".claude/skills")
        for name in AGENTS:
            self.assertEqual((self.home / ".claude" / "agents" / f"{name}.md").resolve(),
                             ROOT / "agents" / f"{name}.md")

    def test_symlinked_skill_dir_still_finds_ses_by_relative_path(self):
        # the fallback skills use: <skill-dir>/../../bin/ses, with <skill-dir> a symlink
        self.setup_("codex", "--skills")
        rel = self.home / ".agents" / "skills" / "intake" / ".." / ".." / "bin" / "ses"
        r = subprocess.run([sys.executable, str(rel), "root"], capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), str(ROOT), r.stderr)

    def test_linked_ses_runs_scripts(self):
        self.setup_("codex")
        r = subprocess.run([sys.executable, str(self.home / ".local" / "bin" / "ses"), "lessons", "intake"],
                           capture_output=True, text=True,
                           env=dict(os.environ, SES_HOME=str(self.home / ".ses")))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("lesson(s) for stage:intake", r.stdout)

    def test_rerun_is_idempotent(self):
        self.setup_("codex", "--skills")
        self.setup_("codex", "--skills")
        self.assert_skill_links(".agents/skills")

    def test_foreign_files_are_never_replaced(self):
        own = self.home / ".agents" / "skills" / "research"
        own.mkdir(parents=True)
        (own / "SKILL.md").write_text("someone else's skill\n")
        r = ses("setup", "codex", "--skills", "--home", self.home)
        self.assertEqual(r.returncode, 1)
        self.assertIn("was not created by ses setup", r.stderr)
        self.assertEqual((own / "SKILL.md").read_text(), "someone else's skill\n")
        self.assertFalse((self.home / ".agents" / "skills" / "intake").exists())

    def test_dry_run_changes_nothing(self):
        self.setup_("copilot", "--skills", "--dry-run")
        self.assertFalse((self.home / ".copilot").exists())
        self.assertFalse((self.home / ".local").exists())

    def test_remove_keeps_shared_cli_until_last_harness(self):
        self.setup_("codex", "--skills")
        self.setup_("copilot", "--skills")
        ses("setup", "codex", "--remove", "--home", self.home)
        self.assertFalse((self.home / ".agents" / "skills" / "intake").exists())
        self.assertFalse((self.home / ".codex" / "agents" / "scope-auditor.toml").exists())
        self.assertTrue((self.home / ".local" / "bin" / "ses").is_symlink())
        ses("setup", "copilot", "--remove", "--home", self.home)
        self.assertFalse((self.home / ".local" / "bin" / "ses").exists())
        self.assertFalse((self.home / ".copilot" / "skills" / "intake").exists())


if __name__ == "__main__":
    unittest.main()
