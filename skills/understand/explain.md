# /understand — §4–6: explain, Q&A, close

> Loaded by `skills/understand/SKILL.md` once the interface map is done
> (`map=done`). Same rules as the skill: every statement from the code, with
> its source; `INFERRED` labelled; the code wins over names and comments.
> `<ws>` = `<workspace-root>/work/<id>`; stage state is recorded with
> `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/status.py`.

## 4. Explain in layers

Present the interface in conversation, top-down, so the user can stop at the
depth they need:

1. **One paragraph** — what it exists to do, in business terms.
2. **At a glance** — trigger/schedule, inputs, outputs, key configuration.
3. **Flow walkthrough** — the mermaid flow plus a narrative of the main path.
4. **Dependency picture** — what feeds it, what would break without it.
5. **Failure & recovery** — how it fails, how you know, how it restarts.

Tie statements visibly to sources (`file:line` inline) — the references are
what lets the user trust the explanation and jump into the code themselves.
Label `INFERRED` items and open questions honestly: an admitted gap keeps
trust; a confident guess destroys it the first time the user checks.

If the user opened with a specific question, answer that first — with its
evidence — then offer the layers around it.

`status.py set <ws> explain=done`.

## 5. Q&A until the model holds

Understanding is interactive; expect follow-ups and treat them as the point
of the exercise, not an interruption.

- Answer every follow-up from the code (or a fresh run), not from memory of
  your own summary; add each new fact to the fact table and, when it changes
  the picture, to the map's diagrams/tables.
- "What if" questions ("what happens if the feed is late", "what breaks if
  we rename this column") are answered by tracing the actual handling path;
  say clearly where the trace ends and reasoning beyond the evidence begins.
- Business meanings confirmed along the way go into
  `<work-repo>/.domain-glossary.md` (marked `from-code`, template:
  `${CLAUDE_PLUGIN_ROOT}/templates/domain-glossary.md`) so the next task
  doesn't re-derive them.
- Findings that suggest work — bugs, dead code, risky patterns — go to
  PARKED.md and are mentioned to the user; never act on them here.

## 6. Close and hand off

1. Make sure interface-map.md reflects everything learned, including Q&A
   discoveries, and log remaining open questions in it.
2. Offer the natural next steps where they fit — a formal
   `/document understanding-doc` (its analyze stage reuses this map), a
   `/change-request`, or a full `/intake` — but don't push: understanding
   alone is a complete outcome.
