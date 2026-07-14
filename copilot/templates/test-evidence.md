# Test Evidence — {TASK_ID}: {what was verified}

- Date: {UTC timestamp}
- Environment: {dev DB / host / local} — mode: live | static-fallback
- Verified by: /verify-code (recipes: {plsql|sql|ksh|python})
- Relates to: impl-doc.md step {N} / acceptance criterion {A#}

## What was run

```sh
{exact commands, connect strings redacted}
```

## Raw output

```
{captured output — trimmed to the relevant portion, full output retained
in the same evidence/ directory if large}
```

## Result

- Outcome: PASS | FAIL | PARTIAL
- Assertion checked: {e.g. row count = 1042; USER_ERRORS empty; pytest 14 passed}
- Follow-up (if not PASS): {…}

## Before / after (data changes only)

| Query | Before | After |
|---|---|---|
