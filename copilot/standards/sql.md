# SQL default standards

> Framework defaults; `.conventions.md` and the surrounding file win.

## Style

- Keywords UPPERCASE, identifiers lowercase; one clause per line for
  multi-table statements; meaningful table aliases (not a/b/c).
- ANSI join syntax; no implicit comma joins.
- No `SELECT *` in persisted code (views, packages, scripts) — explicit columns.

## DDL scripts

- Idempotent where the platform allows: existence checks or documented
  re-runnable pattern; a script that can't be re-run says so in its header.
- Every DDL script pairs with a rollback script (or a header section stating
  the rollback).
- Storage/tablespace clauses only when the repo convention demands them.

## DML scripts

- Wrapped with explicit COMMIT/ROLLBACK strategy stated in the header, plus
  before/after verification queries.
- WHERE clauses reviewed against indexes for large tables; state expected row
  counts in the header so the operator can sanity-check.

## Performance

- New queries against large tables get an EXPLAIN PLAN capture in evidence.
- Hints are a last resort and require a comment with the reason and date.

## Safety

- Scripts never contain credentials or environment-specific connect strings.
- Data-changing scripts name the intended environment class (dev/uat/prod) in
  the header.
