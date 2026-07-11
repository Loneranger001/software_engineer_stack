#!/usr/bin/env python3
"""Reconcile a balance extract file against the datamart's loaded totals.

Usage:
    reconcile.py <extract_file> <datamart_file>

Both files are pipe-delimited: customer_id|snapshot_date|balance_amt.
Exit codes: 0 balances match, 1 mismatches found, 2 input error.
"""
import logging
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

log = logging.getLogger("reconcile")


def load_balances(path: Path) -> dict[int, Decimal]:
    """Return {customer_id: balance} from a pipe-delimited extract file."""
    balances: dict[int, Decimal] = {}
    with path.open() as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                cust, _snap_date, amt = line.split("|")
                balances[int(cust)] = Decimal(amt)
            except (ValueError, InvalidOperation) as exc:
                raise ValueError(f"{path}:{lineno}: bad row {line!r}") from exc
    return balances


def reconcile(extract: dict[int, Decimal], datamart: dict[int, Decimal]) -> list[str]:
    """Return human-readable mismatch descriptions (empty list = clean)."""
    issues = []
    for cust, amt in sorted(extract.items()):
        dm = datamart.get(cust)
        if dm is None:
            issues.append(f"customer {cust}: missing from datamart")
        elif dm != amt:
            issues.append(f"customer {cust}: extract={amt} datamart={dm}")
    for cust in sorted(set(datamart) - set(extract)):
        issues.append(f"customer {cust}: in datamart but not in extract")
    return issues


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if len(argv) != 3:
        log.error("usage: reconcile.py <extract_file> <datamart_file>")
        return 2
    try:
        extract = load_balances(Path(argv[1]))
        datamart = load_balances(Path(argv[2]))
    except (OSError, ValueError) as exc:
        log.error("%s", exc)
        return 2

    issues = reconcile(extract, datamart)
    for issue in issues:
        log.warning("%s", issue)
    log.info("checked %d customers, %d mismatches", len(extract), len(issues))
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
