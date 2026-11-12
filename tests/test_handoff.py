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

IMPL = """# Impl doc — T-1

- Inputs: tdd.md (approved), scope-contract.md v1

## 2. Implementation steps

| # | Repo | Step | Files / objects | TDD § | Verify | Rollback |
|---|---|---|---|---|---|---|
| 1 | repo-a | ddl | a.sql | §5 | compile | drop |
| 2 | repo-a | body | a.pkb | §4.1 | T1 | revert |

## 3. Test plan

| T# | Covers | Type | How run | Expected |
|---|---|---|---|---|
| T1 | A1 | unit | utPLSQL | pass |
"""

TDD = """# TDD — T-1

<!-- handoff:start -->
## Handoff summary
- Contract version: {version}
- Traceability: S1 → §4.1; S2 → §5
<!-- handoff:end -->

## 2. Requirements traceability

| Scope item | Design section(s) |
|---|---|
| S1 | §4.1 |
| S2 | §5 |
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
        self.write("tdd.md", TDD.format(version=2))
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

    def test_impl_doc_has_no_summary_and_is_skipped(self):
        self.write("scope-contract.md", CONTRACT.format(version=1))
        self.write("impl-doc.md", IMPL)
        r = run("check", self.ws)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1 document(s)", r.stdout)
        r = run("check", self.ws / "impl-doc.md")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("no handoff summary by design", r.stdout)

    def test_stale_contract_version_fails(self):
        self.write("scope-contract.md", CONTRACT.format(version=3))
        self.write("tdd.md", TDD.format(version=2))
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

    def test_draft_fdd_is_skipped_in_a_full_workspace_until_approved(self):
        self.write("scope-contract.md", CONTRACT.format(version=1))
        self.write("fdd.md", "# FDD draft, no summary yet\n")
        self.write("STATUS.md", "# STATUS\n\n- task-id: T-1\n- pipeline: full\n")
        r = run("check", self.ws)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("an FDD draft", r.stdout)
        self.assertEqual(run("check", self.ws / "fdd.md").returncode, 1)  # by name: checked
        self.write("STATUS.md", "# STATUS\n\n- task-id: T-1\n- pipeline: full\n- fdd: approved 2026-11-05 by u\n")
        self.assertEqual(run("check", self.ws).returncode, 1)

    def test_grill_rows_in_tdd_verification_must_reach_summary(self):
        self.write("scope-contract.md", CONTRACT.format(version=1))
        self.write("tdd.md", "<!-- handoff:start -->\n- Contract version: 1\n- Verification: A1 → unit\n"
                             "<!-- handoff:end -->\n\n## 7. Verification approach\n\n"
                             "| Criterion (A#, or G# from /grill) | Test type | Sketch |\n|---|---|---|\n"
                             "| A1 | unit | x |\n| G4 | regression | rerun |\n")
        r = run("check", self.ws / "tdd.md")
        self.assertEqual(r.returncode, 1)
        self.assertIn("omits ID(s) the body defines or traces: G4", r.stderr)

    def test_tdd_must_carry_every_contract_criterion_and_approved_scenario(self):
        self.write("scope-contract.md", CONTRACT.format(version=1))
        tdd = ("<!-- handoff:start -->\n- Contract version: 1\n- Traceability: S1, S2\n- Verification: A1, A2\n"
               "<!-- handoff:end -->\n\n## 7. Verification approach\n\n"
               "| Criterion | Test type | Sketch |\n|---|---|---|\n| A1 | unit | x |\n")
        self.write("tdd.md", tdd)
        r = run("check", self.ws)
        self.assertEqual(r.returncode, 1)
        self.assertIn("§7 Verification approach has no row for A2 (scope-contract.md)", r.stderr)
        self.write("tdd.md", tdd.replace("| A1 | unit | x |", "| A1, A2 | unit | x |"))
        self.assertEqual(run("check", self.ws / "tdd.md").returncode, 0)
        # an approved FDD's scenarios join the rows §7 must name
        self.write("fdd.md", "<!-- handoff:start -->\n- Contract version: 1\n- Scenarios: TS1\n<!-- handoff:end -->\n\n"
                             "## 14. Functional test scenarios\n\n| # | Scenario |\n|---|---|\n| TS1 | x |\n")
        self.write("STATUS.md", "# STATUS\n\n- task-id: T-1\n- pipeline: full\n- fdd: approved 2026-11-05 by u\n")
        r = run("check", self.ws / "tdd.md")
        self.assertEqual(r.returncode, 1)
        self.assertIn("TS1 (fdd.md)", r.stderr)

    def test_only_the_documents_own_id_kinds_are_required(self):
        # research notes: open questions travel; rejected options (O#) and risks (R#) do not
        self.write("scope-contract.md", CONTRACT.format(version=1))
        self.write("research-notes.md", "<!-- handoff:start -->\n- Contract version: 1\n- Open questions: Q1 x\n"
                                        "<!-- handoff:end -->\n\n| Option | Sketch |\n|---|---|\n| O1 | a |\n| O2 | b |\n\n"
                                        "| # | Question |\n|---|---|\n| Q1 | x |\n| Q2 | y |\n")
        r = run("check", self.ws / "research-notes.md")
        self.assertEqual(r.returncode, 1)
        self.assertIn("omits ID(s) the body defines or traces: Q2", r.stderr)
        self.assertNotIn("O1", r.stderr)

    def test_several_ids_in_a_first_cell_are_each_required(self):
        self.write("scope-contract.md", CONTRACT.format(version=1))
        self.write("tdd.md", "<!-- handoff:start -->\n- Contract version: 1\n- Verification: A1, A2\n"
                             "<!-- handoff:end -->\n\n## 7. Verification approach\n\n"
                             "| Criterion | Test type | Sketch |\n|---|---|---|\n| A1, A2, TS4 | unit | x |\n")
        r = run("check", self.ws / "tdd.md")
        self.assertEqual(r.returncode, 1)
        self.assertIn("traces: TS4", r.stderr)

    def test_workspace_without_stage_documents_passes(self):
        self.write("analysis.md", "# CR analysis\n")
        r = run("check", self.ws)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("nothing to check", r.stdout)

    def test_templates_carry_complete_blocks(self):
        # each template alone (no sibling contract, so only structure and IDs are checked)
        for name in ("scope-contract.md", "research-notes.md", "fdd.md", "tdd.md"):
            with tempfile.TemporaryDirectory() as d:
                shutil.copy(ROOT / "templates" / name, d)
                r = run("check", Path(d) / name)
                self.assertEqual(r.returncode, 0, f"{name}: {r.stderr}")
        self.assertNotIn("handoff:start", (ROOT / "templates" / "impl-doc.md").read_text())


if __name__ == "__main__":
    unittest.main()
