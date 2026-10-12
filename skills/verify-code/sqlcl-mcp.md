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

## Transactions — assume the worst

Oracle does not document whether `run-sql` autocommits or what happens to
pending work between calls, and the server itself runs DDL on first use
(creating its log table, an implicit commit) and writes a log row per call —
possibly in your session. So a DML check never spans calls and never runs
as a bare statement:

1. `run-sqlcl`: `SET SERVEROUTPUT ON` (once per session).
2. One `run-sql` call per DML check, as an anonymous block. A block is one
   statement, so even an autocommit after it finds nothing to commit:

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

3. Then the open-transaction check (MCP mode step 2) — it must return NULL.
4. No DBMS_OUTPUT comes back → do not fall back to running the DML bare:
   check its predicate with the equivalent `SELECT COUNT(*)` instead, and
   record the check as PARTIAL.

DDL cannot be rolled back and commits implicitly — over MCP it runs only as
an impl-doc deployment step, exactly as in the SQL recipe.

## The audit log table

The server creates `DBTOOLS$MCP_LOG` in the connected schema on first use
and logs every call to it. It is not part of the change: leave it out of
DDL checks, `user_objects` comparisons, and "objects changed" lists, and
never drop or truncate it — pruning it is the user's or DBA's call.
