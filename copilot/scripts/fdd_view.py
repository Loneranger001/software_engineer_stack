#!/usr/bin/env python3
"""fdd_view.py — render a functional design for its audience before conversion.

fdd.md is the working document: it carries template guidance, the handoff
summary, and the developer-facing parts the fact-checker needs (component
input tables, Appendix A source references). Stakeholders get a view of it,
written next to it and converted with md2docx.sh / md2pdf.sh /
md2confluence.sh, so the working document itself never loses those parts.

Usage:
    fdd_view.py <fdd.md> [--audience business|technical] [-o <out.md>]

Both audiences drop HTML comments (template guidance) and the handoff summary.
`business` (the default) also drops every region between
`<!-- technical:start -->` and `<!-- technical:end -->` and any
`## Appendix …` section. `technical` keeps them.
Default output: fdd.<audience>.md beside the input.
Exit codes: 0 ok, 1 unbalanced technical markers, 2 usage error.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

AUDIENCES = ("business", "technical")
TECH = re.compile(r"[ \t]*<!-- technical:start -->.*?<!-- technical:end -->[ \t]*\n?", re.S)
HANDOFF = re.compile(r"<!-- handoff:start -->.*?<!-- handoff:end -->\n?", re.S)
COMMENT = re.compile(r"[ \t]*<!--.*?-->[ \t]*\n?", re.S)
APPENDIX = re.compile(r"^## Appendix\b.*?(?=^## |\Z)", re.S | re.M)


def render(text: str, audience: str) -> str:
    if text.count("<!-- technical:start -->") != text.count("<!-- technical:end -->"):
        raise ValueError("unbalanced <!-- technical:start/end --> markers")
    text = HANDOFF.sub("", text)
    if audience == "business":
        text = TECH.sub("", text)
        text = APPENDIX.sub("", text)
    text = COMMENT.sub("", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def main(argv: list[str]) -> int:
    args = list(argv)
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if args else 2
    audience, out = "business", None
    src = None
    while args:
        a = args.pop(0)
        if a in ("--audience", "-o") and not args:
            print(f"error: {a} needs a value", file=sys.stderr)
            return 2
        if a == "--audience":
            audience = args.pop(0)
        elif a.startswith("--audience="):
            audience = a.split("=", 1)[1]
        elif a == "-o":
            out = Path(args.pop(0))
        elif src is None:
            src = Path(a)
        else:
            print(f"error: unexpected argument {a}", file=sys.stderr)
            return 2
    if audience not in AUDIENCES:
        print(f"error: audience must be one of {', '.join(AUDIENCES)}; got '{audience}'", file=sys.stderr)
        return 2
    if src is None or not src.is_file():
        print(f"error: no such file: {src}", file=sys.stderr)
        return 2
    try:
        view = render(src.read_text(encoding="utf-8"), audience)
    except ValueError as e:
        print(f"error: {src}: {e}", file=sys.stderr)
        return 1
    out = out or src.with_name(f"{src.stem}.{audience}.md")
    out.write_text(view, encoding="utf-8")
    print(f"wrote {out} ({audience} view)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
