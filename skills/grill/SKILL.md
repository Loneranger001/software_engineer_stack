---
name: grill
description: Adversarial interrogation of the technical design before the implementation document is written - stress-test the TDD with concrete edge-case scenarios, fix the gaps the evidence can answer, and grill the user for the answers it cannot. Runs between /tech-design and /impl-plan; also usable on a change-request analysis for risky CRs.
argument-hint: "[task-id]"
---

# /grill — the design survives the interview, or it changes

> Framework files: `<root>` is what `ses root` prints — run it once. Every
> framework script runs as `ses <command>` (`ses help` lists them). If `ses`
> is not on PATH, use `python3 <skill-dir>/../../bin/ses` in its place —
> `<skill-dir>` is the folder this SKILL.md was loaded from — here and for
> every `ses` below. If neither runs, stop and ask the user (README →
> Install); never guess another path.

The tech-design gates prove the TDD's claims are TRUE (fact-checker) and that
scope is covered (traceability). This stage attacks COMPLETENESS: the cases
nobody wrote down. Its output is a design with fewer surprises, and a log
proving which scenarios were confronted.

## 0. Preamble

1. Load applicable lessons: `ses lessons grill` — prior corrected
   assumptions and missed edge cases are exactly the scenarios to re-run.
2. Fresh context: the session that wrote the TDD is anchored on its own
   reasoning and grills it least hard. If this conversation authored the
   target document, say so and recommend a fresh session (or `/clear`)
   before Phase 1; if the user declines, note it in the grill log header.
3. Locate the workspace and gate, by pipeline (`ses status get <ws> pipeline`;
   `<ws>` = `<workspace-root>/work/<id>`):
   - **full**: `ses status require <ws> tech-design=approved`.
     Grilling an unapproved draft is fine if the user asks — skip the
     `require` and record it in the grill log's header ("grilled an
     unapproved TDD at user request").
   - **change-request** (see "Use on change requests"):
     `ses status require <ws> analyze=done`; the target is `analysis.md`.
4. Read tdd.md and ASSUMPTIONS.md fully — they are what you attack. Read the
   contract and research handoff summaries
   (`ses handoff show <ws>/<doc>`), opening a full section
   when a scenario needs its detail. With an approved functional design
   (`<ws>/fdd.md`; approval in `ses status get <ws> fdd`), read its handoff
   summary too — its business rules (BR#) and exceptions (EX#) are prime
   scenario material. Also read the repo rules research
   recorded (`<work-repo>` from STATUS.md — see
   `<root>/core/repo-resolution.md`), and the affected code.
5. Unknowns follow `<root>/core/decision-protocol.md`. In this
   skill the bias flips: the whole point is to ASK — proceed-and-log is
   reserved for trivia.

## 1. Phase 1 — self-grill (no user interruption yet)

Create `<ws>/grill-log.md` from
`<root>/templates/grill-log.md`.

Instantiate CONCRETE scenarios against the TDD from every category below,
using the task's real objects — "what if BALANCE_SNAPSHOT already has rows
for the rerun date", never "what about idempotency". Minimum one scenario per
category; a category that truly cannot apply is marked `n/a` with a reason.

- **Data**: nulls/empty sets, duplicates, zero-rows-affected, boundary values
  (0, negative, max), unexpected volumes, bad encodings/formats
- **Lifecycle**: rerun with same input (idempotency), restart after mid-run
  failure, concurrent execution, partial success/failure ordering
- **Interface**: callers sending the old format, missing/extra fields,
  consumers NOT in the research call graph (search with broader patterns via
  `ses search`; reuse research's recorded rows for repos whose sha is
  unchanged), contract version skew
- **Temporal**: date boundaries, month/year-end, DST/timezone, late-arriving
  or backdated data
- **Environment**: DB unreachable mid-run, missing config/env var, disk
  full/file undeliverable, credentials expired
- **Security/ops**: injection surfaces, missing grants, log noise vs silence,
  alerting on the new failure modes
- **Deploy/rollback**: deploy while the batch is running, sessions holding
  discarded package state (ORA-04068), dependents left INVALID after a
  recompile, grants/synonyms lost on recreate, multi-repo deploy order and
  the window between, rollback after a backfill or migration already ran

For each scenario, answer FROM the TDD and the code — with a source reference
(TDD §, file:line, or evidence). Decision-protocol §1 applies hard: if the
code or dev DB can answer it, check it, don't reason about it — run queries
through `ses capture <ws>/evidence grill-<n> -- …` so the cited evidence can
be re-run. Verdicts:

- `covered` — the design handles it; cite where.
- `gap-fixed` — only when ALL hold: exactly one defensible behaviour (a repo
  convention or an outright defect — cite it); the fix traces to an existing
  S#/A#; and it passes decision-protocol §2 (reversible, no data-changing or
  external-contract surface). EDIT the TDD now — design section, plus a §7
  Verification-approach row keyed `G<n>` (its grill-log row) when testable,
  so /impl-plan plans a test for it — and log the fix. Any choice between
  behaviours (replace, reject or merge?) is `ask-user`, however obvious.
