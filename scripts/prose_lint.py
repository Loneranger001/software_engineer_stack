#!/usr/bin/env python3
"""prose_lint.py — hold a document people read to the writing standard.

standards/writing.md sets the rules for the documents people read (the
review versions of the FDD and TDD, how-to, KB article, understanding doc,
release notes):
a subset of the ASD-STE100 writing rules, plus one of its own — write about
the system, never about how the document was made. This script flags the
mechanical part. It is a floor, not the judgment: a coined noun stack with no
slash in it passes the lint and still fails the standard.

Usage:
    prose_lint.py [--allow KIND[,KIND...]] <doc.md> [<doc.md> ...]

Findings, one per line as `<file>:<line>: [KIND] <match> — <fix>`:
    PROCESS    words about how the document was made: research, this task,
               scope contract, workspace, fact-check, stage names (/intake …),
               "we found", "analysis shows", workspace files
    SLASH      two words joined by a slash ("message / publication"); paths,
               `code` and all-capital acronyms (I/O, PL/SQL) are exempt
    LONG       a sentence over 25 words, or over 20 in a numbered step
    PARAGRAPH  a paragraph over six sentences
    WORDS      a word with a plain replacement (utilize, in order to, prior to …)

Not checked: HTML comments (template guidance), fenced blocks, `inline code`,
block quotes (a source quoted word for word), the header lines above the
first `##` heading, the handoff summary, headings, table header rows, and the
`## Appendix…`, `## Sources` and `## Verification of this article` sections —
they hold source references.

--allow skips the named kinds — only for text a format the repo's rules or
the user prescribe requires word for word.

Exit codes: 0 clean, 1 findings, 2 usage error.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

I = re.I
STEP_MAX, SENTENCE_MAX, PARAGRAPH_MAX = 20, 25, 6
FIX = {
    "PROCESS": "state the fact about the system; the reader never sees how the document was made",
    "SLASH": "write \"or\" or \"and\", or select one word",
    "LONG": "split it — one idea per sentence",
    "PARAGRAPH": f"split it by topic — {PARAGRAPH_MAX} sentences at most",
    "WORDS": "",  # the replacement comes from PLAIN
}
KINDS = tuple(FIX)

PROCESS = [re.compile(p, I) for p in (
    r"\bresearch(ed|ing)?\b",
    r"\bscope[- ]contract\b",
    r"\b(this|our|the current) task\b",
    r"\btask[- ](owned|specific|scoped|level|local)\b",
    r"\bworkspace\b",
    r"\bfact[- ]?check(s|ed|er|ing)?\b",
    r"(?<![\w/.])/(intake|func-design|tech-design|grill|impl-plan|implement|deliver|retro|"
    r"change-request|document|understand|verify-code)\b",
    r"\b(ASSUMPTIONS|PARKED|STATUS)\.md\b",
    r"\bwe\s+(found|identified|verified|confirmed|checked|traced|observed|noticed|searched|reviewed)\b",
    r"\b(analysis|investigation|the code|code review|the search|our review)\s+(has\s+|have\s+)?"
    r"(identified|found|showed|shown|shows|confirmed|revealed|indicated|indicates|suggests|suggested)\b",
)]
PLAIN: list[tuple[re.Pattern[str], str]] = [(re.compile(p, I), fix) for p, fix in (
    (r"\butili[sz](e|es|ed|ing|ation)\b", "use"),
    (r"\bleverag(e|es|ed|ing)\b", "use"),
    (r"\bfacilitat(e|es|ed|ing)\b", "help, let"),
    (r"\bin\s+order\s+to\b", "to"),
    (r"\bprior\s+to\b", "before"),
    (r"\bsubsequent(ly)?(\s+to)?\b", "after, next, then"),
    (r"\bwith\s+(respect|regard)\s+to\b", "about, for"),
    (r"\bin\s+terms\s+of\b", "rewrite with a verb"),
    (r"\ba\s+number\s+of\b", "some, or give the number"),
    (r"\bgoing\s+forward\b", "from now on, or delete it"),
    (r"\bseamless(ly)?\b", "delete it, or say what does not break"),
    (r"\brobust(ly|ness)?\b", "say what it withstands"),
    (r"\betc\.", "list every item, or write \"for example\" before a partial list"),
)]
SLASH = re.compile(r"(?<![\w/.:\\-])([A-Za-z][A-Za-z'-]*)\s*/\s*([A-Za-z][A-Za-z'-]*)(?![\w/:\\-]|\.\w)")
SLASH_OK = {"n/a"}

FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^\s{0,3}(#{1,6})\s")
SKIP_SECTION = re.compile(r"^##\s+(Appendix\b|Sources?\s*$|Verification of this article\b)", I)
ITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
# a sentence ends at . ! ? (optionally closed by a quote or bracket) before a capital, digit or quote
BOUNDARY = re.compile(r"(?<=[.!?])[\"'’”)\]]*\s+(?=[A-Z0-9\"'“(\[])")


def blank(match: re.Match[str]) -> str:
    """Replace a region with its newlines only, so line numbers stay true."""
    return "\n" * match.group(0).count("\n")


def clean(text: str) -> str:
    """Prose as a reader sees it: inline code and links reduced to one word each."""
    text = re.sub(r"`[^`\n]*`", "CODE", text)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"https?://\S+", "URL", text)
    return re.sub(r"[*_]{1,3}(?=\S)|(?<=\S)[*_]{1,3}", "", text)


def blocks(text: str):
    """Yield (kind, [(line, text), ...]) for every checked chunk of prose.

    kind is "paragraph", "step" (a numbered list item), "item" (a bulleted
    list item) or "cell" (one table body cell).
    """
    text = re.sub(r"<!-- handoff:start -->.*?<!-- handoff:end -->", blank, text, flags=re.S)
    text = re.sub(r"<!--.*?-->", blank, text, flags=re.S)
    lines = text.splitlines()
    has_h2 = any(HEADING.match(l) and len(HEADING.match(l).group(1)) >= 2 for l in lines)
    started, skipping, fence = not has_h2, False, False
    cur: tuple[str, list[tuple[int, str]]] | None = None

    def flush():
        nonlocal cur
        if cur and any(t.strip() for _, t in cur[1]):
            yield cur
        cur = None

    for n, line in enumerate(lines, 1):
        if fence:
            fence = not FENCE.match(line)
            continue
        if FENCE.match(line):
            yield from flush()
            fence = True
            continue
        h = HEADING.match(line)
        if h:
            yield from flush()
            if len(h.group(1)) == 2:
                started, skipping = True, bool(SKIP_SECTION.match(line.strip()))
            elif len(h.group(1)) >= 2:
                started = True
            continue
        if not started or skipping:
            continue
        if not line.strip() or line.lstrip().startswith(">"):
            yield from flush()
            continue
        if line.lstrip().startswith("|"):
            yield from flush()
            nxt = lines[n] if n < len(lines) else ""
            if TABLE_SEP.match(line) or TABLE_SEP.match(nxt):
                continue  # separator or header row
            for cell in re.split(r"(?<!\\)\|", line.strip().strip("|")):
                if cell.strip():
                    yield "cell", [(n, cell)]
            continue
        m = ITEM.match(line)
        if m:
            yield from flush()
            kind = "step" if m.group(2)[0].isdigit() else "item"
            cur = (kind, [(n, line[m.end():])])
            continue
        if cur is None:
            cur = ("paragraph", [])
        cur[1].append((n, line.strip()))
    yield from flush()


def sentences(joined: str):
    """Yield (offset, sentence) spans of a chunk joined with single spaces."""
    start = 0
    for b in BOUNDARY.finditer(joined):
        yield start, joined[start:b.start()]
        start = b.end()
    yield start, joined[start:]


def words(s: str) -> int:
    return sum(1 for tok in s.split() if re.search(r"[A-Za-z0-9]", tok))


def lint(text: str, allow: frozenset[str] = frozenset()) -> list[tuple[int, str, str, str]]:
    """Return (line, kind, matched text, fix) for every writing-standard finding."""
    found: list[tuple[int, str, str, str]] = []
    seen: set[tuple[int, str]] = set()

    def add(n: int, kind: str, match: str, fix: str = "") -> None:
        if kind not in allow and (n, kind) not in seen:
            seen.add((n, kind))
            found.append((n, kind, match.strip(), fix or FIX[kind]))

    for kind, chunk in blocks(text):
        starts, pos = [], 0
        for n, t in chunk:
            starts.append((pos, n))
            pos += len(clean(t)) + 1
        joined = " ".join(clean(t) for _, t in chunk)

        def line_at(offset: int) -> int:
            return [n for p, n in starts if p <= offset][-1]

        for rx in PROCESS:
            for m in rx.finditer(joined):
                add(line_at(m.start()), "PROCESS", m.group(0))
        for m in SLASH.finditer(joined):
            a, b = m.group(1), m.group(2)
            if not (a.isupper() and b.isupper()) and f"{a}/{b}".lower() not in SLASH_OK:
                add(line_at(m.start()), "SLASH", m.group(0))
        for rx, fix in PLAIN:
            for m in rx.finditer(joined):
                add(line_at(m.start()), "WORDS", m.group(0), fix)
        limit = STEP_MAX if kind == "step" else SENTENCE_MAX
        spans = [(o, s) for o, s in sentences(joined) if words(s)]
        for o, s in spans:
            count = words(s)
            if count > limit:
                lead = " ".join(s.split()[:8])
                add(line_at(o), "LONG", f"{count} words: {lead} …",
                    f"split it — {limit} words at most{' in a step' if kind == 'step' else ''}, one idea per sentence")
        if kind == "paragraph" and len(spans) > PARAGRAPH_MAX:
            add(chunk[0][0], "PARAGRAPH", f"{len(spans)} sentences")
    return sorted(found)


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
        print("usage: prose_lint.py [--allow KIND[,KIND]] <doc.md> [...]", file=sys.stderr)
        return 2
    total = 0
    for a in args:
        p = Path(a)
        if not p.is_file():
            print(f"error: no such file: {p}", file=sys.stderr)
            return 2
        for n, kind, match, fix in lint(p.read_text(encoding="utf-8"), frozenset(allow)):
            print(f"{p}:{n}: [{kind}] {match[:80]} — {fix}")
            total += 1
    if total:
        print(f"{total} writing finding(s) — rewrite each sentence per standards/writing.md "
              f"(not reworded to dodge the pattern)", file=sys.stderr)
        return 1
    print(f"prose lint ok ({len(args)} file(s){', allowed: ' + ','.join(sorted(allow)) if allow else ''})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
