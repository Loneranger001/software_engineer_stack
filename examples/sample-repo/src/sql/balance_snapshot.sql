-- balance_snapshot.sql
-- Purpose: snapshot table for the nightly customer balance extract.
-- Rollback: drop_balance_snapshot.sql (drops table and sequence)
-- Environment class: dev/uat/prod (DDL, re-runnable guard below)

DECLARE
  l_cnt NUMBER;
BEGIN
  SELECT COUNT(*) INTO l_cnt FROM user_tables WHERE table_name = 'BALANCE_SNAPSHOT';
  IF l_cnt = 0 THEN
    EXECUTE IMMEDIATE q'[
      CREATE TABLE balance_snapshot (
        snapshot_id   NUMBER        NOT NULL,
        snapshot_date DATE          NOT NULL,
        customer_id   NUMBER        NOT NULL,
        balance_amt   NUMBER(15,2)  NOT NULL,
        created_at    DATE          DEFAULT SYSDATE NOT NULL,
        CONSTRAINT pk_balance_snapshot PRIMARY KEY (snapshot_id),
        CONSTRAINT uq_balance_snapshot UNIQUE (snapshot_date, customer_id)
      )]';
    EXECUTE IMMEDIATE 'CREATE SEQUENCE seq_balance_snapshot';
  END IF;
END;
/
