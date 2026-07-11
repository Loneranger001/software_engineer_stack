# sample-repo — nightly balance extract (demo)

Miniature work repo for trying the software-engineer-stack framework.

- `src/sql/balance_snapshot.sql` — snapshot table DDL (re-runnable)
- `src/plsql/pkg_balance.pks|.pkb` — snapshot + extract package
- `bin/run_balance_extract.ksh` — nightly job: snapshot, spool extract file,
  validate row counts, publish
- `tools/reconcile.py` — reconciles the extract file against the datamart load

Try: open Claude Code here, then `/repo-profile`, then
`/intake ../sample-brief.md DEMO-1`.
