# Release Notes — {TASK_ID}: {TITLE}

- Date: {date}
- Branch / tag: {…}
- Scope contract: v{n} — scope audit: PASS ({date})

## Summary

{One paragraph: what changed and why, for a reader outside the team.}

## Changes

| Object / file | Type | Change | Scope item |
|---|---|---|---|
| {SCHEMA.PKG_X} | PL/SQL | {modified proc P to …} | S1 |

## Deployment

<!-- Written out in full from impl-doc.md §4 — the impl doc is agent-only
     and is not handed over. -->
{Ordered deployment steps, with the environment prerequisites and the check
to run after each step.}

## Rollback

<!-- Written out in full from impl-doc.md §5, so operations can act on
     this document alone. -->
{Ordered rollback steps for each repo, in reverse deployment order.}

## Verification evidence

| Acceptance criterion | Evidence file | Result |
|---|---|---|
| A1 | evidence/{…} | PASS |

## Known limitations / follow-ups

<!-- Include the PARKED.md items handed over for future triage, each written
     as a fact about the system. -->
{Limitations and follow-up work that the team that runs the system must know
about.}
