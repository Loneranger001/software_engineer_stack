"""Tests for scripts/review.py: reviewer reports kept on disk, with their mode, and gated on."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVIEW = [sys.executable, str(ROOT / "scripts" / "review.py")]


def run(*args, stdin=None):
    return subprocess.run([*REVIEW, *map(str, args)], capture_output=True, text=True, input=stdin)


TDD = """# Technical Design Document — T-1: x

- Status: draft

<!-- handoff:start -->
## Handoff summary
- Contract version: 1
<!-- handoff:end -->

## 1. Overview

The job loads orders.

## 4. Components

### 4.1 orders_pkg

Adds a parameter.

```sh
## not a heading: a comment in a code block
```

### 4.2 File naming

Keeps the old file name.

## 7. Verification approach

| A1 | unit | x |
"""


class ReviewTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self.tmp.name) / "work" / "T-1"
        self.ws.mkdir(parents=True)
        (self.ws / "STATUS.md").write_text("# STATUS — T-1\n\n- task-id: T-1\n- pipeline: full\n\n"
                                           "## Stage gates\n\nintake: pending\n\n## Next action\n\nx\n")
        self.tdd = self.ws / "tdd.md"
        self.tdd.write_text(TDD)

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_report_fails_the_gate(self):
        r = run("require", self.ws, "doc-fact-checker", "tdd")
        self.assertEqual(r.returncode, 3)
        self.assertIn("no doc-fact-checker report for tdd", r.stdout)

    def test_latest_report_decides(self):
        r = run("record", self.ws, "doc-fact-checker", "tdd", "--mode", "subagent", "--doc", self.tdd, "-",
                stdin="VERDICT: FINDINGS\n[WRONG] §4.2 …\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.ws / "reviews" / "doc-fact-checker-tdd-1.md").is_file())
        self.assertEqual(run("require", self.ws, "doc-fact-checker", "tdd").returncode, 3)
        run("record", self.ws, "doc-fact-checker", "tdd", "--mode", "subagent", "--doc", self.tdd,
            stdin="VERDICT: PASS\n")
        r = run("require", self.ws, "doc-fact-checker", "tdd")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("PASS (subagent, reviews/doc-fact-checker-tdd-2.md)", r.stdout)
        status = (self.ws / "STATUS.md").read_text()
        self.assertIn("- review.doc-fact-checker.tdd: PASS (subagent, ", status)

    def test_self_pass_is_named(self):
        run("record", self.ws, "scope-auditor", "delivery", "--mode", "self-pass", stdin="VERDICT: PASS\n")
        r = run("require", self.ws, "scope-auditor", "delivery")
        self.assertEqual(r.returncode, 0)
        self.assertIn("self-pass: the author re-read its own work; tell the user", r.stdout)
        self.assertIn("self-pass", run("list", self.ws).stdout)

    def test_every_verdict_in_a_report_must_pass(self):
        run("record", self.ws, "code-reviewer", "repo-a", "--mode", "custom-agent",
            stdin="VERDICT: APPROVE\n…\nVERDICT: FINDINGS\n[SEV-1 blocker] x\n")
        self.assertEqual(run("require", self.ws, "code-reviewer", "repo-a").returncode, 3)

    def test_bad_input_is_refused(self):
        self.assertEqual(run("record", self.ws, "doc-fact-checker", "tdd", "--mode", "vibes", "--doc", self.tdd,
                             stdin="VERDICT: PASS\n").returncode, 1)
        self.assertEqual(run("record", self.ws, "doc-fact-checker", "tdd", "--mode", "subagent", "--doc", self.tdd,
                             stdin="looks fine to me\n").returncode, 1)
        r = run("record", self.ws, "doc-fact-checker", "tdd", "--mode", "subagent", stdin="VERDICT: PASS\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("need --doc", r.stderr)
        self.assertEqual(run("record", self.ws, "doc-fact-checker", "tdd", "--mode", "subagent",
                             "--doc", self.ws / "nope.md", stdin="VERDICT: PASS\n").returncode, 1)
        self.assertEqual(run("record", self.ws, "linter", "tdd", "--mode", "subagent",
                             stdin="VERDICT: PASS\n").returncode, 1)
        self.assertEqual(run("require", self.ws, "doc-fact-checker", "TDD").returncode, 1)
        self.assertFalse((self.ws / "reviews").exists())


    def record_tdd(self, target="tdd", verdict="PASS", extra=()):
        r = run("record", self.ws, "doc-fact-checker", target, "--mode", "subagent", "--doc", "tdd.md", *extra,
                stdin=f"VERDICT: {verdict}\n")
        self.assertEqual(r.returncode, 0, r.stderr)

    def edit(self, old, new):
        text = self.tdd.read_text()
        self.assertIn(old, text)
        self.tdd.write_text(text.replace(old, new))

    def test_report_fingerprints_its_document(self):
        self.record_tdd()
        report = (self.ws / "reviews" / "doc-fact-checker-tdd-1.md").read_text()
        self.assertIn("\nDOC: tdd.md\n", report)
        self.assertRegex(report, r"\nDOC-SHA256: [0-9a-f]{64}\n")
        self.assertIn("  4. Components > 4.2 File naming\n", report)
        self.assertNotIn("Handoff summary", report)
        self.assertNotIn("not a heading", report)

    def test_an_edit_after_the_report_fails_the_gate(self):
        self.record_tdd()
        self.assertEqual(run("require", self.ws, "doc-fact-checker", "tdd").returncode, 0)
        self.edit("Keeps the old file name.", "Uses a new file name.")
        r = run("require", self.ws, "doc-fact-checker", "tdd")
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertIn("tdd.md changed since the latest doc-fact-checker report for tdd", r.stdout)
        self.assertIn("changed  4. Components > 4.2 File naming", r.stdout)
        self.assertNotIn("4.1 orders_pkg", r.stdout)
        self.assertIn("doc changed since", run("list", self.ws).stdout)
        self.record_tdd(extra=("--scope", "§4.2"))
        r = run("require", self.ws, "doc-fact-checker", "tdd")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("REVIEW-SCOPE: §4.2", (self.ws / "reviews" / "doc-fact-checker-tdd-2.md").read_text())

    def test_summary_header_and_comments_are_not_the_body(self):
        self.record_tdd()
        self.edit("- Contract version: 1", "- Contract version: 2\n- Approach: keep the name")
        self.edit("- Status: draft", "- Status: user-approved (2026-11-18)\n- re-approved after /grill: 2 edits")
        self.edit("The job loads orders.", "The job loads orders.\n<!-- note to self -->")
        r = run("require", self.ws, "doc-fact-checker", "tdd")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_changed_names_the_rechecks_scope(self):
        r = run("changed", self.ws, "tdd.md")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("check it whole", r.stdout)
        run("record", self.ws, "doc-fact-checker", "tdd", "--mode", "subagent", "--doc", self.tdd,
            stdin="VERDICT: FINDINGS\n[WRONG]      §4.1 — no such parameter\n[UNVERIFIED-OK] §1 x\n")
        self.edit("Adds a parameter.", "Adds the p_date parameter.")
        self.edit("## 7. Verification approach", "## 6. Interface impact\n\nNone.\n\n## 7. Verification approach")
        out = run("changed", self.ws, self.tdd).stdout
        self.assertIn("changed  4. Components > 4.1 orders_pkg", out)
        self.assertIn("added    6. Interface impact", out)
        self.assertIn("[WRONG]      §4.1 — no such parameter", out)
        self.assertNotIn("UNVERIFIED-OK", out)
        self.assertNotIn("1. Overview", out)
        self.record_tdd()
        self.assertIn("nothing to re-check", run("changed", self.ws, "tdd.md").stdout)

    def test_changed_reads_the_latest_check_of_any_target(self):
        self.record_tdd("tdd")
        self.edit("Adds a parameter.", "Adds the p_date parameter.")
        self.record_tdd("tdd-grill", extra=("--scope", "§4.1"))
        self.edit("Keeps the old file name.", "Uses a new file name.")
        out = run("changed", self.ws, "tdd.md").stdout
        self.assertIn("since reviews/doc-fact-checker-tdd-grill-1.md", out)
        self.assertIn("4.2 File naming", out)
        self.assertNotIn("4.1 orders_pkg", out)

    def test_a_missing_document_fails_the_gate(self):
        self.record_tdd()
        self.tdd.unlink()
        r = run("require", self.ws, "doc-fact-checker", "tdd")
        self.assertEqual(r.returncode, 3)
        self.assertIn("missing  tdd.md", r.stdout)

    def test_a_report_from_before_fingerprints_still_counts(self):
        (self.ws / "reviews").mkdir()
        (self.ws / "reviews" / "doc-fact-checker-tdd-1.md").write_text(
            "# doc-fact-checker — tdd — report 1\n\nMODE: subagent\nDATE: 2026-11-01T10:00Z\n\nVERDICT: PASS\n")
        r = run("require", self.ws, "doc-fact-checker", "tdd")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("predates 0.17.0", r.stdout)
        out = run("changed", self.ws, "tdd.md").stdout
        self.assertIn("only reports from before 0.17.0 (reviews/doc-fact-checker-tdd-1.md)", out)
        self.assertIn("Scope this re-check by hand to the sections edited since", out)


    def test_changed_counts_sections_and_says_when_to_check_whole(self):
        self.record_tdd()
        self.edit("Keeps the old file name.", "Uses a new file name.")
        out = run("changed", self.ws, "tdd.md").stdout
        self.assertIn("1 of 5 sections changed", out)
        self.assertIn("re-check scope:", out)
        for old, new in (("The job loads orders.", "The job loads all orders."), ("Adds a parameter.", "Adds two."),
                         ("| A1 | unit | x |", "| A1 | integration | x |")):
            self.edit(old, new)
        out = run("changed", self.ws, "tdd.md").stdout
        self.assertIn("4 of 5 sections changed", out)
        self.assertIn("more than half the sections changed: re-check the whole document", out)

    def test_current_gates_a_stage_on_the_documents_latest_check(self):
        r = run("current", self.ws, "tdd.md")
        self.assertEqual(r.returncode, 3)
        self.assertIn("never been fact-checked", r.stdout)
        self.record_tdd("tdd", verdict="FINDINGS")
        r = run("current", self.ws, "tdd.md")
        self.assertEqual(r.returncode, 3)
        self.assertIn("says FINDINGS", r.stdout)
        self.record_tdd("tdd")
        self.assertEqual(run("current", self.ws, "tdd.md").returncode, 0)
        self.edit("Keeps the old file name.", "Uses a new file name.")
        r = run("current", self.ws, self.tdd)
        self.assertEqual(r.returncode, 3)
        self.assertIn("changed since reviews/doc-fact-checker-tdd-2.md (1 of 5 sections)", r.stdout)
        self.assertIn("4. Components > 4.2 File naming", r.stdout)
        # a later check of another target (the grill's) makes it current again
        self.record_tdd("tdd-grill", extra=("--scope", "§4.2"))
        r = run("current", self.ws, "tdd.md")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("doc-fact-checker-tdd-grill-1.md", r.stdout)
        # the summary and the header are not the body
        self.edit("- Status: draft", "- Status: user-approved (2026-11-18)")
        self.assertEqual(run("current", self.ws, "tdd.md").returncode, 0)

    def test_current_with_reports_from_before_fingerprints(self):
        (self.ws / "reviews").mkdir()
        legacy = "# doc-fact-checker — {t} — report 1\n\nMODE: subagent\nDATE: 2026-11-01T10:00Z\n\nVERDICT: {v}\n"
        (self.ws / "reviews" / "doc-fact-checker-fdd-1.md").write_text(legacy.format(t="fdd", v="PASS"))
        self.assertEqual(run("current", self.ws, "tdd.md").returncode, 3, "an FDD report says nothing of the TDD")
        (self.ws / "reviews" / "doc-fact-checker-tdd-1.md").write_text(legacy.format(t="tdd", v="FINDINGS"))
        self.assertEqual(run("current", self.ws, "tdd.md").returncode, 3)
        (self.ws / "reviews" / "doc-fact-checker-tdd-grill-1.md").write_text(
            legacy.format(t="tdd-grill", v="PASS").replace("10:00Z", "11:00Z"))
        r = run("current", self.ws, "tdd.md")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("predates 0.17.0", r.stdout)
        self.assertIn("doc-fact-checker-tdd-grill-1.md", run("changed", self.ws, "tdd.md").stdout)

if __name__ == "__main__":
    unittest.main()
