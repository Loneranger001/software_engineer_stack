"""Tests for scripts/review_version.py and its hook in scripts/handoff.py."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RV = [sys.executable, str(ROOT / "scripts" / "review_version.py")]
HANDOFF = [sys.executable, str(ROOT / "scripts" / "handoff.py")]
sys.path.insert(0, str(ROOT / "scripts"))
import review_version  # noqa: E402

AGENT = """# FDD — T-1: send approved orders

- Status: draft

<!-- handoff:start -->
## Handoff summary
- Contract version: none
- Requirements: FR1; FR2
- Business rules: BR1
<!-- handoff:end -->

## 2.1 Functional requirements

| # | Requirement | Source |
|---|---|---|
| FR1 | Send approved orders nightly | S1 |
| FR2 | Never resend an order | S2 |

## 6. Business rules

| # | Rule | Applies to | When violated |
|---|---|---|---|
| BR1 | Vendor must accept EDI | §5.1 step 2 | skipped |
"""

REVIEW = """# Send approved orders — functional design

- Status: draft
- For: buyers

<!-- guidance: every part ends with a covers: anchor -->

## In short

The nightly run sends each approved order on the day of approval.
<!-- covers: FR1 -->

## How it works

1. The system finds every approved order that it has not sent. <!-- covers: FR1, FR2 -->
2. It sends an order only if the vendor accepts EDI orders.

| What happens | Who finds out |
|---|---|
| The vendor does not accept EDI | The buyer <!-- covers: BR1 --> |
"""


class ReviewVersionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self.tmp.name)
        self.agent = self.ws / "fdd.md"
        self.review = self.ws / "fdd.review.md"
        self.agent.write_text(AGENT)
        self.review.write_text(REVIEW)

    def tearDown(self):
        self.tmp.cleanup()

    def run_rv(self, *args):
        return subprocess.run(RV + [str(a) for a in args], capture_output=True, text=True)

    def stamp(self):
        r = self.run_rv("stamp", self.agent)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_in_step_review_version_passes(self):
        self.stamp()
        self.assertIn("- Written from: fdd.md @ ", self.review.read_text())
        r = self.run_rv("check", self.agent)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("review versions ok", r.stdout)
        self.assertIn("about 1 page(s)", r.stdout)
        self.assertEqual(self.run_rv("check", self.review).returncode, 0)  # either file names the design

    def test_missing_stamp_fails(self):
        r = self.run_rv("check", self.agent)
        self.assertEqual(r.returncode, 1)
        self.assertIn("ses review-version stamp", r.stderr)

    def test_body_change_makes_it_stale_but_header_change_does_not(self):
        self.stamp()
        self.agent.write_text(AGENT.replace("- Status: draft", "- Status: user-approved (2026-10-23)"))
        self.assertEqual(self.run_rv("check", self.agent).returncode, 0)
        self.agent.write_text(AGENT.replace("Never resend an order", "Never resend a sent order"))
        r = self.run_rv("check", self.agent)
        self.assertEqual(r.returncode, 1)
        self.assertIn("changed after this review version was written", r.stderr)

    def test_restamp_replaces_the_line(self):
        self.stamp()
        self.agent.write_text(AGENT + "\n## 9. Exceptions\n\nNone.\n")
        self.stamp()
        self.assertEqual(self.review.read_text().count("- Written from:"), 1)
        self.assertEqual(self.run_rv("check", self.agent).returncode, 0)

    def test_coverage_problems(self):
        cases = {
            "leaves out FR2": REVIEW.replace("FR1, FR2", "FR1"),
            "anchors BR9": REVIEW.replace("covers: BR1", "covers: BR1, BR9"),
            "shows BR1 in its text": REVIEW.replace("EDI orders.", "EDI orders (BR1)."),
        }
        for expected, text in cases.items():
            with self.subTest(expected=expected):
                found = review_version.coverage_problems(AGENT, text)
                self.assertTrue(any(expected in p for p in found), found)
        self.assertEqual(review_version.coverage_problems(AGENT, REVIEW), [])

    def test_ids_in_handoff_and_comments_are_not_required(self):
        agent = AGENT.replace("- Business rules: BR1", "- Business rules: BR1; BR7") + "<!-- | BR8 | x | -->\n"
        self.assertEqual(review_version.coverage_problems(agent, REVIEW), [])

    def test_render_strips_anchors_guidance_and_stamp(self):
        self.stamp()
        r = self.run_rv("render", self.agent)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = (self.ws / "deliverables" / "fdd.review.md").read_text()
        for gone in ("<!--", "covers:", "Written from"):
            self.assertNotIn(gone, out)
        self.assertIn("1. The system finds every approved order that it has not sent.\n", out)
        self.assertIn("| The vendor does not accept EDI | The buyer |", out)
        self.assertIn("day of approval.\n\n## How it works", out)
        custom = self.ws / "out.md"
        self.assertEqual(self.run_rv("render", self.review, "-o", custom).returncode, 0)
        self.assertTrue(custom.is_file())

    def test_workspace_check_covers_only_designs_with_a_review_version(self):
        (self.ws / "tdd.md").write_text(AGENT)
        self.stamp()
        r = self.run_rv("check", self.ws)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("(1 design(s))", r.stdout)

    def test_explicit_design_without_review_version_fails(self):
        self.review.unlink()
        r = self.run_rv("check", self.agent)
        self.assertEqual(r.returncode, 1)
        self.assertIn("no review version", r.stderr)

    def test_handoff_check_enforces_the_review_version(self):
        r = subprocess.run(HANDOFF + ["check", str(self.agent)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("ses review-version stamp", r.stderr)
        self.stamp()
        r = subprocess.run(HANDOFF + ["check", str(self.ws)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.review.unlink()  # no review version yet: the handoff check is unchanged
        r = subprocess.run(HANDOFF + ["check", str(self.agent)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_review_templates_cover_their_agent_templates(self):
        for agent, review in (("fdd", "fdd-review"), ("tdd", "tdd-review")):
            with self.subTest(template=review):
                found = review_version.coverage_problems((ROOT / "templates" / f"{agent}.md").read_text(),
                                                         (ROOT / "templates" / f"{review}.md").read_text())
                self.assertEqual(found, [])

    def test_usage_errors(self):
        self.assertEqual(subprocess.run(RV, capture_output=True).returncode, 2)
        self.assertEqual(self.run_rv("bogus", self.agent).returncode, 2)
        self.assertEqual(self.run_rv("check", self.ws / "nope.md").returncode, 2)
        self.assertEqual(self.run_rv("render", self.agent, "-o").returncode, 2)


if __name__ == "__main__":
    unittest.main()
