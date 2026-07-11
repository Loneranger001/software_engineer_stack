# Requirement Brief — Balance extract: add currency support

- Requested by: Operations (T. Rivera)
- Reference: CHG-2214
- Date: 2026-07-01

## Background

The nightly balance extract (`run_balance_extract.ksh`, calling
`pkg_balance.extract_daily`) writes customer balance snapshots to
`BALANCE_SNAPSHOT` and a flat file consumed by the finance datamart. All
amounts are currently implicit EUR.

## Requirement

Finance is onboarding UK accounts. The extract must carry a currency code for
every balance row:

1. Add a currency code to the snapshot data and the extract file.
2. Existing rows/files should be treated as EUR.
3. The reconciliation tool must report mismatches per currency.

The datamart team asks that the extract file layout change be
backward-compatible "if possible".

## Constraints

- No change to the extract schedule; the job must stay restartable.
- Delivery expected by end of month.
