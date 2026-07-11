# Implementation Document — {TASK_ID}: {TITLE}

- Status: draft | user-approved ({date})
- Inputs: tdd.md (approved), scope-contract.md v{n}
- Branch: {work-repo branch for this task}

> /implement executes this document step by step. Each step must be small enough
> to verify before moving on, and each has its own rollback note.

## 1. Preconditions

- [ ] TDD approved
- [ ] Work repo clean, branch created: `{branch}`
- [ ] Dev environment reachable ({SES_DB_CONN / SES_KSH_HOST as applicable}) — or static-fallback mode acknowledged
- [ ] .conventions.md present (run /repo-profile if not)

## 2. Implementation steps

<!-- Ordered. One row per commit-sized unit of work. -->
| # | Step | Files / objects | Verification (per step) | Rollback |
|---|---|---|---|---|
| 1 | {DDL: add column} | {src/sql/…} | {compile + query in dev, evidence/step1-*} | {drop column script} |
| 2 | {modify package body} | {src/plsql/…} | {compile, utPLSQL test T1} | {git revert / redeploy previous version} |

## 3. Test plan

### Unit / component tests

| Test | Covers (acceptance criterion) | How run | Expected result |
|---|---|---|---|
| T1 | A1 | {utPLSQL / pytest / ksh invocation} | {…} |

### Integration / end-to-end

| Test | Scenario | How run | Expected result |
|---|---|---|---|

### Regression

{What existing behaviour must be re-checked, and how.}

## 4. Deployment / delivery steps

| # | Step | Environment | Command / action | Verification |
|---|---|---|---|---|

## 5. Rollback plan (whole change)

{Exact steps to restore the previous state if the change must be backed out
after deployment — scripts, previous versions, data restoration.}

## 6. Evidence to capture

- Per-step verification outputs → `evidence/step<N>-<desc>.txt`
- Test runs → `evidence/tests-<date>.txt` (template: test-evidence.md)
- Before/after samples for data changes
