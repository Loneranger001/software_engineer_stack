# /verify-code — SQLcl MCP server (SQL Developer for VS Code)

> Loaded from "MCP mode" in `skills/verify-code/SKILL.md` when the database
> MCP server is SQLcl's — its tools are `list-connections`, `connect`,
> `disconnect`, `run-sql`, and `run-sqlcl` (SQLcl 25.2+; SQL Developer for
> VS Code sets it up). Everything in MCP mode still applies; this file adds
> what is specific to SQLcl. Tool names and arguments can differ between
> SQLcl builds — where the tool schemas your harness shows disagree with
> this file, the schemas win.

## Tools

| Tool | Use |
|---|---|
| `list-connections` | Read-only: confirm the recorded connection name exists. Never a menu to pick from. |
| `connect` | Open a session on exactly the recorded connection, by name. |
| `run-sql` | SQL and PL/SQL — one statement or block per call (multi-statement input is not documented). |
| `run-sqlcl` | SQLcl commands (`SHOW ERRORS`, `SET SERVEROUTPUT ON`, …). |
| `disconnect` | End the session — only with no transaction pending. |

`run-sql` and `run-sqlcl` also take `mcp_client` and `model`: fill them
truthfully (the harness's name; the model's name and version) — they are
written to the audit log below.

## Connecting

- Connections are SQL Developer for VS Code's saved connections, and the
  server can only use one saved with its password. `connect` failing on
  credentials → ask the user to save the password on that connection in the
  extension. Never ask for, or accept, a password in chat.
- After `connect`, run the identity query (MCP mode step 1) before anything
  else.

## Restrict level 4 — the MCP default

The server starts at restrict level 4: `@`/`@@`/`START` scripts, `HOST`,
`SPOOL`, and many other commands are refused. So:

- Compile by sending source through `run-sql`, one call per unit — package
  spec, then body. Split a file at its `/` terminator lines and send each
  unit without the `/`.
- Then the `user_errors` query through `run-sql` — the PASS check — and
  `SHOW ERRORS` through `run-sqlcl` where it is allowed.
- A refused command is not a failure of the code under test: record it and
  use the alternative. Never ask the user to lower the restrict level for
  you — it is their security setting (starting the server with `-R 1`
  allows scripts but not host commands, if they choose to).

## Transactions — pending work outlives the call

`run-sql` does NOT autocommit (confirmed by the user on SQL Developer for
VS Code's server, 2026-10): DML stays pending in the session across later
calls until a `COMMIT` or `ROLLBACK` — and anything that commits implicitly
commits it too: any DDL (including compiling code with `CREATE OR REPLACE`)
and `disconnect`. The server also runs DDL itself on first use (creating its
log table), so the first call after `connect` is the identity query, never
DML. Order the work so compiles and other DDL come first and DML checks
after — never interleaved.

1. `run-sqlcl`: `SET SERVEROUTPUT ON` (once per session).
2. Preferred — one `run-sql` call per DML check, as an anonymous block that
   rolls back before it returns, so nothing is ever left pending between
   calls:

   ```sql
   DECLARE
     l_before NUMBER; l_rows NUMBER; l_after NUMBER;
   BEGIN
     SELECT COUNT(*) INTO l_before FROM <table> WHERE <predicate>;
     <the DML statement>;
     l_rows := SQL%ROWCOUNT;
     SELECT COUNT(*) INTO l_after FROM <table> WHERE <predicate>;
     ROLLBACK;
     DBMS_OUTPUT.PUT_LINE('before=' || l_before || ' rows=' || l_rows || ' after=' || l_after);
   EXCEPTION
     WHEN OTHERS THEN ROLLBACK; RAISE;
   END;
   ```

3. No DBMS_OUTPUT comes back → run the check as consecutive `run-sql`
   calls with NOTHING else in between: before-count, the DML, after-count,
   then `ROLLBACK`. No compile, other DDL, `run-sqlcl` command, or
   `disconnect` before that `ROLLBACK` — each could commit the DML. An
   error at any point → `ROLLBACK` is the very next call.
4. Either way, then the open-transaction check (MCP mode step 2) — it must
   return NULL before you do anything else or end your turn.

DDL cannot be rolled back and commits implicitly. Run it in dev as the SQL
recipe says — never while a DML check is pending (ordering above) — and a
script mixing DDL with DML only as an impl-doc deployment step.

## The audit log table

The server creates `DBTOOLS$MCP_LOG` in the connected schema on first use
and logs every call to it. It is not part of the change: leave it out of
DDL checks, `user_objects` comparisons, and "objects changed" lists, and
never drop or truncate it — pruning it is the user's or DBA's call.
