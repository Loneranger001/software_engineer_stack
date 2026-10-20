---
name: retro
description: Close the self-improvement loop after a delivered task - capture structured lessons into the framework's knowledge base and propose concrete template/checklist/skill improvements for user approval. Use after /deliver, or anytime a notable lesson surfaces.
argument-hint: "[task-id]"
---

# /retro — the framework learns from the task

> Framework files: `<root>` is what `ses root` prints — run it once. Every
> framework script runs as `ses <command>` (`ses help` lists them). If `ses`
> is not on PATH, use `python3 <skill-dir>/../../bin/ses` in its place —
> `<skill-dir>` is the folder this SKILL.md was loaded from — here and for
> every `ses` below. If neither runs, stop and ask the user (README →
> Install); never guess another path.

Every delivered task teaches something. This skill turns that into durable
memory (your lessons file, `ses lessons --path`) and, when warranted, into
edits to the framework itself.

## 1. Gather the raw material

1. Locate the workspace and read the task's history where it is recorded:
   `ses status show <ws>` (gates with their dates and notes), each task
   branch's commits (`git -C <repo> log --format='%h %ad %s' --date=short
   <mainline>..<branch>`), the History tables and amendment notes of the
   stage documents, PARKED.md, ASSUMPTIONS.md (corrected entries =
   over-confidence, see decision-protocol §5), grill-log.md rows with an
   "Upstream miss" (a scenario an earlier stage should have caught), the
   evidence/ summaries
   (failed-then-fixed verifications are lessons; open `raw/` logs only for a
   specific failure), and the conversation context if available.
2. Ask the user 2–3 pointed questions (batch them): What cost the most time?
   What did the framework get wrong or make awkward? What almost shipped
   wrong?

## 2. Distill lessons

A lesson must be **actionable next time**, not a diary entry. Test: would a
future skill run, having read this line, do something differently?

Good: "pkg_batch callers include cron entries under ops-repo/schedules —
grep there too (missed in PROJ-123 impact analysis)".
Bad: "impact analysis was hard".

Append each lesson with `ses lessons --add '<line>'` — it checks the format
and writes to your lessons file (`${SES_HOME:-~/.ses}/lessons.md`), which
lives outside every install, survives plugin updates, and is read by every
harness on this machine. Never append to `<root>/knowledge/lessons.md`: in an
installed copy it is replaced on the next update. Format:

```markdown
- [YYYY-MM-DD] [stage:<stage>] [lang:<plsql|sql|ksh|python|->] [repo:<name|->] <lesson> (task <id>)
```

Rules:
- Append-only; never rewrite or delete existing lessons (pruning happens
  in §4 curation with the user).
- Tag precisely — the tags are how other skills filter for relevance;
  `ses lessons --add` rejects a line whose tags the filter cannot match.
- A lesson every user of the framework should get is promoted into the
  framework checkout's `knowledge/lessons.md` (same line), committed there
  with `python3 scripts/check_knowledge.py` passing — proposed to the user
  like a §3 edit.
- Repo-specific lessons that are really coding RULES belong in that repo's
  own rules files (AGENTS.md, CODING_STANDARDS.md, … — `ses repo-rules`
  lists them). Those files are the team's: propose the exact addition to the
  user for them to commit; never edit them as part of the retro.
- Term resolutions that only made it into the grill log or conversation get
  promoted to `<work-repo>/.domain-glossary.md` now (marked `user-confirmed`
  with this task id) — glossary memory is the cheapest self-improvement there is.

## 3. Propose framework improvements (user-gated)

Where a lesson generalizes, propose the concrete edit — the actual diff, not
"we should improve X":

- A checklist gained/changed line (most common and cheapest fix)
- A template section added/reworded
- A skill instruction clarified
- A standards/ rule adjusted

Present proposals with the lesson that motivated each. Apply ONLY what the
user approves — and apply it where it lasts:

1. **Edit the user's framework checkout, never an installed copy.** `<root>`
   is that checkout only when it is a git working tree outside every plugin
   cache (`~/.claude/plugins/`, `~/.copilot/`, `~/.codex/`); a marketplace
   install is replaced on update and the edit would vanish. Otherwise ask
   the user for the software-engineer-stack checkout and edit `skills/`,
   `com.github.copilot/agents/`, `templates/`, `checklists/`, `core/`,
   `standards/`, or `scripts/` there. No checkout available → write the approved diff to
   `<ws>/deliverables/framework-edits.patch` and record the entry as pending
   (step 3), not applied.
2. **Commit and check** in the framework checkout: commit the edit, then run
   `python3 scripts/check_knowledge.py` and the tests
   (`python3 -m unittest discover -s tests`) — both must pass. A plugin
   installed from GitHub picks the edit up once it is pushed and the plugin
   is updated (README → Updating); one installed from the local checkout
   reads it directly.
3. **Record** under "Applied changes" in the framework repo's
   `knowledge/decisions.md`, naming every edited file by its repo-root path
   in backticks:
   `- [YYYY-MM-DD] <change> in `skills/<x>/SKILL.md` — motivated by <lesson> (task <id>)`
   check_knowledge.py fails an entry whose named files have no commit on or
   after its date: an "applied" entry the framework doesn't contain is worse
   than none, because it tells the next retro the problem is solved. A
   change that is approved but not yet in the framework repo is recorded as
   `- [YYYY-MM-DD] [pending-upstream] <change> — <where the patch is>`.

## 4. Curation (when the lessons grow)

When your lessons file (or the framework's `knowledge/lessons.md`) exceeds
~100 entries or contains contradictions, propose a curation pass to the user:
merge duplicates, promote perennial lessons into checklists/templates (then
retire the entry), archive stale ones to a `lessons-archive.md` beside the
file. Curation always shows the user the diff.

## 5. Close

`ses status set <ws> retro=done` (`<ws>` = `<workspace-root>/work/<id>`). Summarize for the user: lessons recorded,
framework edits applied/declined.
