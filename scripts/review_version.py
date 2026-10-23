#!/usr/bin/env python3
"""review_version.py — keep a design's review version in step with its agent version.

A design has two versions. The agent version (fdd.md, tdd.md) is complete and
traceable — IDs, table.column names, sources, the handoff summary — and every
later stage and reviewer reads it. The review version (fdd.review.md,
tdd.review.md, from templates/fdd-review.md and templates/tdd-review.md) is
what people read and approve: short, plain (standards/writing.md), with no
visible IDs. Approving the review version approves the agent version only if
the two say the same thing, so the review version carries two hidden links:

- every paragraph, step, or table row ends with an anchor naming the
  agent-version IDs it covers:      <!-- covers: FR1, BR1 -->
- its header holds a stamp of the agent version it was written from:
                                    - Written from: fdd.md @ 3f9a1c0b7d2e

Usage:
    review_version.py check  <doc.md|ws>...  doc = fdd.md, tdd.md, or its .review.md;
                                             ws = every design with a review version
    review_version.py stamp  <doc.md>        record the agent version's current stamp
    review_version.py render <doc.md> [-o out.md]
                       the review version without anchors, guidance, or stamp —
                       default <dir>/deliverables/<name>.review.md

`check` fails (exit 1) when the review version:
  - is missing (a design named on the command line);
  - leaves out an ID the agent version defines — the first cell of a table
    row (FR1, BR1, EX1, TS1, Q1, S1, A1, G1, ...): a reader approving it never
    saw that item;
  - anchors an ID the agent version does not define (stale);
  - shows an agent-version ID in its visible text — IDs stay in the anchors;
  - has no stamp, or a stamp that no longer matches: the agent version's body
    changed after the review version was written. Bring the review version up
    to date first, then re-stamp — re-stamping alone hides the drift this
    check exists to catch. The agent version's header (status, approval) and
    handoff summary are not part of the stamp.
It also prints the review version's length: two pages is the aim, four the most.
`ses handoff check` runs the same check on fdd.md and tdd.md whenever a review
version exists beside them.
Exit codes: 0 ok, 1 problems found, 2 usage error.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

from handoff import END, ID_ROW, START

AGENT = ("fdd.md", "tdd.md")
WORDS_PER_PAGE = 450
ANCHOR = re.compile(r"<!--\s*covers:\s*(.*?)-->", re.S)
COMMENT = re.compile(r"<!--.*?-->", re.S)
STAMP = re.compile(r"^- Written from: (\S+) @ ([0-9a-f]{12})\s*$", re.M)


def pair(path: Path) -> tuple[Path, Path]:
    """(agent version, review version) for either file of a design."""
    if path.name.endswith(".review.md"):
        return path.with_name(path.name[: -len(".review.md")] + ".md"), path
    return path, path.with_name(f"{path.stem}.review.md")


def stamp_of(agent_text: str) -> str:
    """Hash of the agent version's body: from its first section, without the handoff summary."""
    text = re.sub(re.escape(START) + r".*?" + re.escape(END), "", agent_text, flags=re.S)
    m = re.search(r"^## ", text, re.M)
    body = text[m.start():] if m else text
    norm = "\n".join(line.rstrip() for line in body.strip().splitlines())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:12]


def agent_ids(agent_text: str) -> list[str]:
    body = re.sub(re.escape(START) + r".*?" + re.escape(END), "", agent_text, flags=re.S)
    body = COMMENT.sub("", body)
    return sorted(set(ID_ROW.findall(body)), key=lambda s: (re.sub(r"\d", "", s), int(re.sub(r"\D", "", s))))


def visible(review_text: str) -> str:
    return COMMENT.sub("", review_text)


def coverage_problems(agent_text: str, review_text: str) -> list[str]:
    """What the review version leaves out, invents, or shows — stamp aside."""
    ids = agent_ids(agent_text)
    anchored = {t for m in ANCHOR.findall(review_text) for t in re.split(r"[,\s]+", m) if t}
    out = []
    missing = [i for i in ids if i not in anchored]
    if missing:
        out.append(f"leaves out {', '.join(missing)} — add each where a reader meets it, with its "
                   "covers: anchor (a reader approving this version never saw these items)")
    unknown = sorted(anchored - set(ids))
    if unknown:
        out.append(f"anchors {', '.join(unknown)}, which the agent version does not define — stale or mistyped")
    shown = [i for i in ids if re.search(rf"\b{re.escape(i)}\b", visible(review_text))]
    if shown:
        out.append(f"shows {', '.join(shown)} in its text — IDs stay in the covers: anchors")
    return out


