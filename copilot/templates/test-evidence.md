# Test Evidence — {TASK_ID}: {what was verified}

- Date: {UTC timestamp}
- Environment: {dev DB / host / local} — mode: live | static-fallback
- Verified by: /verify-code (recipes: {plsql|sql|ksh|python})
- Relates to: impl-doc.md step {N} / acceptance criterion {A#}

## What was run

```sh
{exact commands, connect strings redacted}
```

## Output (capture.sh summary)

```
{scripts/capture.sh output per command: command (connect string redacted),
exit code, line count, error-line matches, last lines — not the full log}
```

Raw logs: `evidence/raw/{name}.log` (full output, opened only to diagnose)

## Result

- Outcome: PASS | FAIL | PARTIAL
- Assertion checked: {e.g. row count = 1042; USER_ERRORS empty; pytest 14 passed}
- Follow-up (if not PASS): {…}

## Before / after (data changes only)

| Query | Before | After |
|---|---|---|
