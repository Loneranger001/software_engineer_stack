"""Tests for scripts/fdd_lint.py."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINT = [sys.executable, str(ROOT / "scripts" / "fdd_lint.py")]

CLEAN = """# Functional Design Document — T-1: send approved orders

<!-- guidance may quote code: SELECT * FROM ordhead; l_x := 1; -->

## 4. Functional overview

```mermaid
flowchart TD
    A[Select approved orders] --> B{Vendor EDI-enabled?}
```

## 5.1 ORDER_EDI_SQL.SEND_ORDERS — changed

1. Select every purchase order that is approved (`ORDHEAD.STATUS` = 'A') and
   not yet sent (`ORDHEAD.EDI_SENT_IND` = 'N'), ordered by vendor.
2. Import the vendor file; an order failing BR1 is skipped and reported (EX1).
3. The order number (up to 10 digits) is written to the file; at the end; the
   run reports the count. Every queued order is sent
   except the following:
4. Rerun: already-sent orders are not resent.
"""


def lint(text, *opts):
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "fdd.md"
        f.write_text(text)
        return subprocess.run(LINT + list(opts) + [str(f)], capture_output=True, text=True)


class FddLintTest(unittest.TestCase):
    def test_functional_prose_passes(self):
        r = lint(CLEAN)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("fdd lint ok", r.stdout)

    def test_template_passes(self):
        r = subprocess.run(LINT + [str(ROOT / "templates" / "fdd.md")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_each_kind_is_caught(self):
        cases = {
            "CODE-BLOCK": "```sql\nanything\n```",
            "SQL": "1. Run `SELECT order_no FROM ordhead WHERE status = 'A'`.",
            "PLSQL": "2. Set l_count := l_count + 1 for each order.",
            "SHELL": "3. The script calls `$(date +%Y%m%d)` to name the file.",
            "PYTHON": "def send_orders(conn):",
            "DATATYPE": "| ORDHEAD | ORDER_NO | NUMBER(10) | order id |",
        }
        for kind, line in cases.items():
            with self.subTest(kind=kind):
                r = lint(f"# FDD\n\n{line}\n")
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(f":3: [{kind}]", r.stdout)

    def test_more_code_shapes(self):
        for line in ("FOR r IN c_po LOOP", "END LOOP;", "BULK COLLECT INTO l_tab",
                     "UPDATE ordhead SET status = 'C'", "CREATE OR REPLACE PACKAGE x",
                     "raises ORA-00001 on duplicates", "WHEN OTHERS THEN log it",
                     "uses NVL(qty, 0)", "l_rec ordhead%ROWTYPE", "grep -c x f | wc -l",
                     "export ORACLE_SID=DEV", "fi", "except ValueError as e:",
                     "| Column | Data type | Meaning |"):
            with self.subTest(line=line):
                self.assertEqual(lint(f"# FDD\n\n{line}\n").returncode, 1, line)

    def test_code_inside_mermaid_or_comments_ignored(self):
        text = "```mermaid\nflowchart TD\n  A[\"SELECT x FROM y\"] --> B\n```\n<!--\nl := 1;\n-->\n"
        self.assertEqual(lint(text).returncode, 0)

    def test_one_finding_per_code_block(self):
        r = lint("# FDD\n\n```plsql\nBEGIN\n  l := 1;\nEND;\n```\n")
        self.assertEqual(r.stdout.count("[CODE-BLOCK]"), 1)
        self.assertNotIn("[PLSQL]", r.stdout)

    def test_line_numbers_survive_multiline_comments(self):
        r = lint("<!--\n\n\n-->\nx := 1\n")
        self.assertIn(":5: [PLSQL]", r.stdout)

    def test_allow_skips_only_named_kinds(self):
        text = "| ORDHEAD | ORDER_NO | NUMBER(10) |\n\nl := 1\n"
        r = lint(text, "--allow", "DATATYPE")
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("[DATATYPE]", r.stdout)
        self.assertIn("[PLSQL]", r.stdout)
        self.assertEqual(lint(text, "--allow=datatype,plsql").returncode, 0)

    def test_usage_errors(self):
        self.assertEqual(subprocess.run(LINT, capture_output=True).returncode, 2)
        self.assertEqual(lint("x", "--allow", "BOGUS").returncode, 2)
        self.assertEqual(subprocess.run(LINT + ["/no/such/file.md"], capture_output=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
