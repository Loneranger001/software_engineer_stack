CREATE OR REPLACE PACKAGE pkg_balance AS
  ------------------------------------------------------------------
  -- pkg_balance: nightly customer balance snapshot & extract
  --
  -- Change history
  --   2025-03-10  init            initial version
  ------------------------------------------------------------------

  -- Snapshot all active customer balances for p_snapshot_date and
  -- write the extract rows. Restartable: an existing snapshot for the
  -- date is replaced atomically.
  -- Raises: e_no_customers when no active customers found.
  PROCEDURE extract_daily(p_snapshot_date IN DATE DEFAULT TRUNC(SYSDATE));

  -- Count of rows written for a snapshot date (used by the ksh wrapper
  -- to validate the extract file).
  FUNCTION get_row_count(p_snapshot_date IN DATE) RETURN NUMBER;

  e_no_customers EXCEPTION;
  PRAGMA EXCEPTION_INIT(e_no_customers, -20001);
END pkg_balance;
/
