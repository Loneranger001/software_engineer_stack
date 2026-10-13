"""Tests for scripts/handoff.py."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HANDOFF = [sys.executable, str(ROOT / "scripts" / "handoff.py")]

CONTRACT = """# Scope Contract — T-1: demo

- Version: {version}

<!-- handoff:start -->
## Handoff summary
- Contract version: {version}
- In scope: S1 add column; S2 populate it
- Out of scope: N1 refactor
- Acceptance: A1 → S1; A2 → S2
<!-- handoff:end -->

## In scope

| # | Item | Source |
|---|---|---|
| S1 | add column | §1 |
| S2 | populate it | §2 |

## Out of scope

| # | Item | Why |
|---|---|---|
| N1 | refactor | not asked |

## Acceptance criteria

| # | Criterion | Verifies | How |
|---|---|---|---|
| A1 | column exists | S1 | query |
| A2 | rows populated | S2 | query |
"""

IMPL = """# Implementation Document — T-1

<!-- handoff:start -->
## Handoff summary
- Contract version: {version}
- step 1: repo-a ddl — verify compile
{step2}- Tests: T1 → A1
<!-- handoff:end -->

## 2. Implementation steps

| # | Repo | Step | Files | Verification | Rollback |
|---|---|---|---|---|---|
| 1 | repo-a | ddl | a.sql | compile | drop |
| 2 | repo-a | body | a.pkb | utPLSQL T1 | revert |

## 3. Test plan

| Test | Covers | How run | Expected |
|---|---|---|---|
| T1 | A1 | utPLSQL | pass |
"""


def run(*args):
    return subprocess.run([*HANDOFF, *map(str, args)], capture_output=True, text=True)


class HandoffTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        (self.ws / name).write_text(text)

    def test_complete_workspace_passes(self):
        self.write("scope-contract.md", CONTRACT.format(version=2))
        self.write("impl-doc.md", IMPL.format(version=2, step2="- step 2: repo-a body — verify T1\n"))
        r = run("check", self.ws)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("2 document(s)", r.stdout)

    def test_show_prints_only_the_block(self):
        self.write("scope-contract.md", CONTRACT.format(version=1))
        out = run("show", self.ws / "scope-contract.md").stdout
        self.assertIn("S2 populate it", out)
        self.assertNotIn("| S1 |", out)

    def test_missing_id_fails(self):
        self.write("scope-contract.md", CONTRACT.format(version=1)
                   .replace("; S2 populate it", "").replace("; A2 → S2", "; A2 → (missing)"))
        r = run("check", self.ws)
        self.assertEqual(r.returncode, 1)
        self.assertIn("omits ID(s) the body defines or traces: S2", r.stderr)

    def test_missing_step_fails(self):
        self.write("scope-contract.md", CONTRACT.format(version=1))
        self.write("impl-doc.md", IMPL.format(version=1, step2=""))
        r = run("check", self.ws / "impl-doc.md")
        self.assertEqual(r.returncode, 1)
        self.assertIn("omits step(s): step 2", r.stderr)

    def test_stale_contract_version_fails(self):
        self.write("scope-contract.md", CONTRACT.format(version=3))
        self.write("impl-doc.md", IMPL.format(version=2, step2="- step 2: x — y\n"))
        r = run("check", self.ws)
        self.assertEqual(r.returncode, 1)
        self.assertIn("based on contract v2 but scope-contract.md is v3", r.stderr)

    def test_missing_block_and_overlong_block_fail(self):
        self.write("tdd.md", "# TDD\n\n## 1. Overview\n")
        self.assertIn("no handoff summary", run("check", self.ws / "tdd.md").stderr)
        filler = "".join(f"- line {i}\n" for i in range(45))
        self.write("tdd.md", "<!-- handoff:start -->\n- Contract version: 1\n" + filler + "<!-- handoff:end -->\n")
        self.assertIn("max 40", run("check", self.ws / "tdd.md").stderr)

    def test_fdd_is_checked_as_a_stage_document(self):
        self.write("scope-contract.md", CONTRACT.format(version=1))
        self.write("fdd.md", "<!-- handoff:start -->\n- Contract version: 1\n- Requirements: FR1 x\n"
                             "<!-- handoff:end -->\n\n| # | Requirement | Source |\n|---|---|---|\n"
                             "| FR1 | x | S1 |\n| FR2 | y | S2 |\n")
        r = run("check", self.ws)
        self.assertEqual(r.returncode, 1)
        self.assertIn("fdd.md: summary omits ID(s) the body defines or traces: FR2", r.stderr)

    def test_workspace_without_stage_documents_passes(self):
        self.write("analysis.md", "# CR analysis\n")
        r = run("check", self.ws)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("nothing to check", r.stdout)

    def test_templates_carry_complete_blocks(self):
        # each template alone (no sibling contract, so only structure and IDs are checked)
        for name in ("scope-contract.md", "research-notes.md", "fdd.md", "tdd.md", "impl-doc.md"):
            with tempfile.TemporaryDirectory() as d:
                shutil.copy(ROOT / "templates" / name, d)
                r = run("check", Path(d) / name)
                self.assertEqual(r.returncode, 0, f"{name}: {r.stderr}")


if __name__ == "__main__":
    unittest.main()
