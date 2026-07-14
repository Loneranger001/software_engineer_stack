# Grill Log — {TASK_ID}: {TITLE}

> Completeness evidence for the TDD: every adversarial scenario confronted,
> and what happened to it. Produced by /grill between tech-design and
> impl-plan. Verdicts: covered | gap-fixed | ask-user → answered | deferred.

- TDD version grilled: tdd.md as of {date/commit}
- Grilled: {date} — phase 2 rounds: {n}

## Scenarios

| # | Category | Scenario (concrete, real objects) | Verdict | Answer / TDD ref |
|---|---|---|---|---|
| 1 | data | {e.g. customers row with NULL currency_code on extract night} | {covered} | {tdd §4.2: fails the account loudly, per Q3} |
| 2 | lifecycle | {e.g. rerun for a date that already has snapshot rows} | {gap-fixed} | {tdd §4.1 updated: delete+insert kept atomic; §7 row T5 added} |

<!-- Categories (min 1 scenario each, or n/a with reason):
     data | lifecycle | interface | temporal | environment | security/ops -->

## Category coverage

| Category | Scenarios | n/a reason (if none) |
|---|---|---|
| data | {#s} | |
| lifecycle | {#s} | |
| interface | {#s} | |
| temporal | {#s} | |
| environment | {#s} | |
| security/ops | {#s} | |

## Terminology resolutions

| Term | Ambiguity | Resolution (user, date) | Recorded in |
|---|---|---|---|
| {balance} | {ledger vs available} | {ledger — user, {date}} | {tdd §1} |

## Deferred by user

| Scenario # | User's deferral (verbatim) | Landed in |
|---|---|---|
| {…} | {"accept the risk for v1, revisit with CR"} | tdd §11 risk R{n} |
