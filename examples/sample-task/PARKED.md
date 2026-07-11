# PARKED — out-of-scope findings for DEMO-1

Items discovered during work that are OUTSIDE the scope contract.
Logged here for later triage; never acted on within this task.

| Date | Found during | Finding | Suggested follow-up |
|---|---|---|---|
| 2026-07-11 | research | run_balance_extract.ksh interpolates $SNAP_DATE into the sqlplus heredoc; format is validated by the case guard, but a bind-style approach would be more robust (bin/run_balance_extract.ksh:24-31) | raise a hardening CR |
| 2026-07-11 | research | reconcile.py loads both files fully into memory; fine at current volumes (~50k rows, evidence/research-volumes.txt) but worth a note for datamart growth | monitor; no action |
