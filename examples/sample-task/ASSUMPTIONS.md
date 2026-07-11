# ASSUMPTIONS — DEMO-1

Proceed-and-log decisions per core/decision-protocol.md: recorded the moment
they are made, presented for ratification at every approval gate. Delivery
with an open entry is a scope-audit finding.

| # | Date | Stage | Assumption | Basis (why ~90%) | Impact if wrong | Reversal step | Status |
|---|---|---|---|---|---|---|---|
| 1 | 2026-07-11 | intake | "Existing rows treated as EUR" (brief §2) means backfill 'EUR' into history, not view-level defaulting | brief says extract "carries" the code per row; datamart consumes raw rows (brief §Background) | backfill DML to remove, view to create instead | drop backfilled values / re-derive; single UPDATE, reversible in dev | ratified (intake gate, 2026-07-11) |
| 2 | 2026-07-11 | research | New column named currency_code CHAR(3) ISO-4217, matching customers.currency_code | repo convention: FK-ish columns mirror parent name+type (customers.currency_code is CHAR(3), evidence/research-columns.txt) | rename column before TDD approval | ALTER TABLE RENAME COLUMN; nothing references it yet | open — present at tech-design gate |

<!--
Counter-example for calibration: "the datamart loader tolerates a 4th
pipe-delimited field" did NOT qualify for this table — external interface
contract = dangerous surface (decision-protocol §3), so it was asked
regardless of confidence and lives as Q2 in the scope contract.
-->
