# Impl doc — {TASK_ID}: {TITLE}

- Status: draft | approved {date}
- Inputs: tdd.md (approved {date}), scope-contract.md v{n}
- Branches: {repo-a → feature/T-1}; {repo-b → feature/T-1}
- Cross-repo order: {repo-a before repo-b; between deploys {what callers see} — {ok because …}} | single repo

<!-- AGENT-ONLY: /implement executes this literally and reads it whole, so it
     has no handoff summary. Terse: tables and fragments, no prose, no
     restated design — cite the TDD § that holds it. Exact paths, objects,
     commands and test names; nothing an executor would have to guess.
     standards/writing.md does not apply. "—" = none. -->

## 1. Preconditions

<!-- Task-specific only: grants, reference data, another team's change, a
     change window. Clean repos, branches, environment and rules files are
     /implement's own checks — don't list them. -->
- {—}

## 2. Implementation steps

<!-- In order; one commit-sized step per row, in exactly one repo; producer
     before consumer. A step that leaves the system inconsistent says so in
     Step, and the next step restores it. Repo: the repo's folder name, as
     in STATUS.md branch.<repo>. Files: exact paths, relative to the repo
     root, including the test files the step adds or changes (ses checkpoint
     reads them). Verify: a T# from §3 or a one-line check. -->
| # | Repo | Step | Files / objects | TDD § | Verify | Rollback |
|---|---|---|---|---|---|---|
| 1 | {repo-a} | {add ORDHEAD.EDI_SENT_DATE} | {src/sql/ordhead_add_col.sql} | {§5} | {compile; describe ORDHEAD} | {src/sql/ordhead_drop_col.sql} |
| 2 | {repo-a} | {send proc in PKG_ORDER_EDI} | {src/plsql/pkg_order_edi.pkb, test/ut_pkg_order_edi.pkb} | {§4.1} | {T1} | {git revert} |
| 3 | {repo-b} | {loader reads new column} | {src/py/loader.py} | {§6} | {T2} | {git revert} |

## 3. Test plan

<!-- Every TDD §7 row (A#, G#) → at least one T#. Regression rows re-check
     the callers in TDD §6. The repo's own tooling. A long before/after
     query goes in a fenced block under the table, named by its T#. -->
| T# | Covers | Type | How run | Expected |
|---|---|---|---|---|
| T1 | {A1} | {unit} | {utPLSQL: ut.run('ut_pkg_order_edi')} | {pass} |
| T2 | {A2, G1} | {integration} | {pytest tests/test_loader.py} | {pass} |
| T3 | {§6 callers} | {regression} | {…} | {…} |

## 4. Deployment

| # | Env | Command / action | Verify |
|---|---|---|---|
| 1 | {test} | {…} | {…} |

## 5. Rollback (whole change)

<!-- After deployment. Per repo, reverse dependency order. Name the previous
     version or the script — never "revert the change". -->
1. {repo-b: redeploy src/py/loader.py@{prev-sha}}
2. {repo-a: run src/sql/ordhead_drop_col.sql; recompile PKG_ORDER_EDI@{prev-sha}}
