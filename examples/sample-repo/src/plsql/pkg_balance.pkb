CREATE OR REPLACE PACKAGE BODY pkg_balance AS

  PROCEDURE extract_daily(p_snapshot_date IN DATE DEFAULT TRUNC(SYSDATE)) IS
    l_rows PLS_INTEGER := 0;
  BEGIN
    -- restartable: replace any existing snapshot for the date
    DELETE FROM balance_snapshot WHERE snapshot_date = TRUNC(p_snapshot_date);

    INSERT INTO balance_snapshot (snapshot_id, snapshot_date, customer_id, balance_amt)
    SELECT seq_balance_snapshot.NEXTVAL,
           TRUNC(p_snapshot_date),
           c.customer_id,
           NVL(SUM(t.amount), 0)
      FROM customers c
      LEFT JOIN transactions t
        ON t.customer_id = c.customer_id
       AND t.txn_date < TRUNC(p_snapshot_date) + 1
     WHERE c.status = 'ACTIVE'
     GROUP BY c.customer_id;

    l_rows := SQL%ROWCOUNT;
    IF l_rows = 0 THEN
      RAISE_APPLICATION_ERROR(-20001, 'extract_daily: no active customers for '
        || TO_CHAR(p_snapshot_date, 'YYYY-MM-DD'));
    END IF;
    -- commit is owned by the caller (run_balance_extract.ksh sqlplus block)
  END extract_daily;

  FUNCTION get_row_count(p_snapshot_date IN DATE) RETURN NUMBER IS
    l_cnt NUMBER;
  BEGIN
    SELECT COUNT(*) INTO l_cnt
      FROM balance_snapshot
     WHERE snapshot_date = TRUNC(p_snapshot_date);
    RETURN l_cnt;
  END get_row_count;

END pkg_balance;
/
