# Grill Log — {TASK_ID}: {TITLE}

> Completeness evidence for the TDD: every adversarial scenario confronted,
> and what happened to it. Produced by /grill between tech-design and
> impl-plan. Verdicts: covered | gap-fixed | out-of-scope | ask-user →
> answered | deferred. A testable gap-fixed or answered row #n becomes TDD
> §7 row `G<n>`.

- TDD version grilled: tdd.md as of {date/commit}
- Grilled: {date} — phase 2 rounds: {n}

## Scenarios

<!-- Upstream miss: the stage that should have caught this (research,
     tech-design, intake) or `-` — /retro turns these into lessons. -->
| # | Category | Scenario (concrete, real objects) | Verdict | Answer / TDD ref | Upstream miss |
|---|---|---|---|---|---|
| 1 | data | {e.g. customers row with NULL currency_code on extract night} | {covered} | {tdd §4.2: fails the account loudly, per Q3} | {-} |
| 2 | lifecycle | {e.g. rerun for a date with snapshot rows: §4.1's delete and insert commit separately, so a failure between leaves the date empty} | {gap-fixed} | {tdd §4.1: one transaction — a defect, the replace behaviour is unchanged; §7 row G2 added} | {tech-design} |

<!-- Categories (min 1 scenario each, or n/a with reason):
     data | lifecycle | interface | temporal | environment | security/ops | deploy/rollback -->

## Category coverage

| Category | Scenarios | n/a reason (if none) |
|---|---|---|
| data | {#s} | |
| lifecycle | {#s} | |
| interface | {#s} | |
| temporal | {#s} | |
| environment | {#s} | |
| security/ops | {#s} | |
| deploy/rollback | {#s} | |

## Terminology resolutions

| Term | Ambiguity | Resolution (user, date) | Recorded in |
|---|---|---|---|
| {balance} | {ledger vs available} | {ledger — user, {date}} | {tdd §1} |

## Deferred by user

| Scenario # | User's deferral (verbatim) | Landed in |
|---|---|---|
| {…} | {"accept the risk for v1, revisit with CR"} | tdd §11 risk R{n}; PARKED.md |
