"""Tests for scripts/fdd_view.py."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIEW = [sys.executable, str(ROOT / "scripts" / "fdd_view.py")]

DOC = """# FDD — T-1

<!-- guidance for the author -->

<!-- handoff:start -->
## Handoff summary
- Contract version: none
<!-- handoff:end -->

## 5. Component functional design

### 5.1 SEND_ORDERS — changed

- Purpose: send approved orders
<!-- technical:start -->
- Inputs:

  | Input | Business meaning |
  |---|---|
  | run date | business day |

<!-- technical:end -->
- Processing logic:
  1. (new) Select approved orders.

## 15. Sign-off

<!-- technical:start -->
## Appendix A. Source references

| Section | Claim | Source |
|---|---|---|
| §5.1 | x | repo:a.pkb:10 |
<!-- technical:end -->
"""


def render(text, *opts):
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "fdd.md"
        src.write_text(text)
        r = subprocess.run(VIEW + [str(src)] + list(opts), capture_output=True, text=True)
        outs = {p.name: p.read_text() for p in Path(d).glob("fdd.*.md")}
        return r, outs


class FddViewTest(unittest.TestCase):
    def test_business_view_drops_technical_detail(self):
        r, outs = render(DOC)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = outs["fdd.business.md"]
        for gone in ("Handoff summary", "Inputs:", "run date", "Appendix A", "repo:a.pkb", "<!--"):
            self.assertNotIn(gone, out)
        for kept in ("Purpose: send approved orders", "(new) Select approved orders", "## 15. Sign-off"):
            self.assertIn(kept, out)

    def test_technical_view_keeps_detail_but_not_guidance(self):
        r, outs = render(DOC, "--audience", "technical")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = outs["fdd.technical.md"]
        self.assertIn("Inputs:", out)
        self.assertIn("Appendix A", out)
        self.assertNotIn("<!--", out)
        self.assertNotIn("Handoff summary", out)

    def test_appendix_dropped_even_without_markers(self):
        _, outs = render("# FDD\n\n## 1. Purpose\n\nx\n\n## Appendix A. Source references\n\n| a | b |\n")
        self.assertNotIn("Appendix", outs["fdd.business.md"])
        self.assertIn("## 1. Purpose", outs["fdd.business.md"])

    def test_unbalanced_markers_fail(self):
        r, _ = render("# FDD\n<!-- technical:start -->\nx\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("unbalanced", r.stderr)

    def test_template_renders_for_both_audiences(self):
        for audience in ("business", "technical"):
            with tempfile.TemporaryDirectory() as d:
                out = Path(d) / "v.md"
                r = subprocess.run(VIEW + [str(ROOT / "templates" / "fdd.md"), "--audience", audience,
                                           "-o", str(out)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertNotIn("<!--", out.read_text())

    def test_usage_errors(self):
        self.assertEqual(render(DOC, "--audience", "board")[0].returncode, 2)
        self.assertEqual(subprocess.run(VIEW + ["/no/such.md"], capture_output=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
