# Test Evidence — {TASK_ID}: {what was verified}

- Date: {UTC timestamp}
- Environment: {dev DB / host / local} — mode: live | static-fallback
- Verified by: /verify-code (recipes: {plsql|sql|ksh|python})
- Relates to: impl-doc.md step {N} / acceptance criterion {A#}

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

- Checked against: {rules-checklist.md R#, … | the CR's rules files} — diff lines read: {count}
- Violations fixed before verifying: {R# — file:line — what changed | none}
- Existing names kept that break a rule: {file:line — name — R# | none} (→ PARKED.md)

## Result

- Outcome: PASS | FAIL | PARTIAL
- Assertion checked: {e.g. row count = 1042; USER_ERRORS empty; pytest 14 passed}
- Follow-up (if not PASS): {…}

## Before / after (data changes only)

| Query | Before | After |
|---|---|---|
