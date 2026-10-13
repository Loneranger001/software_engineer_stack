#!/usr/bin/env python3
"""fdd_lint.py — keep a functional design document at the functional level.

A functional design (templates/fdd.md) says WHAT the system does, WHEN, and
under WHICH business rules; HOW it is coded belongs in the TDD. Drift toward
code is gradual — a pasted cursor here, a VARCHAR2(30) there — so this script
flags it mechanically. It is a floor, not the judgment: a code-shaped step
written in plain words passes the lint and still fails the skill's litmus test
(skills/func-design/SKILL.md, "Abstraction rules").

Usage:
    fdd_lint.py [--allow KIND[,KIND...]] <fdd.md> [<fdd.md> ...]

Findings, one per line as `<file>:<line>: [KIND] <match> — <fix>`:
    CODE-BLOCK  a fenced block other than ```mermaid
    SQL         SQL statements, clauses, DDL, or SQL functions (SELECT … FROM,
                UPDATE … SET, CREATE TABLE, NVL(…), …)
    PLSQL       PL/SQL constructs (:=, BEGIN/END;, cursors, BULK COLLECT, %TYPE,
                exception handlers, ORA- error codes, …)
    SHELL       shell syntax ($(…), ${VAR}, $VAR, [[ … ]], pipes into grep/awk/sed,
                redirections, shebangs, if/fi)
    PYTHON      Python syntax (def/class/import lines, self., try:/except …:)
    DATATYPE    column data types or precision (VARCHAR2(30), NUMBER(12,4), CLOB,
                a "Data type" table column) — state the business limit in words

--allow skips the named kinds — only for content a format the repo's rules or
the user prescribe requires (recorded in the workspace, see the skill).
HTML comments (template guidance) and ```mermaid block contents are ignored.
Uppercase-only patterns are deliberate: "select approved orders from the
queue" is prose, "SELECT … FROM" is SQL.

Exit codes: 0 clean, 1 findings, 2 usage error.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

I = re.I
FIX = {
    "CODE-BLOCK": "describe the behaviour as numbered steps; only ```mermaid diagrams belong in an FDD",
    "SQL": "say which records are selected or changed and why, naming table.column where it pins the meaning",
    "PLSQL": "describe the business effect, not the mechanism",
    "SHELL": "describe what the script does and when, not its commands",
    "PYTHON": "describe what the program does, not its code",
    "DATATYPE": "state the business limit in words (\"up to 30 characters\"); types belong in the TDD",
}

RULES: list[tuple[str, re.Pattern[str]]] = [(k, re.compile(p, f)) for k, p, f in (
    # --- SQL (keywords uppercase-only; function calls any case) ---
    ("SQL", r"\bSELECT\b.*\bFROM\b", 0),
    ("SQL", r"^\s*SELECT\s", 0),
    ("SQL", r"\bINSERT\s+INTO\b", 0),
    ("SQL", r"\bUPDATE\s+[\w.$#]+\s+SET\b", 0),
    ("SQL", r"\bDELETE\s+FROM\b", 0),
    ("SQL", r"\bMERGE\s+INTO\b", 0),
    ("SQL", r"\bTRUNCATE\s+TABLE\b", 0),
    ("SQL", r"\b(GROUP|ORDER)\s+BY\b", 0),
    ("SQL", r"\b(CREATE|ALTER|DROP)\s+(OR\s+REPLACE\s+)?(GLOBAL\s+TEMPORARY\s+)?"
            r"(TABLE|VIEW|INDEX|PACKAGE|PROCEDURE|FUNCTION|TRIGGER|SEQUENCE|TYPE|SYNONYM)\b", 0),
    ("SQL", r"\b(NVL2?|DECODE|COALESCE|TO_CHAR|TO_DATE|TO_NUMBER|TRUNC|SUBSTR|INSTR|ROWNUM)\s*\(", I),
    # --- PL/SQL ---
    ("PLSQL", r":=", 0),
    ("PLSQL", r"^\s*(BEGIN|DECLARE)\s*$", I),
    ("PLSQL", r"\bEND(\s+(LOOP|IF|CASE)|\s+[A-Za-z_]\w*)?\s*;", 0),
    ("PLSQL", r"\bBULK\s+COLLECT\b|\bFORALL\b|\bEXECUTE\s+IMMEDIATE\b|\bPRAGMA\b|\bREF\s+CURSOR\b", I),
    ("PLSQL", r"\bCURSOR\s+\w+\s+IS\b|\b(OPEN|CLOSE)\s+\w+\s*;|\bFETCH\s+\w+\s+(BULK\s+COLLECT\s+)?INTO\b", I),
    ("PLSQL", r"\bFOR\s+\w+\s+IN\b.*\bLOOP\b", 0),
    ("PLSQL", r"%(ROW)?TYPE\b", I),
    ("PLSQL", r"\bEXCEPTION\s+WHEN\b|\bWHEN\s+(OTHERS|NO_DATA_FOUND|TOO_MANY_ROWS|DUP_VAL_ON_INDEX)\b", I),
    ("PLSQL", r"\b(RAISE_APPLICATION_ERROR|SQLERRM|SQLCODE|DBMS_OUTPUT|PLS_INTEGER|BINARY_INTEGER)\b", I),
    ("PLSQL", r"\b(COMMIT|ROLLBACK)\s*;", I),
    ("PLSQL", r"\bORA-\d{5}\b", 0),
    # --- shell ---
    ("SHELL", r"\$\([^)]*\)|\$\{\w+[^}]*\}", 0),
    ("SHELL", r"\$[A-Z_][A-Z0-9_]+\b", 0),
    ("SHELL", r"\[\[\s.*\s\]\]", 0),
    ("SHELL", r"^\s*#!/", 0),
    ("SHELL", r"\|\s*(grep|egrep|awk|sed|cut|xargs|tee|wc)\b", 0),
    ("SHELL", r"2>&1|>\s*/dev/null", 0),
    ("SHELL", r"^\s*(if|while|for)\s.*;\s*(then|do)\b|^\s*(fi|done|esac)\s*$", 0),
    ("SHELL", r"\bexport\s+[A-Za-z_]\w*=", 0),
    # --- Python ---
    ("PYTHON", r"^\s*def\s+\w+\s*\(|^\s*class\s+\w+\s*[(:]", 0),
    ("PYTHON", r"^\s*import\s+[\w.]+(\s+as\s+\w+)?\s*$|^\s*from\s+[\w.]+\s+import\s+[\w*, ]+$", 0),
    ("PYTHON", r"\bself\.\w+|^\s*except(\s+[\w.]+(\s+as\s+\w+)?)?\s*:\s*$|^\s*(try|finally)\s*:\s*$", 0),
    # --- data types ---
    ("DATATYPE", r"\b(N?VARCHAR2?|N?CHAR|NUMBER|RAW|TIMESTAMP)\s*\(\s*\d+", 0),
    ("DATATYPE", r"\b(N?CLOB|BLOB|BFILE)\b", 0),
    ("DATATYPE", r"\|\s*(data\s*type|datatype|type\s*/\s*length|length\s*/\s*precision|precision)\s*\|", I),
)]
KINDS = tuple(FIX)
FENCE = re.compile(r"^\s*(```|~~~)\s*([\w+-]*)")


def strip_comments(text: str) -> str:
    """Blank out HTML comments, keeping their newlines so line numbers stay true."""
    return re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)


def lint(text: str, allow: frozenset[str] = frozenset()) -> list[tuple[int, str, str]]:
    """Return (line, kind, matched text) for every code-level construct."""
    found: list[tuple[int, str, str]] = []
    fence: str | None = None  # the opening marker while inside a fenced block
    for n, line in enumerate(strip_comments(text).splitlines(), 1):
        m = FENCE.match(line)
        if fence is not None:
            if m and m.group(1) == fence and not m.group(2):
                fence = None
            continue
        if m:
            fence = m.group(1)
            if m.group(2).lower() != "mermaid" and "CODE-BLOCK" not in allow:
                found.append((n, "CODE-BLOCK", line.strip()))
            continue
        for kind, rx in RULES:
            if kind in allow:
                continue
            hit = rx.search(line)
            if hit:
                found.append((n, kind, hit.group(0).strip()))
                break  # one finding per line is enough to send the author back to it
    return found


def main(argv: list[str]) -> int:
    allow: set[str] = set()
    args = list(argv)
    if args and args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    while args and args[0].startswith("--allow"):
        opt = args.pop(0)
        val = opt.split("=", 1)[1] if "=" in opt else (args.pop(0) if args else "")
        kinds = {k.strip().upper() for k in val.split(",") if k.strip()}
        bad = kinds - set(KINDS)
        if not kinds or bad:
            print(f"error: --allow takes kinds from {', '.join(KINDS)}; got '{val}'", file=sys.stderr)
            return 2
        allow |= kinds
    if not args:
        print("usage: fdd_lint.py [--allow KIND[,KIND]] <fdd.md> [...]", file=sys.stderr)
        return 2
    total = 0
    for a in args:
        p = Path(a)
        if not p.is_file():
            print(f"error: no such file: {p}", file=sys.stderr)
            return 2
        for n, kind, match in lint(p.read_text(encoding="utf-8"), frozenset(allow)):
            print(f"{p}:{n}: [{kind}] {match[:80]} — {FIX[kind]}")
            total += 1
    if total:
        print(f"{total} code-level finding(s) — lift each to the functional level "
              f"(not reworded to dodge the pattern)", file=sys.stderr)
        return 1
    print(f"fdd lint ok ({len(args)} file(s){', allowed: ' + ','.join(sorted(allow)) if allow else ''})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
