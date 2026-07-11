#!/bin/ksh
######################################################################
# run_balance_extract.ksh — nightly balance snapshot + extract file
#
# Usage:    run_balance_extract.ksh [YYYYMMDD]   (default: today)
# Exit:     0 ok | 1 usage | 2 db failure | 3 file validation failure
######################################################################

SNAP_DATE=${1:-$(date +%Y%m%d)}
case "$SNAP_DATE" in
  [0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]) ;;
  *) print -u2 "usage: $0 [YYYYMMDD]"; exit 1 ;;
esac

: "${EXTRACT_DIR:=/data/finance/extract}"
: "${DB_CONN:?DB_CONN must be set (dev/uat/prod connect string)}"
OUT_FILE="$EXTRACT_DIR/balance_${SNAP_DATE}.dat"
TMP_FILE=$(mktemp "$EXTRACT_DIR/.balance_${SNAP_DATE}.XXXXXX") || exit 2
trap 'rm -f "$TMP_FILE"' EXIT INT TERM

print "$(date '+%Y-%m-%d %H:%M:%S') start extract snap_date=$SNAP_DATE pid=$$"

sqlplus -s "$DB_CONN" <<EOF > "$TMP_FILE"
WHENEVER SQLERROR EXIT FAILURE
WHENEVER OSERROR EXIT FAILURE
SET PAGESIZE 0 FEEDBACK OFF HEADING OFF TRIMSPOOL ON LINESIZE 200
EXEC pkg_balance.extract_daily(TO_DATE('$SNAP_DATE','YYYYMMDD'));
SELECT customer_id || '|' || snapshot_date || '|' || balance_amt
  FROM balance_snapshot
 WHERE snapshot_date = TO_DATE('$SNAP_DATE','YYYYMMDD')
 ORDER BY customer_id;
COMMIT;
EOF
rc=$?
if [ $rc -ne 0 ]; then
  print -u2 "$(date '+%Y-%m-%d %H:%M:%S') ERROR extract failed rc=$rc"
  exit 2
fi

# validate row count against the database before publishing the file
DB_ROWS=$(sqlplus -s "$DB_CONN" <<EOF
WHENEVER SQLERROR EXIT FAILURE
SET PAGESIZE 0 FEEDBACK OFF HEADING OFF
SELECT pkg_balance.get_row_count(TO_DATE('$SNAP_DATE','YYYYMMDD')) FROM dual;
EOF
) || exit 2
FILE_ROWS=$(wc -l < "$TMP_FILE")

if [ "$(print "$DB_ROWS" | tr -d ' ')" -ne "$FILE_ROWS" ]; then
  print -u2 "ERROR row mismatch db=$DB_ROWS file=$FILE_ROWS"
  exit 3
fi

mv "$TMP_FILE" "$OUT_FILE" || exit 3
trap - EXIT
print "$(date '+%Y-%m-%d %H:%M:%S') done rows=$FILE_ROWS file=$OUT_FILE"
exit 0
