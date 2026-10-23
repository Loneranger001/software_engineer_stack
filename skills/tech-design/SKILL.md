---
name: tech-design
description: Produce a technical design document (TDD) from the approved scope contract and research notes, with full requirements traceability and fact-checked claims. Gates on user approval. Use when research is done and a technical design is needed.
argument-hint: "[task-id]"
---

# /tech-design — traceable technical design document

> Framework files: `<root>` is what `ses root` prints — run it once. Every
> framework script runs as `ses <command>` (`ses help` lists them). If `ses`
> is not on PATH, use `python3 <skill-dir>/../../bin/ses` in its place —
> `<skill-dir>` is the folder this SKILL.md was loaded from — here and for
> every `ses` below. If neither runs, stop and ask the user (README →
> Install); never guess another path.

Produce `<ws>/tdd.md` and get it user-approved. The TDD is the contract
for HOW the scope will be met.

## 0. Preamble

1. Load applicable lessons: `ses lessons tech-design` — it prints only
   the matching entries; don't read the lesson files whole.
2. Locate the workspace and gate:
   `ses status require <ws> research=done`
   (`<ws>` = `<workspace-root>/work/<id>`) — non-zero exit = stop. Take
   `<work-repo>` from `ses status get <ws> work-repo`
   (`<root>/core/repo-resolution.md`) — repo-level files below
   hang off it, not off your cwd.
3. Read scope-contract.md fully — traceability must cover every S# and A#.
   For research, read its handoff summary
   (`ses handoff show <ws>/research-notes.md`) and open a
   research section only when designing the component it concerns.
   `ses handoff check <ws>/research-notes.md` reporting an older contract
   version means research is stale: send the user back to /research.
   If the task has an approved functional design (`<ws>/fdd.md`; approval in
   `ses status get <ws> fdd`), read its handoff summary
   (`ses handoff show <ws>/fdd.md`): the TDD realises it — every FR# joins the
   S# items in §2 traceability, its business rules (BR#) and exceptions
   (EX#) are honoured, and a design that has to depart from it goes back to
   the user as an FDD amendment, re-approved before the TDD diverges.
4. Unknowns follow `<root>/core/decision-protocol.md`: design
   judgment calls that pass §2 (high confidence, reversible, in-scope, no
   dangerous surface) go to ASSUMPTIONS.md; anything else stops and asks.

## 1. Design

1. Copy `<root>/templates/tdd.md` → `<ws>/tdd.md`.
2. Choose the implementation option (from research §Options) and justify it in
   §10 Alternatives; if you deviate from the research recommendation, say why.
3. Fill §2 traceability FIRST: every in-scope item → the design section that
   will satisfy it. If an item has no natural home, the design is incomplete.
4. Design each component against the rules of the repo it lands in
   (its rules files per `ses repo-rules` — a component designed for a sibling
   repo follows that repo's rules, not the primary repo's; else
   `<root>/standards/<language>.md`): naming, error
   handling, logging, transaction boundaries. §1 Overview lists every
   business term the TDD relies on, so the handed-over TDD reads on its own:
   a global term with its `Meaning` line copied verbatim from
   `<workspace-root>/work/domain-glossary.md` (never re-defined); a
   repo-specific term — left out of the glossary — defined for its repo from
   the research notes.
5. Draw the as-is and to-be mermaid flow diagrams from the research call
   graph — never from memory; the fact-checker verifies them against the code.
6. Data model changes always carry migration/backfill AND rollback.
7. Interface impact (§6) must cite the research call graph, **naming the repo
   of each affected caller**. "No callers affected" requires the evidence from
   every repo in `<repo-set>`, not the assertion — and where callers live in
   repos this task will not change, say how they keep working (backward
   compatibility, or a follow-up recorded with the user).

### Scope discipline

- Design NOTHING that maps to an exclusion or to no scope item. If the design
  genuinely needs something the contract excludes, stop and ask the user for a
  scope-contract version bump — do not design around the contract.

### Accuracy

- Claims about existing behaviour keep their source references: copy the
  code references (`file:line`) over from research-notes.md and add new ones
  for anything newly read. Never cite research-notes.md itself — it stays
  in the workspace, so the reader of the handed-over TDD cannot open it.
- Pseudocode/signatures must compile against reality: correct object names,
  parameter types from the actual specs.

## 2. Quality gates

1. Self-check with `<root>/checklists/tech-design.md`.
2. Run the fact-check procedure in
   `<root>/com.github.copilot/agents/doc-fact-checker.agent.md` on tdd.md (it verifies
   every claim against the code) — delegated per `<root>/core/reviewers.md`. Resolve all
   findings.
3. Write the TDD's **handoff summary** block now — after the fact-check
   fixes — and run `ses handoff check <ws>/tdd.md`; it must pass.
4. **Review version.** tdd.md is the agent version: complete and traceable,
   read by /grill, /impl-plan and the reviewers. People read and approve a
   short review version written from it. Copy
   `<root>/templates/tdd-review.md` → `<ws>/tdd.review.md` and fill it from
   tdd.md: In short first, two pages (four at most), plain words per
   `<root>/standards/writing.md` — about the system, never about how the
   design was made; no coined noun stacks or slashes; no visible IDs. Each
   part ends with a hidden `covers:` anchor naming the tdd.md IDs it covers;
   every S, FR, A and G of tdd.md is covered somewhere. Then run
   `ses review-version stamp <ws>/tdd.md`,
   `ses review-version check <ws>/tdd.md` and
   `ses prose-lint <ws>/tdd.review.md`; all must pass.
5. **Agreement check.** Run the doc-fact-checker procedure on tdd.review.md
   against tdd.md — delegated per `<root>/core/reviewers.md` — and fix every
   finding in the review version (in tdd.md first when tdd.md is unclear).
6. Render the review version (`ses review-version render <ws>/tdd.md` →
   `<ws>/deliverables/tdd.review.md`) and present it — it is what the user
   approves — plus open ASSUMPTIONS.md entries for ratification
   (decision-protocol §4); promote design-shaping ones into the TDD. Iterate
   until approved — each revision changes tdd.md first, then its summary
   and the review version in the same edit; re-stamp, re-run the checks,
   and re-run the agreement check on the changed parts. Record approval +
   date in both headers.
7. Record:
   `ses status set <ws> tech-design=approved --next "Run /grill."`
   (the
   adversarial completeness interrogation runs before any implementation
   planning).

## Fault tolerance

Write the TDD incrementally. On resume, diff the traceability table against
the scope contract to find unfinished sections. Never edit an approved TDD
silently — changes after approval require re-approval and a note in the
header. Every change to tdd.md updates tdd.review.md in the same edit and is
re-approved on it; `ses handoff check` fails until the review version is
re-stamped.
