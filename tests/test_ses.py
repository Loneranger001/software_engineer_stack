"""Tests for bin/ses: root resolution and script dispatch."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SES = ROOT / "bin" / "ses"


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

    def test_skill_fallback_path_reaches_ses(self):
        # what a skill runs when `ses` is not on PATH: <skill-dir>/../../bin/ses
        rel = ROOT / "skills" / "intake" / ".." / ".." / "bin" / "ses"
        r = subprocess.run([sys.executable, str(rel), "root"], capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), str(ROOT), r.stderr)

    def test_fallback_path_survives_a_symlinked_skill_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            link = Path(tmp) / "skills" / "intake"
            link.parent.mkdir()
            link.symlink_to(ROOT / "skills" / "intake", target_is_directory=True)
            r = subprocess.run([sys.executable, str(link / ".." / ".." / "bin" / "ses"), "root"],
                               capture_output=True, text=True)
            self.assertEqual(r.stdout.strip(), str(ROOT), r.stderr)


if __name__ == "__main__":
    unittest.main()
