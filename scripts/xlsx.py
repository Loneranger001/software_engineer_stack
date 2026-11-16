"""xlsx.py — a minimal, deterministic XLSX writer (imported by ut_workbook.py; not a command).

The framework runs on the Python standard library alone, so this writes the
few SpreadsheetML parts a workbook needs by hand: text cells (inline strings —
nothing is ever a formula, so no cell value can execute), a fixed style
table, column widths, a frozen header, an autofilter, and hyperlinks between
sheets (`<hyperlink location="'TC1'!A1">`, which Excel, LibreOffice and
Google Sheets all follow). Every zip entry carries the same timestamp, so the
same content always produces the same bytes: a workbook rebuilt from
unchanged evidence has the same SHA-256.

Limits enforced here, from Excel: a sheet name is 1-31 characters without
[]:*?/\\ ; a cell holds at most 32,767 characters; XML 1.0 forbids most
control characters, which are dropped (ANSI colour codes first).
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

MAX_CELL = 32767
MAX_ROWS = 1048576
_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
_ILLEGAL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f￾￿]")
_BAD_SHEET = re.compile(r"[\[\]:*?/\\]")
_STAMP = (1980, 1, 1, 0, 0, 0)

# cell styles — indexes into <cellXfs> below
DEFAULT, TITLE, HEADER, TEXT, LINK, KEY, PASS, FAIL, WARN, MONO, GRID_HEAD, GRID, NOTE, LINK_PLAIN, SECTION = range(15)

_FONTS = [
    '<font><sz val="11"/><name val="Calibri"/><family val="2"/></font>',
    '<font><b/><sz val="14"/><name val="Calibri"/><family val="2"/></font>',
    '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/><family val="2"/></font>',
    '<font><u/><sz val="11"/><color rgb="FF0563C1"/><name val="Calibri"/><family val="2"/></font>',
    '<font><b/><sz val="11"/><name val="Calibri"/><family val="2"/></font>',
    '<font><sz val="10"/><name val="Consolas"/><family val="3"/></font>',
    '<font><i/><sz val="10"/><color rgb="FF595959"/><name val="Calibri"/><family val="2"/></font>',
    '<font><b/><sz val="11"/><color rgb="FF006100"/><name val="Calibri"/><family val="2"/></font>',
    '<font><b/><sz val="11"/><color rgb="FF9C0006"/><name val="Calibri"/><family val="2"/></font>',
    '<font><b/><sz val="11"/><color rgb="FF9C5700"/><name val="Calibri"/><family val="2"/></font>',
]
_FILLS = [
    '<fill><patternFill patternType="none"/></fill>',
    '<fill><patternFill patternType="gray125"/></fill>',
    *(f'<fill><patternFill patternType="solid"><fgColor rgb="FF{c}"/><bgColor indexed="64"/></patternFill></fill>'
      for c in ("1F4E78", "C6EFCE", "FFC7CE", "FFEB9C", "F2F2F2")),
]
_BORDERS = [
    '<border><left/><right/><top/><bottom/><diagonal/></border>',
    '<border>' + "".join(f'<{s} style="thin"><color rgb="FFBFBFBF"/></{s}>' for s in ("left", "right", "top", "bottom"))
    + '<diagonal/></border>',
]
# (font, fill, border, wrap) per style index
_XF = [
    (0, 0, 0, False),   # DEFAULT
    (1, 0, 0, False),   # TITLE
    (2, 2, 1, True),    # HEADER
    (0, 0, 1, True),    # TEXT
    (3, 0, 1, False),   # LINK
    (4, 6, 1, True),    # KEY
    (7, 3, 1, False),   # PASS
    (8, 4, 1, False),   # FAIL
    (9, 5, 1, False),   # WARN
    (5, 0, 0, False),   # MONO
    (4, 6, 1, False),   # GRID_HEAD
    (0, 0, 1, False),   # GRID
    (6, 0, 0, False),   # NOTE
    (3, 0, 0, False),   # LINK_PLAIN
    (4, 0, 0, False),   # SECTION
]

_NS = ('xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
       'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')
_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'


def clean(value: object) -> str:
    """Text safe for an XLSX cell: ANSI codes and XML-illegal characters dropped, capped at 32,767."""
    s = _ILLEGAL.sub("", _ANSI.sub("", str(value)))
    if len(s) > MAX_CELL:
        s = s[:MAX_CELL - 20] + " … [truncated]"
    return s


def col_letter(n: int) -> str:
    """1 → A, 27 → AA."""
    out = ""
    while n:
        n, r = divmod(n - 1, 26)
        out = chr(65 + r) + out
    return out


def ref(row: int, col: int) -> str:
    return f"{col_letter(col)}{row}"


def absolute(cells: str) -> str:
    """A7:M12 → $A$7:$M$12."""
    return re.sub(r"([A-Z]+)(\d+)", r"$\1$\2", cells)


def sheet_ref(name: str, cell: str = "A1") -> str:
    return "'" + name.replace("'", "''") + "'!" + cell


class Sheet:
    def __init__(self, name: str):
        if not name or len(name) > 31 or _BAD_SHEET.search(name) or name.startswith("'") or name.endswith("'"):
            raise ValueError(f"invalid sheet name: {name!r}")
        self.name = name
        self.cells: dict[int, dict[int, tuple[str, int]]] = {}
        self.widths: dict[int, float] = {}
        self.links: list[tuple[str, str, str]] = []
        self.freeze_rows = 0
        self.autofilter: str | None = None

    def set(self, row: int, col: int, value: object, style: int = DEFAULT) -> None:
        if not 1 <= row <= MAX_ROWS or not 1 <= col <= 16384:
            raise ValueError(f"cell out of range: row {row}, column {col}")
        self.cells.setdefault(row, {})[col] = (clean(value), style)

    def row(self, row: int, values: list[object], style: int = DEFAULT, start: int = 1) -> None:
        for i, v in enumerate(values):
            self.set(row, start + i, v, style)

    def link(self, row: int, col: int, text: str, sheet: str, cell: str = "A1", style: int = LINK) -> None:
        """A cell that opens another sheet of this workbook."""
        self.set(row, col, text, style)
        self.links.append((ref(row, col), sheet_ref(sheet, cell), clean(text)))

    def width(self, col: int, chars: float) -> None:
        self.widths[col] = chars

    @property
    def max_row(self) -> int:
        return max(self.cells, default=0)

    def xml(self, selected: bool) -> str:
        rows = sorted(self.cells)
        max_col = max((c for r in self.cells.values() for c in r), default=1)
        dim = f"A1:{ref(rows[-1], max_col)}" if rows else "A1"
        view = '<sheetView workbookViewId="0"' + (' tabSelected="1"' if selected else "")
        if self.freeze_rows:
            top = f"A{self.freeze_rows + 1}"
            view += (f'><pane ySplit="{self.freeze_rows}" topLeftCell="{top}" activePane="bottomLeft" state="frozen"/>'
                     f'<selection pane="bottomLeft" activeCell="{top}" sqref="{top}"/></sheetView>')
        else:
            view += "/>"
        # printed or saved as PDF: landscape, every column on one page width
        parts = [_HEAD, f"<worksheet {_NS}>", '<sheetPr><pageSetUpPr fitToPage="1"/></sheetPr>',
                 f'<dimension ref="{dim}"/>', f"<sheetViews>{view}</sheetViews>",
                 '<sheetFormatPr defaultRowHeight="15"/>']
        if self.widths:
            parts.append("<cols>" + "".join(f'<col min="{c}" max="{c}" width="{w}" customWidth="1"/>'
                                            for c, w in sorted(self.widths.items())) + "</cols>")
        parts.append("<sheetData>")
        for r in rows:
            parts.append(f'<row r="{r}">')
            for c in sorted(self.cells[r]):
                text, style = self.cells[r][c]
                s = f' s="{style}"' if style else ""
                parts.append(f'<c r="{ref(r, c)}" t="inlineStr"{s}><is><t xml:space="preserve">{escape(text)}</t></is></c>')
            parts.append("</row>")
        parts.append("</sheetData>")
        if self.autofilter:
            parts.append(f'<autoFilter ref="{self.autofilter}"/>')
        if self.links:
            parts.append("<hyperlinks>" + "".join(
                f'<hyperlink ref="{cell}" location={quoteattr(target)} display={quoteattr(text)}/>'
                for cell, target, text in self.links) + "</hyperlinks>")
        parts.append('<pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>')
        parts.append('<pageSetup orientation="landscape" fitToWidth="1" fitToHeight="0"/>')
        parts.append("</worksheet>")
        return "".join(parts)


class Workbook:
    def __init__(self, title: str = ""):
        self.title = title
        self.sheets: list[Sheet] = []

    def add_sheet(self, name: str) -> Sheet:
        if any(s.name.lower() == name.lower() for s in self.sheets):
            raise ValueError(f"duplicate sheet name: {name!r}")
        sheet = Sheet(name)
        self.sheets.append(sheet)
        return sheet

    def _styles(self) -> str:
        xfs = "".join(
            f'<xf numFmtId="0" fontId="{f}" fillId="{fi}" borderId="{b}" xfId="0"'
            + (' applyFont="1"' if f else "") + (' applyFill="1"' if fi else "") + (' applyBorder="1"' if b else "")
            + (' applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>' if wrap
               else ' applyAlignment="1"><alignment vertical="top"/></xf>')
            for f, fi, b, wrap in _XF)
        return (f'{_HEAD}<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                f'<fonts count="{len(_FONTS)}">{"".join(_FONTS)}</fonts>'
                f'<fills count="{len(_FILLS)}">{"".join(_FILLS)}</fills>'
                f'<borders count="{len(_BORDERS)}">{"".join(_BORDERS)}</borders>'
                '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
                f'<cellXfs count="{len(_XF)}">{xfs}</cellXfs>'
                '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
                "</styleSheet>")

    def parts(self) -> list[tuple[str, str]]:
        if not self.sheets:
            raise ValueError("a workbook needs at least one sheet")
        n = len(self.sheets)
        types = "".join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/'
                        f'vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1, n + 1))
        defined = "".join(
            f'<definedName name="_xlnm._FilterDatabase" localSheetId="{i}" hidden="1">'
            f"{escape(sheet_ref(s.name, absolute(s.autofilter)))}</definedName>"
            for i, s in enumerate(self.sheets) if s.autofilter)
        out = [
            ("[Content_Types].xml",
             f'{_HEAD}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="xml" ContentType="application/xml"/>'
             '<Override PartName="/xl/workbook.xml" ContentType="application/'
             'vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
             '<Override PartName="/xl/styles.xml" ContentType="application/'
             'vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
             '<Override PartName="/docProps/core.xml" ContentType="application/'
             'vnd.openxmlformats-package.core-properties+xml"/>'
             f"{types}</Types>"),
            ("_rels/.rels",
             f'{_HEAD}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
             'officeDocument" Target="xl/workbook.xml"/>'
             '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/'
             'metadata/core-properties" Target="docProps/core.xml"/></Relationships>'),
            ("docProps/core.xml",
             f'{_HEAD}<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/'
             'core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/">'
             f"<dc:title>{escape(clean(self.title))}</dc:title><dc:creator>ses ut-workbook</dc:creator>"
             "</cp:coreProperties>"),
            ("xl/workbook.xml",
             f'{_HEAD}<workbook {_NS}><bookViews><workbookView activeTab="0"/></bookViews><sheets>'
             + "".join(f'<sheet name={quoteattr(s.name)} sheetId="{i}" r:id="rId{i}"/>'
                       for i, s in enumerate(self.sheets, 1))
             + "</sheets>" + (f"<definedNames>{defined}</definedNames>" if defined else "") + "</workbook>"),
            ("xl/_rels/workbook.xml.rels",
             f'{_HEAD}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             + "".join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                       f'relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1, n + 1))
             + f'<Relationship Id="rId{n + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
               'relationships/styles" Target="styles.xml"/></Relationships>'),
            ("xl/styles.xml", self._styles()),
        ]
        out += [(f"xl/worksheets/sheet{i}.xml", s.xml(i == 1)) for i, s in enumerate(self.sheets, 1)]
        return out

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".part")
        with zipfile.ZipFile(tmp, "w") as z:
            for name, data in self.parts():
                info = zipfile.ZipInfo(name, date_time=_STAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                z.writestr(info, data.encode("utf-8"))
        tmp.replace(path)
