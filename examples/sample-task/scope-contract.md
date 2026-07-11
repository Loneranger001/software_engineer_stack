# Scope Contract — DEMO-1: Balance extract currency support

> The single source of scope truth for this task. Approved by the user at intake.
> Every later stage re-reads this file. Work not covered here goes to PARKED.md.

- Source brief: ./brief.md (from examples/sample-brief.md, CHG-2214)
- Approved by: user on 2026-07-11
- Version: 1

## Objective

Carry a currency code on every balance snapshot row and extract file line so
finance can onboard UK (GBP) accounts; existing data defaults to EUR; the
reconciliation tool reports mismatches per currency.

## In scope

| # | Item | Source (brief section / requester) |
|---|---|---|
| S1 | Add `currency_code` to BALANCE_SNAPSHOT, backfilled 'EUR' for existing rows | brief §Requirement 1–2 |
| S2 | `pkg_balance.extract_daily` populates currency per customer account | brief §Requirement 1 |
| S3 | Extract file gains currency as a 4th pipe-delimited field (backward-compatible: appended, not inserted) | brief §Requirement 1, datamart ask |
| S4 | `reconcile.py` groups and reports mismatches per currency | brief §Requirement 3 |

## Out of scope / non-goals

| # | Item | Why excluded |
|---|---|---|
| N1 | Multi-currency conversion/aggregation (FX rates) | brief asks to carry the code, not convert amounts |
| N2 | Changes to extract schedule or job orchestration | brief §Constraints |
| N3 | Datamart-side loader changes | owned by datamart team |

## Acceptance criteria

| # | Criterion | Verifies | How verified |
|---|---|---|---|
| A1 | BALANCE_SNAPSHOT has currency_code NOT NULL; pre-existing rows read 'EUR' | S1 | user_tab_columns + before/after query in evidence/ |
| A2 | extract_daily writes GBP for a GBP test account, EUR otherwise | S2 | anonymous-block test in dev, output captured |
| A3 | Extract file line = cust|date|amount|currency; datamart sample load accepts it | S3 | run job in dev, file diff vs previous layout |
| A4 | reconcile.py exits 1 and names the currency on a seeded mismatch | S4 | pytest run captured to evidence/ |

## Interfaces & objects expected to change

| Object | Type | Change |
|---|---|---|
| BALANCE_SNAPSHOT | table | add currency_code + backfill |
| pkg_balance (spec+body) | PL/SQL package | extract_daily populates currency |
| bin/run_balance_extract.ksh | KSH | spool SELECT gains the 4th field |
| tools/reconcile.py | Python | per-currency reporting |

## Assumptions & open questions

| # | Assumption / Question | Status | Resolution |
|---|---|---|---|
| Q1 | Where does an account's currency come from? | answered | customers.currency_code exists, populated (research evidence/research-columns.txt) |
| Q2 | Is appending a 4th field acceptable to the datamart loader? | answered | yes — loader ignores trailing fields (datamart team, 2026-07-11) |
| Q3 | Should e_no_customers behaviour change for currency-less accounts? | answered | no — fail the row's account loudly, see TDD risk table |

## Constraints

- Job stays restartable (brief §Constraints); follow sample-repo conventions.

## History

| Version | Date | Change | Approved by |
|---|---|---|---|
| 1 | 2026-07-11 | Initial contract | user |
