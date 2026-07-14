# PL/SQL default standards

> Framework defaults. A work repo's `.conventions.md` ALWAYS overrides these;
> and the file being edited overrides both — match what's around your change.

## Naming

- Packages `pkg_<domain>`, procedures verbs (`load_…`, `calc_…`), functions
  noun/`get_…` returning one thing.
- Parameters `p_<name>` (with `in`/`out` in the declaration, not the name),
  locals `l_<name>`, globals `g_<name>`, cursors `c_<name>`, types `t_<name>`.
- Constants `co_<name>`; exceptions `e_<name>`.

## Structure

- One package per file pair: `<name>.pks` (spec) / `<name>.pkb` (body); spec
  documents each public routine (purpose, params, raises).
- Header block per object: purpose, author, change history table.
- No business logic in triggers beyond delegation to a package.

## Error handling

- Never `WHEN OTHERS THEN NULL`. `WHEN OTHERS` must log (with `SQLERRM` and
  context) and `RAISE`/`RAISE_APPLICATION_ERROR`.
- Use named exceptions for expected conditions; reserve -20000..-20999 with a
  package-level error-code map.
- Bulk operations: `SAVE EXCEPTIONS` with per-row error logging where partial
  success is acceptable; otherwise fail the batch atomically.

## Transactions

- Commit/rollback only at the outermost orchestration level (top-level proc or
  the calling script) — library code never commits. Exceptions to this must be
  documented in the spec.
- Autonomous transactions only for logging.

## SQL inside PL/SQL

- Bind variables always; no string-concatenated dynamic SQL with external
  input (injection). `EXECUTE IMMEDIATE` requires a comment justifying it.
- `%TYPE`/`%ROWTYPE` anchoring for variables bound to table data.
- Bulk collect with `LIMIT` for large sets; no row-by-row loops over big tables.

## Testing

- utPLSQL preferred where present. Otherwise: an anonymous-block test script
  per change under the repo's test directory, with asserted outcomes (not just
  "runs without error").
