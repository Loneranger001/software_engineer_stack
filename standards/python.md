# Python default standards

> Framework defaults; `.conventions.md`, the repo's own tooling config
> (pyproject/setup.cfg/ruff.toml), and the surrounding module win.

## Style & structure

- PEP 8 baseline; the repo's formatter/linter config is authoritative where
  present — run THEIR tools, don't impose new ones.
- Type hints on public function signatures in code that already uses them;
  don't retrofit hints into an unhinted codebase as a side effect.
- Docstrings on public functions/modules: purpose, params, raises.
- No mutable default arguments; context managers for files/connections.

## Errors & logging

- Catch specific exceptions; a bare/broad `except` must log and re-raise or
  have a comment justifying the swallow.
- `logging` module (repo's configured logger), not print, in library/batch
  code. CLI user-facing output may print.
- Batch entry points exit non-zero on failure.

## Database access

- Bind parameters always (`:name` / `%s` per driver) — never string-format SQL
  with external input.
- Connections/cursors in context managers; commit/rollback explicit at the
  orchestration level, mirroring the PL/SQL transaction standard.
- Credentials from env/wallet/config service — never in code or committed config.

## Dependencies

- Use what the repo already depends on before adding anything; new
  dependencies need user agreement and a note in the TDD.

## Testing

- pytest where present: tests colocated per repo convention; new/changed
  behaviour gets a test asserting outcomes, not just "no exception".
- No repo test setup: provide a runnable test script under the repo's test/
  tools directory and wire it into the evidence capture.
