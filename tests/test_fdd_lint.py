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


ORDERED = """# FDD — T-1

## 1. Why this change and what it does

### 1.2 What changes and why

#### C1. Orders reach the vendor each night

- Why: a vendor can start work sooner.

## 3. Sequence of events

| # | When | What happens | Who or what does it | Detail |
|---|---|---|---|---|
| E1 | 02:00 | (changed, C1) The run sends the orders. | ORDER_EDI job | §4.1 steps 1–2 |
| E2 | after E1 | The report lists each skipped order. | Exception report | §4.2 |

```mermaid
flowchart LR
    E1[E1 Send orders, see §4.2] --> E2
```

## 4. Step by step

### 4.1 SEND — changed

1. Send the approved orders.

### 4.2 REPORT

1. List the skipped orders.

<!-- handoff:start -->
## Appendix B. Handoff summary
- Changes: C1 nightly
<!-- handoff:end -->
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

    def test_run_told_in_order_passes(self):
        self.assertEqual(lint(ORDERED).returncode, 0, lint(ORDERED).stdout)

    def test_steps_without_a_sequence_of_events(self):
        r = lint(ORDERED.replace("## 3. Sequence of events", "## 3. Overview"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("[SEQUENCE] no 'Sequence of events' section", r.stdout)

    def test_component_no_event_names(self):
        r = lint(ORDERED.replace("| §4.2 |", "| §9 |"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("[SEQUENCE] §4.2 REPORT: no event in the sequence of events names it", r.stdout)
        self.assertNotIn("§4.1 SEND", r.stdout)

    def test_components_out_of_run_order(self):
        swapped = ORDERED.replace("| §4.1 steps 1–2 |", "| §4.X |").replace("| §4.2 |", "| §4.1 |") \
                         .replace("| §4.X |", "| §4.2 |")
        r = lint(swapped)
        self.assertIn("[SEQUENCE] §4.2 REPORT: runs before §4.1 in the sequence of events", r.stdout)

    def test_change_not_marked_in_the_run(self):
        r = lint(ORDERED.replace("(changed, C1)", "(changed)"))
        self.assertIn("[SEQUENCE] C1: no event or step is marked with it", r.stdout)
        # the handoff summary naming C1 does not count as marking it in the run
        self.assertEqual(lint(ORDERED.replace("(changed, C1)", "(changed)"), "--allow", "SEQUENCE").returncode, 0)

    def test_sequence_check_needs_the_step_by_step_section(self):
        # an FDD laid out before 0.20.0 ("Component functional design") is not held to it
        self.assertEqual(lint(ORDERED.replace("Step by step", "Component functional design")
                              .replace("## 3. Sequence of events", "## 3. Actors")).returncode, 0)

    def test_usage_errors(self):
        self.assertEqual(subprocess.run(LINT, capture_output=True).returncode, 2)
        self.assertEqual(lint("x", "--allow", "BOGUS").returncode, 2)
        self.assertEqual(subprocess.run(LINT + ["/no/such/file.md"], capture_output=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
