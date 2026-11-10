"""Tests for scripts/md2docx.sh, md2confluence.sh and mermaid.lua: diagrams reach the reader as diagrams."""
import os
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
DOC = "# Design\n\nThe flow:\n\n```mermaid\nflowchart TD\n    A[load] --> B{valid?}\n```\n\nEnd.\n"
# a fake mermaid-cli: writes a 1x1 PNG wherever -o points
FAKE_MMDC = """#!/usr/bin/env python3
import base64, sys
out = sys.argv[sys.argv.index("-o") + 1]
open(out, "wb").write(base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="))
"""


@unittest.skipUnless(shutil.which("pandoc"), "pandoc not installed")
class MermaidTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / "deliverables").mkdir()
        self.md = self.dir / "tdd.md"
        self.md.write_text(DOC)

    def tearDown(self):
        self.tmp.cleanup()

    def convert(self, script, path):
        env = dict(os.environ, PATH=path)
        return subprocess.run(["sh", str(SCRIPTS / script), str(self.md)], capture_output=True, text=True, env=env)

    def no_mmdc_path(self):
        # keep pandoc and the shell tools, drop any real mmdc
        dirs = [d for d in os.environ["PATH"].split(os.pathsep) if not (Path(d) / "mmdc").exists()]
        return os.pathsep.join(dirs)

    def test_without_mmdc_the_diagram_is_named_as_left_as_code(self):
        r = self.convert("md2docx.sh", self.no_mmdc_path())
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("WARNING: 1 mermaid diagram(s) in tdd.md will appear as source code", r.stderr)
        xml = zipfile.ZipFile(self.dir / "deliverables" / "tdd.docx").read("word/document.xml").decode()
        self.assertIn("flowchart TD", xml)

    def test_with_mmdc_the_diagram_is_an_image(self):
        fake = self.dir / "bin"
        fake.mkdir()
        (fake / "mmdc").write_text(FAKE_MMDC)
        (fake / "mmdc").chmod(0o755)
        r = self.convert("md2docx.sh", f"{fake}{os.pathsep}{self.no_mmdc_path()}")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("WARNING", r.stderr)
        z = zipfile.ZipFile(self.dir / "deliverables" / "tdd.docx")
        self.assertNotIn("flowchart TD", z.read("word/document.xml").decode())
        self.assertTrue(any(n.startswith("word/media/") for n in z.namelist()))
        r = self.convert("md2confluence.sh", f"{fake}{os.pathsep}{self.no_mmdc_path()}")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("!diagram-1.png!", (self.dir / "deliverables" / "tdd.confluence.txt").read_text())
        self.assertIn("attach the diagram images", r.stdout)

    def test_document_without_diagrams_converts_quietly(self):
        self.md.write_text("# Notes\n\nNo diagrams.\n")
        r = self.convert("md2docx.sh", self.no_mmdc_path())
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stderr, "")


if __name__ == "__main__":
    unittest.main()
