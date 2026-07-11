---
name: tech-design
description: Produce a technical design document (TDD) from the approved scope contract and research notes, with full requirements traceability and fact-checked claims. Gates on user approval. Use when research is done and a technical design is needed.
argument-hint: "[task-id]"
---

# /tech-design — traceable technical design document

Produce `work/<id>/tdd.md` and get it user-approved. The TDD is the contract
for HOW the scope will be met.

## 0. Preamble

1. Load lessons tagged `stage:tech-design` from
   `${CLAUDE_PLUGIN_ROOT}/knowledge/lessons.md`.
2. Locate the workspace; verify STATUS.md shows `research: done`. If research
   is missing or stale (scope contract version newer than the notes), send the
   user back to /research.
3. Read scope-contract.md AND research-notes.md fully.

## 1. Design

1. Copy `${CLAUDE_PLUGIN_ROOT}/templates/tdd.md` → `work/<id>/tdd.md`.
2. Choose the implementation option (from research §Options) and justify it in
   §8 Alternatives; if you deviate from the research recommendation, say why.
3. Fill §2 traceability FIRST: every in-scope item → the design section that
   will satisfy it. If an item has no natural home, the design is incomplete.
4. Design each component against the repo's conventions (`.conventions.md`,
   else `${CLAUDE_PLUGIN_ROOT}/standards/<language>.md`): naming, error
   handling, logging, transaction boundaries.
5. Data model changes always carry migration/backfill AND rollback.
6. Interface impact (§6) must cite the research call graph. "No callers
   affected" requires the evidence, not the assertion.

### Scope discipline

- Design NOTHING that maps to an exclusion or to no scope item. If the design
  genuinely needs something the contract excludes, stop and ask the user for a
  scope-contract version bump — do not design around the contract.

### Accuracy

- Claims about existing behaviour keep their source references (carry them
  over from research-notes.md; add new ones for anything newly read).
- Pseudocode/signatures must compile against reality: correct object names,
  parameter types from the actual specs.

## 2. Quality gates

1. Self-check with `${CLAUDE_PLUGIN_ROOT}/checklists/tech-design.md`.
2. Launch the `doc-fact-checker` agent on tdd.md (it verifies every claim
   against the code). Resolve all findings.
3. Present the TDD to the user for approval: summary, key decisions,
   traceability table, risks. Iterate until approved; record approval + date
   in the TDD header.
4. Update STATUS.md: `tech-design: approved`, next action `/impl-plan`.

## Fault tolerance

Write the TDD incrementally. On resume, diff the traceability table against
the scope contract to find unfinished sections. Never edit an approved TDD
silently — changes after approval require re-approval and a note in the header.
