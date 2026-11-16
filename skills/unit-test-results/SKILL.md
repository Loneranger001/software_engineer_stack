---
name: unit-test-results
description: Produce the consolidated unit-test results workbook (XLSX, or ODS) for a task - a Summary sheet with one row per test case (test data, expected result, actual result, outcome), each linked to its own TC<n> sheet holding the data the test captured - rendered from the task's hashed evidence, never typed in. Check mode runs in /implement §3 and /change-request §4 before the test evidence is committed; build mode runs in /deliver §3 and /change-request §5, or standalone for a preview.
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
  type, description, test data, expected result, actual result, outcome,
  mode, where the expected value came from, evidence file, notes.
- **TC1, TC2, …** — one sheet per test case (TC<n> is T<n>; in a change
  request, A<n>), linked both ways with its Summary row: the case's full
  record, then every file it captured — a `.csv` laid out in cells, a log one
  line per row — each with its SHA-256 and whether a task commit recorded it.

The workbook is a **view of evidence the framework already holds**, never a
second record. Every cell comes from the workspace; every outcome is the one
`ses coverage` reads (UNRECORDED, PARTIAL and NO-ORACLE included). So it
cannot claim a PASS the gate does not, and the same evidence always rebuilds
the same bytes. Never edit the workbook by hand and never type a result into
it: an edited workbook is a document nobody can rebuild or prove. Wrong
content is fixed in the evidence — before its commit — or by a re-run.

## Where it runs

The content is decided long before the workbook is built, and once the test
evidence is committed its hash is fixed — so the work sits at three points:

| When | Stage | What happens |
|---|---|---|
| Plan | /impl-plan §2 | Each T# in impl-doc §3 names its **Test data** (seed, fixture, input rows). |
| Capture | /implement §3, /change-request §4 | Each test's data is captured into `evidence/raw/` and its **Test cases** row written; then `ses ut-workbook <ws> --check`, BEFORE the test-plan commit — the last moment a gap can be filled. |
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
3. Unknowns follow `<root>/core/decision-protocol.md`. What counts as a
   test's data, and which outputs a reader needs to see, are cheap to ask —
   ask rather than guess at capture time; nothing can be added afterwards.

## 1. Capture (inside /implement §3 or /change-request §4)

For every test case, while running it:

1. **Capture the data it read and produced** through `ses capture`, named
   `<run>-T<n>-<what>` (`<run>` is the caller's prefix: `tests-<date>` in
   /implement §3, `cr` in /change-request — there, `A<n>` in place of `T<n>`).
   Tabular data goes in as CSV with `--ext csv`, so it lands in
   `evidence/raw/<name>.csv` and the TC sheet lays it out in cells; anything
   else stays a `.log`. Capture keeps redaction — never write a data file
   into `evidence/` any other way.
   - SQL / PL/SQL: a script that prints the rows as CSV —
     `SET MARKUP CSV ON QUOTE ON` (SQL*Plus 12.2+) or `SET SQLFORMAT CSV`
     (SQLcl), with `SET FEEDBACK OFF`, `SET PAGESIZE 50000`, the query, `EXIT`:
     `ses capture <ev> tests-<date>-T1-actual --ext csv -- sqlplus -s "$SES_DB_CONN" @t1_actual.sql`.
     Capture the input rows the same way (`-T1-data`) when the test seeds them.
   - Python: the test runner's log, plus a CSV printed by `csv.writer` for
     data a reader must see.
   - KSH: the script's log, plus each output file it writes, captured through
     `cat` so it is redacted and named like the rest:
     `ses capture <ev> tests-<date>-T3-extract --ext csv -- cat <out-file>`.
2. **Write its Test cases row** in the evidence file
   (`<root>/templates/test-evidence.md`, "## Test cases"), next to its Result
   row: description, test data, expected result and actual result as
   concrete values — "1 row: ACC-2, diff 0.01", never "pass" — and Captured,
   the `evidence/raw/…` files from step 1. The expected value comes from
   where the Result row's `Expected from` says, never from the code under test.
3. **Check before committing**: `ses ut-workbook <ws> --check`. It reads the
   uncommitted evidence as it stands and lists every gap: no result, no
   Test cases row, an empty or value-less Test data / Expected result /
   Actual result, no captured file, or one that is missing or outside
   `evidence/`. Exit 3 → fill each gap now. Then the caller commits the test
   evidence as it already does, the trailer naming the captured files too.

## 2. Build (inside /deliver §3 or /change-request §5, or standalone)

1. `ses ut-workbook <ws>` — add `--ods` when the `formats` field
   (`ses status get <ws> formats`) names `ods`. It writes
   `<ws>/deliverables/<task-id>-unit-test-results.xlsx` (and `.ods` beside it,
   converted headless by LibreOffice), reads it back to check every part
   parses, and prints its SHA-256.
2. Exit 3 → it still wrote the workbook, gaps marked in it; it now also
   checks that each captured file's hash is in a task commit and unchanged.
   The committed evidence cannot be edited (`ses checkpoint verify` would
   report it ALTERED). Either re-run the affected tests under a new run name,
   with their own Test cases rows and their own `tests:` commit — the latest
   result wins — or tell the user each gap and let them accept the workbook
   as it is. A task begun before 0.17.0 has no Test cases tables: its gaps are
   listed, not failed, and its TC sheets show the evidence file instead.
3. Exit 127 → LibreOffice is missing for `--ods`; the `.xlsx` is written.
   Tell the user (the install line is in the message), or hand over the
   `.xlsx` — any spreadsheet tool opens it.
4. Report to the user: the path, the SHA-256, the outcome counts, and any
   case not PASS with its note. The workbook stays in `deliverables/`: the
   workspace never goes into git.

## Fault tolerance

Idempotent and deterministic: a rebuild overwrites the workbook with
identical bytes while the evidence is unchanged, so anyone holding the
evidence can rebuild it and compare the hash. A large captured file shows
its first 2000 rows (`--max-rows N` changes it) and names the rest, which
stays in the file the sheet cites.
