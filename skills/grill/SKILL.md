---
name: grill
description: Adversarial interrogation of the technical design before the implementation document is written - a fresh design-griller agent stress-tests the TDD with concrete edge-case scenarios and fixes the gaps the evidence can answer, then the user is grilled for the answers it cannot. Runs between /tech-design and /impl-plan; also usable on a change-request analysis for risky CRs.
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

The attack always runs in a fresh context. The session that wrote the TDD is
anchored on its own reasoning and grills it least hard; a session that
discussed it remembers what was said but never written down, and counts it as
covered. So Phase 1 runs in the `design-griller` agent, never in this
conversation, whoever wrote the TDD. This session runs the interview
(Phase 2), which only it can, and closes the stage.

## 0. Preamble

1. Locate the workspace — the given task-id, else the single
   `<workspace-root>/work/*/STATUS.md` with next action /grill, else ask —
   and gate by pipeline (`ses status get <ws> pipeline`;
   `<ws>` = `<workspace-root>/work/<id>`):
   - **full**: `ses status require <ws> tech-design=approved`.
     Grilling an unapproved draft is fine if the user asks — skip the
     `require` and record it in the grill log's header ("unapproved, grilled
     at user request").
   - **change-request** (see "Use on change requests"):
     `ses status require <ws> analyze=done`; the target is `analysis.md`.

   Take `<work-repo>` and `<workspace-root>` from `ses status show <ws>`
   (`<root>/core/repo-resolution.md`), never from your cwd.
2. Resume: a `<ws>/grill-log.md` whose header reads `Phase 1: done` → go to
   Phase 2. Otherwise run Phase 1; the agent resumes a partial log.
3. Unknowns follow `<root>/core/decision-protocol.md`. In this
   skill the bias flips: the whole point is to ASK — proceed-and-log is
   reserved for trivia.

## 1. Phase 1 — self-grill, in a fresh context

Delegate it — never run it in this conversation. Use the first option the
harness offers (`<root>/core/reviewers.md`):

1. **The installed `design-griller` custom agent** (in Copilot, delegate to
   it as a subagent). Context line: `design-griller agent`.
2. **A fresh subagent** told to read
   `<root>/com.github.copilot/agents/design-griller.agent.md` in full and
   follow it exactly. It must start empty: never a fork, nor any subagent
   that inherits this conversation. Context line: `fresh subagent`.
3. **No subagent tool:** Phase 1 runs here only in a session started for
   this grill — a new session, or one just cleared with `/clear`, that has
   not read or discussed the target before this /grill. Ask the user to
   confirm that, then follow the agent file yourself, every input read from
   disk. Context line: `fresh session (confirmed by <who> <date>)`. Not
   confirmed → stop, and tell the user to start a new session (or `/clear`)
   and run `/grill <task-id>` there. Only the user can waive this; record
   `same session (waived by <who> <date>: <reason>)` and continue.

The delegation prompt carries the agent's inputs and nothing else: `<ws>`,
the target (`tdd.md`, or `analysis.md` for a change request), whether it is
approved or grilled unapproved at the user's request, the Context line, the
`ses` command you resolved, and `<root>`. Never add a summary of the design,
reasons it is sound, or what you expect it to find — that hands the agent the
anchoring it exists to avoid. Write the prompt from this list, not from
memory.

When the agent reports, check that the grill log reads `Phase 1: done`,
carries the Context line, and covers every category (a scenario, or `n/a`
with a reason). A report of `incomplete` → delegate again; the agent resumes
the log. Never re-verdict its rows: you may add a scenario, or move a row to
`ask-user` with the reason, but never move one the other way — this
session's memory of the design is what Phase 1 was kept away from.

## 2. Phase 2 — grill the user

Read the grill log, the TDD sections its `ask-user` rows cite, and — with an
approved functional design (`<ws>/fdd.md`; approval in
`ses status get <ws> fdd`) — the FDD's handoff summary. Then interview the
user until no `ask-user` row is left without an answer:

- Ask each row as the log words it: the concrete scenario with the real
  objects, what the design does now, and the proposed default ("The extract
  reruns for a date that already has GBP rows — replace them, reject the run,
  or merge? Current design silently replaces (tdd §4.2)."). Never close a row
  from what this conversation remembers: if you think the TDD already
  answers it, say so in the question with the § — the user's answer closes
  it.
- Group by theme; one theme at a time, highest blast radius first
  (data-changing and external-contract questions lead, so whatever is left
  when the user tires is cheap) — through the harness's ask-user tool
  where it has one, up to 4 questions per round. Do not dump twenty questions at once,
  and do not stop at one round if answers spawn follow-ups — that's the
  grilling.
- Every answer lands immediately: TDD design section updated, §7 `G<n>` row
  added when testable, the row's verdict set to `answered` with its TDD
  ref, terminology recorded in the grill log (and the TDD overview
  if load-bearing). Resolved terms that hold in every repo also update
  `<workspace-root>/work/domain-glossary.md` marked `user-confirmed` — that's how the next task
  skips this question; a repo-specific answer stays in the TDD and grill log. An answer that changes a business rule or exception
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
2. If the grill edited the TDD (the agent's `gap-fixed` rows, user answers),
   fact-check the edits: run the procedure in
   `<root>/com.github.copilot/agents/doc-fact-checker.agent.md` on tdd.md,
   scoped to the edited sections — delegated per `<root>/core/reviewers.md`.
   A fix that adds a claim about existing behaviour is exactly what the
   tech-design fact-check never saw. Resolve all findings.
3. Every TDD edit updates the TDD's handoff summary in the same edit — its
   Verification line names every `G#` row, which
   `ses handoff check <ws>/tdd.md` enforces like A# — and, once the TDD has
   one, its review version (tdd.review.md, a `covers:` anchor for each new
   `G#`), re-stamped with `ses review-version stamp <ws>/tdd.md`; the
   handoff check enforces that too. Re-run it before closing.
4. An approved TDD the grill edited is re-approved, never silently changed —
   whatever the size of the edits. Present ONE change list built from the
   grill log's TDD-changing rows (`#n · TDD § · before → after`, one line
   each) with the fact-check verdict, plus the updated review version
   rendered (`ses review-version render <ws>/tdd.md`); one approval covers
   it. Record it as a
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
Phase 1 is delegated the same way with `analysis.md` as the target — same
categories, same verdicts — and answers land in the mini scope contract.

## Fault tolerance

grill-log.md is the resume point. An interrupted Phase 1 is delegated again:
the agent keeps every verdicted row and continues. An interrupted Phase 2
resumes from the first `ask-user` row without an answer, in any session —
the questions are on disk.
