"""Tests for scripts/prose_lint.py."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINT = [sys.executable, str(ROOT / "scripts" / "prose_lint.py")]
READER_TEMPLATES = ("fdd", "tdd", "howto", "kb-article", "understanding-doc", "release-notes")

CLEAN = """# Functional Design Document — T-1: send approved orders

- Inputs: scope-contract.md v1 + research-notes.md

<!-- guidance may say anything: research identified the task-owned id / key -->

<!-- handoff:start -->
## Handoff summary
- Purpose: research says the task-owned message/publication identity changes
<!-- handoff:end -->

## In short

Today, an order waits for the weekly run. After this change, the nightly run
sends each approved order on the day that the buyer approves it.

### Before and after this change

| Aspect | Before / now | After this change |
|---|---|---|
| How orders reach vendors | Weekly, by hand | Each night, by EDI |

## 5.1 SEND_ORDERS — changed

1. Find every approved purchase order that the system has not sent to its vendor.
2. Check that the vendor accepts EDI orders (BR1). If it does not, skip the
   order (EX1).
- The file goes to `/data/out/po_{yyyymmdd}.dat` through PL/SQL and I/O,
  e.g. the vendor gets it as src/out/po.dat. The value is n/a for returns.

> The client brief says: "research and/or utilize the existing interface".

```mermaid
flowchart TD
    A[research / task] --> B
```

## Appendix A. Source references

| Claim | Source |
|---|---|
| research found the resend rule | research-notes §3 |
"""


def lint(text, *opts):
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "doc.md"
        f.write_text(text)
        return subprocess.run(LINT + list(opts) + [str(f)], capture_output=True, text=True)


def body(text):
    return f"# Doc\n\n## 1. Section\n\n{text}\n"


class ProseLintTest(unittest.TestCase):
    def test_plain_prose_passes(self):
        r = lint(CLEAN)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("prose lint ok", r.stdout)

    def test_reader_templates_pass(self):
        # templates seed the phrasing of every document made from them
        for name in READER_TEMPLATES:
            with self.subTest(template=name):
                r = subprocess.run(LINT + [str(ROOT / "templates" / f"{name}.md")],
                                   capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_the_users_examples_are_caught(self):
        r = lint(body("Research identified no implementation of the resend rule."))
        self.assertIn(":5: [PROCESS] Research", r.stdout)
        r = lint(body("The job stores the task owned message / publication identity."))
        self.assertIn("[PROCESS] task owned", r.stdout)
        self.assertIn("[SLASH] message / publication", r.stdout)

    def test_each_kind_is_caught(self):
        long_sentence = " ".join(["word"] * 26) + "."
        cases = {
            "PROCESS": "The scope contract excludes returns.",
            "SLASH": "The buyer approves and/or rejects the order.",
            "LONG": long_sentence,
            "PARAGRAPH": " ".join(["The job runs."] * 7),
            "WORDS": "The job utilizes the vendor table.",
        }
        for kind, text in cases.items():
            with self.subTest(kind=kind):
                r = lint(body(text))
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(f":5: [{kind}]", r.stdout)

    def test_more_process_shapes(self):
        for text in ("This task adds a column.", "We found two callers.", "Analysis shows a retry.",
                     "The code shows a retry.", "See PARKED.md for the rest.", "Run /grill again.",
                     "The fact-checker passed it.", "The workspace holds the file."):
            with self.subTest(text=text):
                self.assertIn("[PROCESS]", lint(body(text)).stdout, text)

    def test_numbered_step_has_the_shorter_limit(self):
        step = " ".join(["word"] * 22) + "."
        self.assertIn("[LONG] 22 words", lint(body(f"1. {step}")).stdout)
        self.assertEqual(lint(body(f"- {step}")).returncode, 0)
        self.assertEqual(lint(body(step)).returncode, 0)

    def test_sentences_span_wrapped_lines_and_report_their_first_line(self):
        text = "Short one.\nThe " + " ".join(["word"] * 12) + "\n" + " ".join(["word"] * 13) + "."
        r = lint(body(text))
        self.assertIn(":6: [LONG] 26 words", r.stdout)

    def test_abbreviations_and_ids_do_not_split_or_count_as_slashes(self):
        text = "Step 2 of §5.1 sends the file, e.g. the order file. Values are A/B in PL/SQL."
        r = lint(body(text))
        self.assertNotIn("[LONG]", r.stdout)
        self.assertNotIn("A/B", r.stdout)

    def test_slash_at_sentence_end_is_caught_but_a_file_name_is_not(self):
        self.assertIn("[SLASH]", lint(body("The job is restarted/recovered.")).stdout)
        self.assertEqual(lint(body("The job writes out/po.dat each night.")).returncode, 0)

    def test_headings_and_table_headers_are_skipped(self):
        text = "### Rollback / undo\n\n| Read/Write | Command / query |\n|---|---|\n| read | none |\n"
        self.assertEqual(lint(body(text)).returncode, 0)

    def test_table_body_cells_are_checked(self):
        text = "| Aspect | Value |\n|---|---|\n| Entry points | proc / script |\n"
        self.assertIn(":7: [SLASH]", lint(body(text)).stdout)

    def test_source_sections_and_header_are_skipped(self):
        for heading in ("## Sources", "## Verification of this article", "## Appendix B. Evidence"):
            with self.subTest(heading=heading):
                text = f"# Doc\n\n- Inputs: research-notes.md\n\n{heading}\n\n| research found it | x |\n"
                self.assertEqual(lint(text).returncode, 0)

    def test_document_without_sections_is_still_checked(self):
        self.assertEqual(lint("# Doc\n\nThis task adds a column.\n").returncode, 1)

    def test_line_numbers_survive_multiline_comments(self):
        r = lint("# Doc\n\n## 1\n\n<!--\n\n\n-->\nThe workspace holds it.\n")
        self.assertIn(":9: [PROCESS]", r.stdout)

    def test_allow_skips_only_named_kinds(self):
        text = body("This task utilizes the table.")
        r = lint(text, "--allow", "PROCESS")
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("[PROCESS]", r.stdout)
        self.assertIn("[WORDS]", r.stdout)
        self.assertEqual(lint(text, "--allow=process,words").returncode, 0)

    def test_usage_errors(self):
        self.assertEqual(subprocess.run(LINT, capture_output=True).returncode, 2)
        self.assertEqual(lint("x", "--allow", "BOGUS").returncode, 2)
        self.assertEqual(subprocess.run(LINT + ["/no/such/file.md"], capture_output=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
