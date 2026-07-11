---
name: verify-code
description: Verify PL/SQL, SQL, KSH, or Python code by running it against live dev environments where available (Oracle via SQL*Plus/SQLcl, Unix host for KSH, project Python), with documented static fallbacks. Captures evidence files. Used by /implement and /change-request, or standalone.
argument-hint: <file(s) or directory to verify> [--task <task-id>]
---

# /verify-code — run it, don't trust it

Per-language verification recipes. Live mode proves the code works; static
fallback proves it parses and conforms. Every run produces an evidence file
(`${CLAUDE_PLUGIN_ROOT}/templates/test-evidence.md`) into the task's
`evidence/` directory (or `./verify-evidence/` when standalone).

## Environment resolution (all recipes)

| Variable | Purpose |
|---|---|
| `SES_DB_CONN` | SQL*Plus/SQLcl connect string for the dev schema |
| `SES_KSH_HOST` | optional `user@host` for running KSH remotely via ssh |
| `SES_PY` | Python interpreter for the work repo (venv-aware) |

- Never echo passwords; prefer wallet/OS auth; redact connect strings in
  evidence files.
- Variable unset or connection fails → use the static fallback and record
  `mode: static-fallback` plus the reason in the evidence file. Fallback mode
  is a degraded PASS: tell the user which live checks remain outstanding.
- Only run against DEV/test environments. If `SES_DB_CONN` looks production-like
  (name contains prod/prd), stop and confirm with the user first.

## PL/SQL (.pks .pkb .sql packages/procs/triggers)

**Live**:
1. Compile: `sqlplus -s "$SES_DB_CONN" @file` (or `sql -s` for SQLcl).
2. Check: `SELECT * FROM user_errors WHERE name = '<OBJECT>' ORDER BY sequence, line;`
   — must return no rows. Include `SHOW ERRORS` output in evidence.
3. Warnings count too: compile with `ALTER SESSION SET plsql_warnings='ENABLE:ALL'`
   when the repo's conventions allow, and triage warnings.
4. Tests: if the repo has utPLSQL, run the suite for the object
   (`ut.run('<schema>.<test_pkg>')`); otherwise run the impl-doc's test
   queries/anonymous blocks.

**Static fallback**: careful read-through against `standards/plsql.md` +
`.conventions.md`: balanced blocks, exception handling present, no implicit
commits in unexpected places, object/parameter naming. State clearly this did
not compile anything.

## SQL (queries, DML, DDL scripts)

**Live**:
1. Queries: `EXPLAIN PLAN FOR ...` then `SELECT * FROM table(dbms_xplan.display)`;
   run the query with a row limit; capture plan + row count + sample rows.
2. DML: run inside a transaction — capture before-count, execute, after-count,
   then ROLLBACK unless the task explicitly deploys data (then follow the
   impl-doc step, with before/after evidence).
3. DDL: run in dev; verify via `user_objects`/`user_tab_columns` queries.

**Static fallback**: syntax review, join/predicate sanity, standards check;
flag full scans on known-large tables from research notes.

## KSH (.ksh .sh with ksh shebang)

**Live**:
1. Syntax: `ksh -n script.ksh` (locally or `ssh "$SES_KSH_HOST" ksh -n <
   script.ksh`).
2. `shellcheck -s ksh script.ksh` if available — note: shellcheck's ksh support
   is partial; treat its findings as advisory, not gospel.
3. Execute the script's dry-run/help mode if it has one; else run in a scratch
   directory with test inputs per the impl-doc test plan. Capture exit code +
   output.

**Static fallback**: `ksh -n` locally if ksh exists, else careful review:
quoting, `set -e`-equivalents per repo convention, exit-code propagation
through pipes, cleanup traps.

## Python

**Live**:
1. Interpreter: `$SES_PY` else the repo's venv else `python3`.
2. Repo tooling first (from `.conventions.md`): its pytest config, ruff/flake8,
   mypy. Run the narrowest test selection covering the change, then the
   broader suite if fast.
3. No repo tooling: `python -m py_compile <files>`, `ruff check` if available,
   and run the impl-doc's test snippets.

**Static fallback**: `python -m py_compile` (almost always available), plus
import-graph sanity and standards review.

## Output contract

For each file verified, append to the evidence file: recipe used, mode
(live/static-fallback), commands run, trimmed output, PASS/FAIL/PARTIAL, and
the assertion that justifies the verdict. /implement and /change-request treat
anything but PASS as a blocker to resolve or escalate.
