---
name: impl-plan
description: Produce an implementation document from the approved TDD - ordered commit-sized steps with per-step verification and rollback, a test plan covering every acceptance criterion, and deployment steps. Gates on user approval. Use after the TDD is approved.
argument-hint: "[task-id]"
---

# /impl-plan — executable implementation document

Produce `work/<id>/impl-doc.md` and get it user-approved. /implement will
execute this document literally, so it must be executable by someone (or some
session) with no memory of this conversation.

## 0. Preamble

1. Load lessons tagged `stage:impl-plan` from
   `${CLAUDE_PLUGIN_ROOT}/knowledge/lessons.md`.
2. Locate the workspace; verify `tech-design: approved` in STATUS.md.
3. Read scope-contract.md and the approved tdd.md.

## 1. Plan the steps

1. Copy `${CLAUDE_PLUGIN_ROOT}/templates/impl-doc.md` → `work/<id>/impl-doc.md`.
2. Decompose the TDD into ordered, commit-sized steps. Ordering rules:
   - The system stays consistent between steps (DDL before code that needs it;
     backward-compatible interface changes before caller updates).
   - Any step that leaves a temporary inconsistency says so and is immediately
     followed by the step that restores consistency.
3. Every step row gets: files/objects touched, its OWN verification (what
   /verify-code or which test proves it), and its OWN rollback note naming the
   exact revert action.
4. Name the task branch (follow the repo's branch conventions from
   `.conventions.md`, e.g. `feature/<task-id>`).

## 2. Test plan

- Map every acceptance criterion A# to at least one test T#. A criterion
  without a test is a planning failure.
- Reuse the repo's existing test tooling (utPLSQL, pytest, script harnesses —
  see `.conventions.md`); only introduce new tooling with user agreement.
- Include regression: which existing behaviours are touched (from the TDD §6
  interface impact) and how each is re-checked.
- For DB changes, specify before/after queries for the evidence bundle.

## 3. Deployment and rollback

- §4 deployment steps: exact commands per environment, each with its
  verification. Assume the executor has the release notes and this document only.
- §5 whole-change rollback: concrete (scripts, previous object versions,
  data restoration), not "revert the change".

## 4. Gate

1. Self-check with `${CLAUDE_PLUGIN_ROOT}/checklists/impl-plan.md`.
2. Present to the user: step table, test-to-criterion mapping, rollback
   summary. Iterate until approved; record approval in the header.
3. Update STATUS.md: `impl-plan: approved`, next action `/implement`.

## Fault tolerance

The impl-doc is itself the fault-tolerance mechanism for /implement: steps are
independently verifiable and rollbackable. Keep it that way — if a review
comment makes two steps merge into one big one, split differently instead.
