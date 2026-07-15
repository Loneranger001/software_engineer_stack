---
name: retro
description: Close the self-improvement loop after a delivered task - capture structured lessons into the framework's knowledge base and propose concrete template/checklist/skill improvements for user approval. Use after /deliver, or anytime a notable lesson surfaces.
argument-hint: "[task-id]"
---

# /retro — the framework learns from the task

> Path note: `${CLAUDE_PLUGIN_ROOT}` is this framework's root — the ancestor
> directory of this file containing `plugin.json`/`skills/`. Claude Code resolves
> it automatically; other harnesses resolve it from this file's location.

Every delivered task teaches something. This skill turns that into durable
memory (`knowledge/lessons.md`) and, when warranted, into edits to the
framework itself.

## 1. Gather the raw material

1. Locate the workspace; read STATUS.md's log end-to-end (it records every
   stage transition and stumble), PARKED.md, ASSUMPTIONS.md (corrected
   entries = over-confidence, see decision-protocol §5), evidence/
   (failed-then-fixed verifications are lessons), and the conversation
   context if available.
2. Ask the user 2–3 pointed questions (batch them): What cost the most time?
   What did the framework get wrong or make awkward? What almost shipped
   wrong?

## 2. Distill lessons

A lesson must be **actionable next time**, not a diary entry. Test: would a
future skill run, having read this line, do something differently?

Good: "pkg_batch callers include cron entries under ops-repo/schedules —
grep there too (missed in PROJ-123 impact analysis)".
Bad: "impact analysis was hard".

Append to `${CLAUDE_PLUGIN_ROOT}/knowledge/lessons.md` in its format:

```markdown
- [YYYY-MM-DD] [stage:<stage>] [lang:<plsql|sql|ksh|python|->] [repo:<name|->] <lesson> (task <id>)
```

Rules:
- Append-only; never rewrite or delete existing lessons here (pruning happens
  in §4 curation with the user).
- Tag precisely — the tags are how other skills filter for relevance.
- Repo-specific lessons that are really CONVENTIONS belong in that repo's
  `.conventions.md` instead; put them there and note the move.
- Term resolutions that only made it into the grill log or conversation get
  promoted to the repo's `.domain-glossary.md` now (marked `user-confirmed`
  with this task id) — glossary memory is the cheapest self-improvement there is.

## 3. Propose framework improvements (user-gated)

Where a lesson generalizes, propose the concrete edit — the actual diff, not
"we should improve X":

- A checklist gained/changed line (most common and cheapest fix)
- A template section added/reworded
- A skill instruction clarified
- A standards/ rule adjusted

Present proposals with the lesson that motivated each. Apply ONLY what the
user approves; record applied changes in `knowledge/decisions.md` with the
motivating task id.

## 4. Curation (when lessons.md grows)

When lessons.md exceeds ~100 entries or contains contradictions, propose a
curation pass to the user: merge duplicates, promote perennial lessons into
checklists/templates (then retire the entry), archive stale ones to
`knowledge/lessons-archive.md`. Curation always shows the user the diff.

## 5. Close

Update STATUS.md: `retro: done`. Summarize for the user: lessons recorded,
framework edits applied/declined.
