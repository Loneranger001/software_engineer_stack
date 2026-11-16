# Test Evidence — {TASK_ID}: {what was verified}

- Date: {UTC timestamp}
- Environment: {dev DB / host / local} — mode: live | static-fallback
- Verified by: /verify-code (recipes: {plsql|sql|ksh|python})
- Relates to: {repo} — impl-doc.md step {N} | test T{n} — criterion {A# | TS# | G#}

## What was run

```sh
{exact commands, connect strings redacted}
```

## Output (ses capture summary)

```
{ses capture output per command: command (connect string redacted),
exit code, line count, error-line matches, last lines — not the full log}
```

Raw logs: `evidence/raw/{name}.log` (full output, opened only to diagnose)

## Rules check (code changes)

- New files — checked against the rules: {file — R#, … | none}
- Existing files — matched to their own conventions: {file — convention followed | none}
- Violations fixed before verifying: {file:line — rule or convention — what changed | none}
- Rule breaches carried by a file's convention, or existing names that break a rule: {file or name — R# | none} (→ PARKED.md)

## Result

<!-- One row per test (T#) or, in a change request, per criterion (A#) this
     file proves — `ses coverage` reads this table. Outcome is PASS | FAIL |
     PARTIAL | NOT-RUN: a test that could not run is a NOT-RUN row, never
     left out. Mode is live | static-fallback; a static-fallback PASS counts
     as PARTIAL, since the code parsed but did not run.
     Expected from: where the expected value came from — hand-derived from
     the scenario, the spec (contract A#, FDD BR#), a fixture's known
     contents. NEVER the code under test: an expectation computed by the same
     query, function or logic agrees with the code whether it is right or
     not. A PASS without it counts as NO-ORACLE in `ses coverage`.
     A step's own check with no T# keeps the bullet below only. -->
| Test or criterion | Outcome | Mode | Expected from | Assertion checked |
|---|---|---|---|---|
| {T1 \| A1} | {PASS \| FAIL \| PARTIAL \| NOT-RUN} | {live \| static-fallback} | {hand-derived: 2 of 5 lines post \| spec: contract A3 \| fixture: 3 known rows} | {e.g. row count = 1042; USER_ERRORS empty; pytest 14 passed} |

- Outcome: PASS | FAIL | PARTIAL | NOT-RUN
- Follow-up (if not PASS): {…}

## Test cases

<!-- One row per T# (or A#) in the Result table — what the unit-test
     workbook shows for it (`ses ut-workbook`: its Summary row and TC sheet).
     Write it now: once a commit hashes this file, a gap can only be filled by
     a re-run under a new name. `ses ut-workbook <ws> --check` lists gaps.
     Test data: the input — seed or fixture file, rows, parameters.
     Expected result / Actual result: concrete values, never just "pass";
     the expected value as its `Expected from` source gives it.
     Check: the fields of the captured rows to check, separated by , or ; —
     COL=VALUE (every row must hold it), or COL alone (compared with the
     expected table if one is captured, else highlighted to check by eye).
     The TC sheet colours each checked value green or red.
     Captured: the evidence/ files holding the data the test read and
     produced, each optionally labelled — `<label>: evidence/raw/<file>`.
     Rows go in as a CSV (`ses capture … --ext csv`) or as SQL*Plus/SQLcl
     output with its headings; either is laid out in cells. A label saying
     "expected" marks the expected table (the complete expected result, e.g.
     a repo fixture captured through `cat`); one saying before, input, seed,
     setup or fixture marks the input, shown but not checked. A step's own
     check with no T# has no row here. -->
| Test | Description | Test data | Expected result | Actual result | Check | Captured |
|---|---|---|---|---|---|---|
| {T1 \| A1} | {a 0.01 difference is flagged} | {fixture test/seed_bal.sql: 3 accounts} | {ACC-2 FLAGGED, diff 0.01; others OK} | {ACC-2 FLAGGED, diff .01} | {STATUS, DIFF} | {Accounts before the run: evidence/raw/tests-2026-11-16-T1-data.csv, Reconciliation rows: evidence/raw/tests-2026-11-16-T1-actual.csv, Expected rows: evidence/raw/tests-2026-11-16-T1-expected.csv} |

## Before / after (data changes only)

| Query | Before | After |
|---|---|---|