- `ask-user` — needs domain or business knowledge the repo cannot provide,
  or a design choice the evidence cannot settle.
- `out-of-scope` — a real scenario the scope contract excludes; cite the
  exclusion. No exclusion covers it and the design doesn't handle it →
  `ask-user`, never assumed out.

A scenario that research or tech-design should have caught (a caller
missed, a claim that proves wrong) gets its stage in the log's "Upstream
miss" column — /retro turns those into lessons.

Also collect **terminology challenges**: any term the brief/TDD uses that has
two defensible readings ("balance: ledger or available?"). Consult
`<workspace-root>/work/domain-glossary.md` first — a documented, user-confirmed term with one
meaning is not a challenge; a term the brief BENDS away from its entry, or an
entry still `unconfirmed`, IS. Surviving challenges are always
`ask-user` — never resolve terminology by assumption.

## 2. Phase 2 — grill the user

Take the `ask-user` list and interview the user until it is EMPTY:

- Ask as concrete scenarios with the real objects and a proposed default
  ("The extract reruns for a date that already has GBP rows — replace them,
  reject the run, or merge? Current design silently replaces (tdd §4.2).").
- Group by theme; one theme at a time, highest blast radius first
  (data-changing and external-contract questions lead, so whatever is left
  when the user tires is cheap) — through the harness's ask-user tool
  where it has one, up to 4 questions per round. Do not dump twenty questions at once,
  and do not stop at one round if answers spawn follow-ups — that's the
  grilling.
- Every answer lands immediately: TDD design section updated, §7 `G<n>` row
  added when testable, terminology recorded in the grill log (and the TDD overview
  if load-bearing). Resolved terms also update
  `<workspace-root>/work/domain-glossary.md` marked `user-confirmed` — that's how the next task
  skips this question. An answer that changes a business rule or exception
  of an approved FDD amends the FDD first, re-approved per /func-design
  "Changes after approval"; the TDD follows it, never leads.
- The user may DEFER a question ("accept the risk", "later CR") — record the
  deferral verbatim in TDD §11 Risks (Mitigation: `accepted by <who> <date>:
  "<their words>"`), in the grill log, and as a PARKED.md row (found during
  grill), which is what /deliver's release notes and scope audit read — an
  accepted risk is handed over, not forgotten.
  Deferred is a user decision; unanswered is not a terminal state.

## 3. Close the stage

1. Self-check with `<root>/checklists/grill.md`.
2. If the grill edited the TDD (`gap-fixed`, user answers), fact-check the
   edits: run the procedure in
   `<root>/com.github.copilot/agents/doc-fact-checker.agent.md` on tdd.md,
   scoped to the edited sections — delegated per `<root>/core/reviewers.md`.
   A fix that adds a claim about existing behaviour is exactly what the
   tech-design fact-check never saw. Resolve all findings.
3. Every TDD edit updates the TDD's handoff summary in the same edit — its
   Verification line names every `G#` row, which
   `ses handoff check <ws>/tdd.md` enforces like A#; re-run it before closing.
4. An approved TDD the grill edited is re-approved, never silently changed —
   whatever the size of the edits. Present ONE change list built from the
   grill log's TDD-changing rows (`#n · TDD § · before → after`, one line
   each) with the fact-check verdict; one approval covers it. Record it as a
   TDD header note (`re-approved after /grill <date>: <n> edits`) and with
   `ses status set <ws> tech-design=approved --note "re-approved after grill, <n> edits"`.
   An edit the user rejects is reverted and its row goes back to `ask-user`.
   No TDD edits, or an unapproved TDD, needs no re-approval.
5. Record (full pipeline):
   `ses status set <ws> grill=done --next "Run /impl-plan."`
   — or, if the user explicitly skipped it,
   `grill="waived by <who> <date>: <reason>"`. A change-request pipeline has
   no grill stage: the grill log's closing line records it instead ("grill
   done on analysis.md: <n> scenarios, <m> answered by user").

## Use on change requests

For a borderline CR (escalation factors near the threshold in
/change-request §1), run this skill against `analysis.md` instead of a TDD:
same categories, same verdicts, answers land in the mini scope contract.

## Fault tolerance

grill-log.md is the resume point: scenarios already verdicted are skipped on
re-run; an interrupted phase 2 resumes from the first `ask-user` row without
an answer.
