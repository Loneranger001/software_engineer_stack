"""ut_data.py — a test's captured files as blocks a sheet shows, and its Check against them (imported by ut_workbook.py).

Not a command. `ses ut-workbook` reads every file a test captured into blocks:

  grid   rows and columns: a .csv/.tsv, or a table that SQL*Plus or SQLcl
         printed in its default layout — a heading line, a line of dashes under
         each column, then the rows (page breaks that repeat the headings are
         merged back into one table)
  text   any other output, one line per row
  file   what cells cannot hold — a binary file, or a table wider than a
         sheet: the sheet links it instead

and compares the grids with the test's Check — the Test cases table's Check
cell, items separated by , or ;

  COL            a field to check by eye: highlighted, nothing compared
  COL=VALUE      every row's COL must equal VALUE ('quote' a value holding , or ;
                 — an empty VALUE or NULL means the cell is empty)
  expected table a captured file whose label says "expected" (or named *-expected.csv):
                 the complete expected result. A Check naming columns compares
                 those and matches rows on the table's other columns (its key);
                 no Check compares every column, row by row in order. A row
                 missing from the actual data, or one the table does not have,
                 differs.

Numbers compare as numbers (Oracle prints 0.5 as .5), an empty cell equals
NULL, anything else is exact text. A file whose label says before, input, seed,
setup or fixture, or starts with "data" (unless it says after or actual), is
the test's input — "Accounts before the run": shown, never checked.
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

MAX_COLS = 16384
BINARY_EXT = {".xlsx", ".xls", ".ods", ".zip", ".gz", ".tgz", ".bz2", ".xz", ".7z", ".tar", ".pdf", ".png",
              ".jpg", ".jpeg", ".gif", ".bmp", ".dmp", ".bin", ".exe", ".so", ".dll", ".class", ".jar", ".pyc"}
DASHES = re.compile(r"^\s*-+(?:\s+-+)*\s*$")
TABLE_END = re.compile(r"^\s*(\d+ rows? selected\.?|no rows selected\.?)\s*$", re.I)
ITEM = re.compile(r"""\s*([A-Za-z_][\w$#]*)\s*(?:=\s*('(?:[^']|'')*'|"[^"]*"|[^,;]*?))?\s*(?:[,;]|$)""")
NUMBER = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
NULLS = ("", "null", "(null)")
EXPECTED_ROLE = re.compile(r"\bexpected\b", re.I)
INPUT_ROLE = re.compile(r"^(test )?data\b|\b(before|input|seed|setup|fixture)\b", re.I)
ACTUAL_ROLE = re.compile(r"\b(after|actual)\b", re.I)


@dataclass
class Block:
    kind: str                                   # grid | text | file
    rows: list[list[str]] = field(default_factory=list)   # grid: headings first; text: one line per row
    reason: str = ""                            # file: why cells cannot hold it
    marks: dict[tuple[int, int], str] = field(default_factory=dict)   # (row, col) → match | differ | eye
    checked: set[int] = field(default_factory=set)                    # columns the Check compares
    keys: set[int] = field(default_factory=set)                       # columns matching rows to the expected table


@dataclass
class Captured:
    label: str
    rel: str
    role: str                                   # actual | expected | input
    blocks: list[Block]
    lines: int


@dataclass
class Check:
    column: str
    value: str | None                           # None: check by eye


@dataclass
class Result:
    matched: int = 0
    eye: int = 0
    differ: list[tuple[str, str, str, str, str]] = field(default_factory=list)   # where, row, field, expected, actual
    unknown: list[str] = field(default_factory=list)
    checked: bool = False                       # was there anything to check at all

    def summary(self) -> tuple[str, str]:
        """(text, PASS | FAIL | WARN | '') for the Data check cell."""
        if not self.checked:
            return "", ""
        n = self.matched + len(self.differ)
        eye = f"{self.eye} value(s) to check by eye" if self.eye else ""
        if self.differ:
            return f"{len(self.differ)} of {n} checked value(s) differ" + (f"; {eye}" if eye else ""), "FAIL"
        if self.matched:
            return f"{self.matched} of {n} checked value(s) as expected" + (f"; {eye}" if eye else ""), "PASS"
        if eye:
            return eye, "WARN"
        return "no checked field in the captured data", "WARN"


# --- reading ----------------------------------------------------------------------

def role_of(label: str) -> str:
    """expected (the label says "expected"), input (before, input, seed, setup, fixture, or it starts with
    "data" — unless it also says after or actual), else actual."""
    if EXPECTED_ROLE.search(label):
        return "expected"
    return "input" if INPUT_ROLE.search(label) and not ACTUAL_ROLE.search(label) else "actual"


def read(path: Path) -> tuple[list[Block], int]:
    """(blocks, rows in the source) of a captured file."""
    raw = path.read_bytes()
    if path.suffix.lower() in BINARY_EXT or b"\x00" in raw[:8192]:
        return [Block("file", reason="it is a binary file")], 0
    text = raw.decode("utf-8", errors="replace")
    if text.count("�") > max(8, len(text) // 100):
        return [Block("file", reason="it is not UTF-8 text")], 0
    if path.suffix.lower() in (".csv", ".tsv"):
        try:
            rows = list(csv.reader(io.StringIO(text), dialect="excel-tab" if path.suffix.lower() == ".tsv" else "excel"))
            while rows and not any(c.strip() for c in rows[-1]):
                rows.pop()
            if max((len(r) for r in rows), default=0) > MAX_COLS:
                return [Block("file", reason=f"it is wider than a sheet's {MAX_COLS} columns")], len(rows)
            return [Block("grid", rows)], len(rows)
        except csv.Error:
            pass
    lines = text.splitlines()
    return tables(lines), len(lines)


def _spans(dashes: str) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in re.finditer(r"-+", dashes)]


def _fits(line: str, spans: list[tuple[int, int]]) -> bool:
    """Only spaces where the dash line has gaps, nothing past its end: the line belongs to this table
    (SQL*Plus wraps a value inside its column, so a row never runs past the dashes)."""
    if line[:spans[0][0]].strip() or len(line.rstrip()) > spans[-1][1]:
        return False
    return all(not line[e:n].strip() for (_s, e), (n, _e) in zip(spans, spans[1:]))


def _cut(line: str, spans: list[tuple[int, int]]) -> list[str]:
    ends = [s for s, _e in spans[1:]] + [len(line)]
    return [line[s:end].strip() for (s, _e), end in zip(spans, ends)]


def tables(lines: list[str]) -> list[Block]:
    """Text, with each SQL*Plus/SQLcl default-format table in it turned into a grid."""
    blocks: list[Block] = []
    text: list[str] = []

    def flush() -> None:
        if any(t.strip() for t in text):
            blocks.append(Block("text", [[t] for t in text]))
        text.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        if i + 1 < len(lines) and line.strip() and not DASHES.match(line) and DASHES.match(lines[i + 1]):
            spans = _spans(lines[i + 1])
            head = _cut(line, spans) if _fits(line, spans) else []
            if head and all(head):
                rows, j = [], i + 2
                while j < len(lines) and lines[j].strip() and not TABLE_END.match(lines[j]) and _fits(lines[j], spans):
                    rows.append(_cut(lines[j], spans))
                    j += 1
                last = blocks[-1] if blocks else None
                if last and last.kind == "grid" and last.rows[0] == head and not any(t.strip() for t in text):
                    text.clear()                # the same headings after a page break: one table
                    last.rows.extend(rows)
                else:
                    flush()
                    blocks.append(Block("grid", [head] + rows))
                i = j
                continue
        text.append(line)
        i += 1
    flush()
    return blocks or [Block("text", [])]


# --- checking ---------------------------------------------------------------------

def parse(spec: str) -> tuple[list[Check], list[str]]:
    """(checks, errors) of a Check cell."""
    spec = spec.strip().strip("`").strip()
    checks: list[Check] = []
    pos = 0
    while pos < len(spec):
        m = ITEM.match(spec, pos)
        if not m or m.end() == pos:
            return checks, [f"cannot read the Check at '{spec[pos:]}' — write COL or COL=VALUE, separated by , or ;"]
        value = m.group(2)
        if value is not None:
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                value = value[1:-1].replace("''", "'") if value[0] == "'" else value[1:-1]
        checks.append(Check(m.group(1), value))
        pos = m.end()
    return checks, []


def same(expected: str, actual: str) -> bool:
    e, a = expected.strip(), actual.strip()
    if e.lower() in NULLS or a.lower() in NULLS:
        return e.lower() in NULLS and a.lower() in NULLS
    if e == a:
        return True
    if NUMBER.match(e) and NUMBER.match(a):
        return Decimal(e) == Decimal(a)
    return False


def _canon(v: str) -> str:
    v = v.strip()
    if NUMBER.match(v):
        return format(Decimal(v).normalize(), "f")          # 200, 10.50, 2E+2 → 200, 10.5, 200
    return "" if v.lower() in NULLS else v


def compare(files: list[Captured], checks: list[Check]) -> Result:
    """Mark every checked cell of the actual grids, and list each value that differs."""
    out = Result()
    expected = next((b for f in files if f.role == "expected" for b in f.blocks if b.kind == "grid" and b.rows), None)
    actual = [(f.label, b) for f in files if f.role == "actual" for b in f.blocks if b.kind == "grid" and b.rows]
    named = {c.column.upper(): c for c in checks}
    out.checked = bool(checks or expected)
    exp_head = [h.strip().upper() for h in expected.rows[0]] if expected else []
    exp_rows = expected.rows[1:] if expected else []
    found: set[str] = set()
    for label, g in actual:
        head = [h.strip().upper() for h in g.rows[0]]
        idx = {h: i for i, h in reversed(list(enumerate(head)))}
        how: dict[str, tuple[str, int | str | None]] = {}
        for name, c in named.items():
            if name not in idx:
                continue
            found.add(name)
            if c.value is not None:
                how[name] = ("value", c.value)
            elif name in exp_head:
                how[name] = ("expected", exp_head.index(name))
            else:
                how[name] = ("eye", None)
        if expected and not named:
            how = {h: ("expected", exp_head.index(h)) for h in exp_head if h in idx}
        if not how:
            continue
        keys = [k for k in exp_head if k not in named and k in idx] if named else []
        match: dict[int, list[str] | None] = {}
        if any(kind == "expected" for kind, _ in how.values()):
            if keys:
                key_of = lambda r, cols, ix: tuple(_canon(r[ix[k]] if ix[k] < len(r) else "") for k in cols)  # noqa: E731
                exp_ix = {h: i for i, h in enumerate(exp_head)}
                by_key = {key_of(r, keys, exp_ix): r for r in reversed(exp_rows)}
                seen = set()
                for ri, r in enumerate(g.rows[1:], 1):
                    k = key_of(r, keys, idx)
                    match[ri] = by_key.get(k)
                    seen.add(k)
                for k, r in by_key.items():
                    if k not in seen:
                        shown = ", ".join(f"{c}={r[exp_ix[c]] if exp_ix[c] < len(r) else ''}" for c in keys)
                        out.differ.append((label, shown, "—", "this row", "not found"))
            else:
                for ri in range(1, len(g.rows)):
                    match[ri] = exp_rows[ri - 1] if ri - 1 < len(exp_rows) else None
                for ri in range(len(g.rows), len(exp_rows) + 1):
                    out.differ.append((label, f"row {ri}", "—", "this row", "not found"))
        g.checked = {idx[n] for n in how}
        g.keys = {idx[k] for k in keys}
        for ri, r in enumerate(g.rows[1:], 1):
            where = ", ".join(f"{k}={r[idx[k]] if idx[k] < len(r) else ''}" for k in keys) or f"row {ri}"
            extra = False
            for name, (kind, ref) in how.items():
                ci = idx[name]
                val = r[ci] if ci < len(r) else ""
                if kind == "eye":
                    g.marks[(ri, ci)] = "eye"
                    out.eye += 1
                    continue
                if kind == "value":
                    want = str(ref)
                else:
                    er = match.get(ri)
                    if er is None:
                        g.marks[(ri, ci)] = "differ"
                        extra = True
                        continue
                    want = er[int(ref)] if int(ref) < len(er) else ""
                if same(want, val):
                    g.marks[(ri, ci)] = "match"
                    out.matched += 1
                else:
                    g.marks[(ri, ci)] = "differ"
                    out.differ.append((label, where, name, want or "(empty)", val or "(empty)"))
            if extra:
                out.differ.append((label, where, "—", "no such row", "this row"))
    if expected:                                # show which columns of the expected table count
        keys = [k for k in exp_head if k not in named] if named else []
        expected.checked = {i for i, h in enumerate(exp_head) if (h in named if named else True)}
        expected.keys = {exp_head.index(k) for k in keys}
    out.unknown = [c.column for c in checks if c.column.upper() not in found]
    return out
