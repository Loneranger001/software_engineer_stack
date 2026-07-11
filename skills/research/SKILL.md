---
name: research
description: Investigate the codebase and external sources for the current task and produce source-referenced research notes. Runs after /intake scope approval; feeds /tech-design. Use when the user wants research done on how to implement an approved scope.
argument-hint: "[task-id]"
---

# /research — source-referenced investigation

Produce `work/<id>/research-notes.md`: everything /tech-design needs to design
confidently, with every finding traceable to a source.

## 0. Preamble

1. Load lessons tagged `stage:research` from `${CLAUDE_PLUGIN_ROOT}/knowledge/lessons.md`.
2. Locate the workspace: the given task-id, else the single `work/*/STATUS.md`
   with next action /research, else ask. Verify `intake: approved` — if not,
   stop and direct the user to /intake.
3. Read `scope-contract.md`. It bounds the investigation: research serves the
   in-scope items; interesting adjacent findings go to PARKED.md.

## 1. Codebase investigation

Work from the contract's "interfaces & objects expected to change" table and
expand it:

1. **Locate and read** every named object: PL/SQL packages (spec AND body),
   SQL scripts/DDL, KSH scripts, Python modules. Read them, don't skim
   signatures.
2. **Build the call graph both directions**: who calls the affected objects
   (grep for package.proc names, script invocations, imports) and what they
   call. Record the exact grep/queries used so results are reproducible.
3. **Data model**: for each touched table/view, capture relevant columns,
   constraints, indexes, and (if the dev DB is reachable via `$SES_DB_CONN`)
   row volumes. Store queries + outputs in `evidence/research-*.txt`.
4. **Conventions**: read `.conventions.md` (run /repo-profile first if missing)
   and note which conventions bind this change.

### Accuracy rules

- Every finding row gets a source: `file:line`, the query used, or the doc/URL.
- If you infer something (e.g. "this job appears to run nightly"), label it
  `INFERRED` with the evidence, and add an open question to confirm.
- Do not trust names/comments over code: verify what a proc actually does
  before recording its role.

## 2. External research

Where the task needs approaches, library choices, or platform behaviour
(Oracle features, ksh portability, Python libraries): search authoritative
sources, record findings with URLs, and prefer versions matching the repo's
platform (note the Oracle/ksh/Python versions if discoverable).

## 3. Options and risks

- Sketch 2–3 implementation options with pros/cons grounded in the findings.
  Recommend one, but the decision lands in /tech-design.
- Record risks discovered (data volumes, concurrent jobs, fragile callers).

## 4. Write up and gate

1. Fill `${CLAUDE_PLUGIN_ROOT}/templates/research-notes.md` →
   `work/<id>/research-notes.md`.
2. Log out-of-scope findings to PARKED.md (never act on them).
3. Batch remaining open questions to the user; blocking ones must be answered
   before /tech-design.
4. Update STATUS.md: `research: done`, next action `/tech-design`.

## Fault tolerance

Write research-notes.md incrementally (section by section) so an interrupted
run resumes by reading what's already recorded and continuing from the first
empty section.
