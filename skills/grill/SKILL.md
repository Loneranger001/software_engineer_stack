---
name: grill
description: Adversarial interrogation of the technical design before the implementation document is written - stress-test the TDD with concrete edge-case scenarios, fix the gaps the evidence can answer, and grill the user for the answers it cannot. Runs between /tech-design and /impl-plan; also usable on a change-request analysis for risky CRs.
argument-hint: "[task-id]"
---

# /grill — the design survives the interview, or it changes

> Path note: `${CLAUDE_PLUGIN_ROOT}` is this framework's root — the ancestor
> directory of this file containing `plugin.json`/`skills/`. Claude Code resolves
> it automatically; other harnesses resolve it from this file's location.

The tech-design gates prove the TDD's claims are TRUE (fact-checker) and that
scope is covered (traceability). This stage attacks COMPLETENESS: the cases
nobody wrote down. Its output is a design with fewer surprises, and a log
proving which scenarios were confronted.

## 0. Preamble

1. Load lessons tagged `stage:grill` from
   `${CLAUDE_PLUGIN_ROOT}/knowledge/lessons.md` — prior corrected assumptions
   and missed edge cases are exactly the scenarios to re-run.
2. Locate the workspace; verify `tech-design: approved` (grilling an
   unapproved draft is fine too if the user asks — note it in STATUS.md).
3. Read scope-contract.md, research-notes.md, tdd.md, ASSUMPTIONS.md,
   `.conventions.md`, and the affected code.
4. Unknowns follow `${CLAUDE_PLUGIN_ROOT}/core/decision-protocol.md`. In this
   skill the bias flips: the whole point is to ASK — proceed-and-log is
   reserved for trivia.

## 1. Phase 1 — self-grill (no user interruption yet)

Create `work/<id>/grill-log.md` from
`${CLAUDE_PLUGIN_ROOT}/templates/grill-log.md`.

Instantiate CONCRETE scenarios against the TDD from every category below,
using the task's real objects — "what if BALANCE_SNAPSHOT already has rows
for the rerun date", never "what about idempotency". Minimum one scenario per
category; a category that truly cannot apply is marked `n/a` with a reason.

- **Data**: nulls/empty sets, duplicates, zero-rows-affected, boundary values
  (0, negative, max), unexpected volumes, bad encodings/formats
- **Lifecycle**: rerun with same input (idempotency), restart after mid-run
  failure, concurrent execution, partial success/failure ordering
- **Interface**: callers sending the old format, missing/extra fields,
  consumers NOT in the research call graph, contract version skew
- **Temporal**: date boundaries, month/year-end, DST/timezone, late-arriving
  or backdated data
- **Environment**: DB unreachable mid-run, missing config/env var, disk
  full/file undeliverable, credentials expired
- **Security/ops**: injection surfaces, missing grants, log noise vs silence,
  alerting on the new failure modes

For each scenario, answer FROM the TDD and the code — with a source reference
(TDD §, file:line, or evidence). Decision-protocol §1 applies hard: if the
code or dev DB can answer it, check it, don't reason about it. Verdicts:

- `covered` — the design handles it; cite where.
- `gap-fixed` — a real gap the evidence can resolve without the user; EDIT
  the TDD now (design section + a §7 Verification-approach row so it gets
  tested), log the fix.
- `ask-user` — needs domain or business knowledge the repo cannot provide.

Also collect **terminology challenges**: any term the brief/TDD uses that has
two defensible readings ("balance: ledger or available?"). Consult the repo's
`.domain-glossary.md` first — a documented, user-confirmed term with one
meaning is not a challenge; a term the brief BENDS away from its entry, or an
entry still `seeded — unconfirmed`, IS. Surviving challenges are always
`ask-user` — never resolve terminology by assumption.

## 2. Phase 2 — grill the user

Take the `ask-user` list and interview the user until it is EMPTY:

- Ask as concrete scenarios with the real objects and a proposed default
  ("The extract reruns for a date that already has GBP rows — replace them,
  reject the run, or merge? Current design silently replaces (tdd §4.2).").
- Group by theme; one theme at a time (use AskUserQuestion where the harness
  has it, up to 4 questions per round). Do not dump twenty questions at once,
  and do not stop at one round if answers spawn follow-ups — that's the
  grilling.
- Every answer lands immediately: TDD design section updated, §7 row added
  when testable, terminology recorded in the grill log (and the TDD overview
  if load-bearing). Resolved terms also update the repo's
  `.domain-glossary.md` marked `user-confirmed` — that's how the next task
  skips this question.
- The user may DEFER a question ("accept the risk", "later CR") — record the
  deferral verbatim in TDD §11 Risks with their ack, and in the grill log.
  Deferred is a user decision; unanswered is not a terminal state.

## 3. Close the stage

1. Self-check with `${CLAUDE_PLUGIN_ROOT}/checklists/grill.md`.
2. If the grill materially changed an already-approved TDD, re-present the
   changed sections for approval (never silently edit an approved document).
3. Update STATUS.md: `grill: done` (or `grill: waived by user` if the user
   explicitly skipped it — record who/when), next action `/impl-plan`.

## Use on change requests

For a borderline CR (escalation factors near the threshold in
/change-request §1), run this skill against `analysis.md` instead of a TDD:
same categories, same verdicts, answers land in the mini scope contract.

## Fault tolerance

grill-log.md is the resume point: scenarios already verdicted are skipped on
re-run; an interrupted phase 2 resumes from the first `ask-user` row without
an answer.