def problems(path: Path) -> list[str]:
    agent, review = pair(path)
    if not agent.is_file():
        return [f"{review}: no agent version {agent.name} beside it"]
    if not review.is_file():
        return [f"{agent}: no review version — write {review.name} from <root>/templates/"
                f"{agent.stem}-review.md at the approval gate"]
    agent_text, review_text = agent.read_text(encoding="utf-8"), review.read_text(encoding="utf-8")
    out = [f"{review}: {p}" for p in coverage_problems(agent_text, review_text)]
    m = STAMP.search(review_text)
    if not m:
        out.append(f"{review}: no '- Written from: {agent.name} @ <stamp>' line — run "
                   f"`ses review-version stamp {agent}` once it matches {agent.name}")
    elif m.group(2) != stamp_of(agent_text):
        out.append(f"{review}: {agent.name} changed after this review version was written — update "
                   f"it to match, have its agreement re-checked, then re-stamp")
    return out


def length(review: Path) -> str:
    words = len(visible(review.read_text(encoding="utf-8")).split())
    pages = max(1, round(words / WORDS_PER_PAGE))
    note = "" if pages <= 4 else " — over four pages: cut it down"
    return f"{review}: {words} words, about {pages} page(s){note}"


def stamp(path: Path) -> int:
    agent, review = pair(path)
    if not (agent.is_file() and review.is_file()):
        print(f"error: need both {agent} and {review}", file=sys.stderr)
        return 2
    line = f"- Written from: {agent.name} @ {stamp_of(agent.read_text(encoding='utf-8'))}"
    text = review.read_text(encoding="utf-8")
    if STAMP.search(text) or re.search(r"^- Written from:.*$", text, re.M):
        text = re.sub(r"^- Written from:.*$", line, text, count=1, flags=re.M)
    else:
        lines = text.splitlines()
        at = next((i + 1 for i, l in enumerate(lines) if l.startswith("# ")), 0)
        while at < len(lines) and lines[at].startswith("- "):
            at += 1
        lines.insert(at, line)
        text = "\n".join(lines) + "\n"
    review.write_text(text, encoding="utf-8")
    print(f"stamped {review} ({line[2:]})")
    return 0


def render(path: Path, out: Path | None) -> int:
    _, review = pair(path)
    if not review.is_file():
        print(f"error: no such file: {review}", file=sys.stderr)
        return 2
    text = review.read_text(encoding="utf-8")
    if text.count("<!--") != text.count("-->"):
        print(f"error: {review}: unbalanced HTML comment", file=sys.stderr)
        return 1
    text = re.sub(r"^- Written from:.*\n?", "", text, flags=re.M)
    one = r"<!--(?:(?!-->).)*-->"  # a single comment, never running into the next
    text = re.sub(rf"^[ \t]*{one}[ \t]*\n", "", text, flags=re.M | re.S)  # guidance on its own lines
    text = re.sub(rf" ?{one}", "", text, flags=re.S)  # anchors at the end of a line or cell
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    out = out or review.parent / "deliverables" / review.name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] not in ("check", "stamp", "render"):
        print(__doc__)
        return 2
    cmd, args = argv[0], argv[1:]
    if cmd == "stamp":
        return stamp(Path(args[0])) if len(args) == 1 else main([])
    if cmd == "render":
        out = None
        if "-o" in args:
            i = args.index("-o")
            if i + 1 >= len(args):
                return main([])
            out, args = Path(args[i + 1]), args[:i] + args[i + 2:]
        return render(Path(args[0]), out) if len(args) == 1 else main([])
    designs: list[Path] = []
    for a in map(Path, args):
        if a.is_dir():
            designs += [a / d for d in AGENT if (a / d).is_file() and pair(a / d)[1].is_file()]
        elif a.is_file():
            designs.append(a)
        else:
            print(f"error: no such file or directory: {a}", file=sys.stderr)
            return 2
    if not designs:
        print("no design with a review version — nothing to check")
        return 0
    found = [p for d in designs for p in problems(d)]
    for p in found:
        print(f"problem: {p}", file=sys.stderr)
    for d in designs:
        if pair(d)[1].is_file():
            print(length(pair(d)[1]))
    if not found:
        print(f"review versions ok ({len(designs)} design(s))")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
