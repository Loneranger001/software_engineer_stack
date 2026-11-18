---
name: unit-test-results
description: Produce the consolidated unit-test results workbook (XLSX, or ODS) for a task - a Summary sheet with one row per test case (test data, expected result, actual result, data check, outcome), each linked to its own TC<n> sheet holding the test's actual data in cells, the fields to check highlighted and each checked value coloured as expected or differing - rendered from the task's hashed evidence, never typed in. Check mode runs in /implement §3 and /change-request §4 before the test evidence is committed; build mode runs in /deliver §3 and /change-request §5, or standalone for a preview.
argument-hint: "[task-id] [--check] [--ods]"
---

# /unit-test-results — the UT document, from the evidence

> Framework files: `<root>` is what `ses root` prints — run it once. Every
> framework script runs as `ses <command>` (`ses help` lists them). If `ses`
> is not on PATH, use `python3 <skill-dir>/../../bin/ses` in its place —
> `<skill-dir>` is the folder this SKILL.md was loaded from — here and for
> every `ses` below. If neither runs, stop and ask the user (README →
> Install); never guess another path.

One workbook per task, `<ws>/deliverables/<task-id>-unit-test-results.xlsx`:

- **Summary** — one row per test case: TC link, test ID, what it covers,
  type, description, test data, expected result, actual result, data check
  ("6 of 6 checked values as expected"), outcome, mode, where the expected
  value came from, notes.
- **TC1, TC2, …** — one sheet per test case (TC<n> is T<n>; in a change
  request, A<n>), linked both ways with its Summary row: the case's record,
  the values that differ, then **the data itself** — every table the test
  captured laid out in cells, the fields its Check names highlighted, each
  checked value green (as expected), red (differs) or amber (check by eye).
  Other output follows one line per row. Only what cells cannot hold — a
  binary file, or rows past the first 2000 — is a link to the file instead.
- **Evidence** — every file the workbook was built from, its SHA-256 and
  whether a task commit recorded it: the proof, kept off the TC sheets.

The workbook is a **view of evidence the framework already holds**, never a
second record. Every cell comes from the workspace; every outcome is the one
`ses coverage` reads (UNRECORDED, PARTIAL and NO-ORACLE included). The data
check is the reviewer's comparison done for them, not a second verdict: when
it disagrees with a recorded PASS, that is a gap to resolve, never a silent
override. The same evidence always rebuilds the same bytes. Never edit the
workbook by hand and never type a result into it: wrong content is fixed in
the evidence — before its commit — or by a re-run.

## Where it runs

The content is decided long before the workbook is built, and once the test
evidence is committed its hash is fixed — so the work sits at three points:

| When | Stage | What happens |
|---|---|---|
| Plan | /impl-plan §2 | Each T# in impl-doc §3 names its **Test data** (seed, fixture, input rows) and a concrete Expected value. |
| Capture | /implement §3, /change-request §4 | Each test's rows are captured into `evidence/raw/` and its **Test cases** row written, with the fields to **Check**; then `ses ut-workbook <ws> --check`, BEFORE the test-plan commit — the last moment a gap can be filled. |
| Build | /deliver §3, /change-request §5 | After `ses coverage` passes: `ses ut-workbook <ws>`, into `deliverables/`. |

Run standalone (`/unit-test-results <task-id>`) any time after the test-plan
commit for a preview; rebuilding is free and gives identical bytes while the
evidence is unchanged.

## 0. Preamble

1. Locate `<ws>` (`<workspace-root>/work/<id>`; paths from STATUS.md per
   `<root>/core/repo-resolution.md`) and load lessons:
   `ses lessons verify --ws <ws>`.
2. `ses status show <ws>` — the pipeline must be `full` or
   `change-request`; the others run no tests. The test cases are the T# rows
   of impl-doc §3 (full) or the A# criteria of analysis.md (change request).
3. Unknowns follow `<root>/core/decision-protocol.md`. Which rows and fields
   prove a test, and what its expected values are, are cheap to ask — ask
   rather than guess at capture time; nothing can be added afterwards.

## 1. Capture (inside /implement §3 or /change-request §4)

For every test case, while running it:

