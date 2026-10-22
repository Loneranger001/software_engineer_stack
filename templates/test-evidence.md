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

- New code (new file, object, or unit) — checked against the rules: {unit — R#, … | none}
- Modified code (inside an existing unit) — matched to its conventions: {unit — convention followed | none}
- Violations fixed before verifying: {file:line — rule or convention — what changed | none}
- Rule breaches carried by a unit's convention, or existing names that break a rule: {unit or name — R# | none} (→ PARKED.md)

## Result

- Outcome: PASS | FAIL | PARTIAL
- Assertion checked: {e.g. row count = 1042; USER_ERRORS empty; pytest 14 passed}
- Follow-up (if not PASS): {…}

## Before / after (data changes only)

| Query | Before | After |
|---|---|---|
