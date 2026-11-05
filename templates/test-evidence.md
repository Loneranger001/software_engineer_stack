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

## Before / after (data changes only)

| Query | Before | After |
|---|---|---|