1. **Capture the rows it read and produced** through `ses capture`, named
   `<run>-T<n>-<what>` (`<run>` is the caller's prefix: `tests-<date>` in
   /implement §3, `cr` in /change-request — there, `A<n>` in place of `T<n>`).
   Relational data goes into cells either way:
   - **CSV** (preferred: no layout to parse, values never wrapped) —
     `--ext csv` with a script that prints CSV: `SET MARKUP CSV ON QUOTE ON`
     (SQL*Plus 12.2+) or `SET SQLFORMAT CSV` (SQLcl), plus `SET FEEDBACK OFF`,
     `SET PAGESIZE 50000`, the query, `EXIT`:
     `ses capture <ev> tests-<date>-T1-actual --ext csv -- sqlplus -s "$SES_DB_CONN" @t1_actual.sql`.
   - **SQL*Plus or SQLcl default output** — the heading line and the dashes
     under it are enough; page breaks are merged back into one table. Keep
     headings on and each column wide enough for its heading (`COLUMN status
     FORMAT A10`): a one-character column prints a one-letter heading.
   - The **input rows** the same way when the test seeds them (`-T1-data`,
     labelled e.g. "Accounts before the run"), and an **expected table** when
     each row expects different values: a fixture in the repo, captured
     through `cat` so it is named and hashed like the rest
     (`ses capture <ev> tests-<date>-T1-expected --ext csv -- cat test/expected/t1.csv`).
     It is the complete expected result: rows are matched on its columns
     that the Check does not name, and a missing or extra row differs.
   - Python: the runner's log, plus a CSV from `csv.writer` for data a
     reader must see. KSH: the script's log, plus each output file through
     `cat`. Capture keeps redaction — never write a data file into
     `evidence/` any other way.
2. **Write its Test cases row** in the evidence file
   (`<root>/templates/test-evidence.md`, "## Test cases"), next to its Result
   row: description, test data, expected and actual result as concrete
   values — "ACC-2 FLAGGED, diff 0.01", never "pass"; **Check**, the fields
   that prove it (`STATUS=P` — every row must hold it; `UNIT_COST` — compared
   with the expected table, or highlighted to check by eye without one;
   separated by `,` or `;`); and **Captured**, each file with an optional
   label (`Accounts before the run: evidence/raw/…-T1-data.csv`). A label
   saying "expected" marks the expected table; one saying before, input,
   seed, setup or fixture marks input, shown but never checked. The expected
   values come from where the Result row's `Expected from` says, never from
   the code under test.
3. **Check before committing**: `ses ut-workbook <ws> --check`. It reads the
   uncommitted evidence and lists every gap: no result, no Test cases row,
   an empty or value-less Test data / Expected result / Actual result, no
   captured file or one missing or outside `evidence/`, a Check it cannot
   read or that names a field no captured table has — and **captured data
   that contradicts a recorded PASS**: then the code, the outcome or the
   expected value is wrong; find which, never relax the Check to fit. Exit 3
   → fill each gap now. Then the caller commits the test evidence as it
   already does, the trailer naming the captured files too.

## 2. Build (inside /deliver §3 or /change-request §5, or standalone)

1. `ses ut-workbook <ws>` — add `--ods` when the `formats` field
   (`ses status get <ws> formats`) names `ods`. It writes
   `<ws>/deliverables/<task-id>-unit-test-results.xlsx` (and `.ods` beside it,
   converted headless by LibreOffice), reads it back to check every part
   parses, and prints its SHA-256. A link to a file the cells cannot hold
   resolves relative to the workbook, so it opens while the workbook sits in
   `deliverables/`; the data in cells needs nothing beside it.
2. Exit 3 → it still wrote the workbook, gaps marked in it; it now also
   checks that each captured file's hash is in a task commit and unchanged.
   The committed evidence cannot be edited (`ses checkpoint verify` would
   report it ALTERED). Either re-run the affected tests under a new run name,
   with their own Test cases rows and their own `tests:` commit — the latest
   result wins — or tell the user each gap and let them accept the workbook
   as it is. A task begun before 0.17.0 has no Test cases tables: its gaps are
   listed, not failed, and its TC sheets show the output its evidence file
   recorded.
3. Exit 127 → LibreOffice is missing for `--ods`; the `.xlsx` is written.
   Tell the user (the install line is in the message), or hand over the
   `.xlsx` — any spreadsheet tool opens it.
4. Report to the user: the path, the SHA-256, the outcome and data-check
   counts, and any case not PASS with its note. The workbook stays in
   `deliverables/`: the workspace never goes into git.

## Fault tolerance

Idempotent and deterministic: a rebuild overwrites the workbook with
identical bytes while the evidence is unchanged, so anyone holding the
evidence can rebuild it and compare the hash. A large captured file shows
its first 2000 rows (`--max-rows N` changes it) and links the full file; the
Check still runs on every row.
