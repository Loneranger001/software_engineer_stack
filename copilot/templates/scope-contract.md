# Scope Contract — {TASK_ID}: {TITLE}

> The single source of scope truth for this task. Approved by the user at intake.
> Every later stage re-reads this file. Work not covered here goes to PARKED.md.

- Source brief: {path or link to the SDD / requirement brief}
- Approved by: {user} on {date}
- Version: 1 (bump on any user-approved scope change; record the change in History)

## Objective

{One paragraph: the business/technical outcome this task must achieve.}

## In scope

<!-- Concrete, checkable items. Each becomes a row in the traceability matrix. -->
| # | Item | Source (brief section / requester) |
|---|---|---|
| S1 | {e.g. Add column X to table Y and populate via package Z} | {brief §2.1} |

## Out of scope / non-goals

<!-- Explicitly excluded, even if adjacent or tempting. -->
| # | Item | Why excluded |
|---|---|---|
| N1 | {e.g. Refactoring package Z's error handling} | {not requested; separate CR} |

## Acceptance criteria

<!-- How we will know each in-scope item is done. Verifiable statements only. -->
| # | Criterion | Verifies | How verified |
|---|---|---|---|
| A1 | {e.g. SELECT of new column returns populated values for existing rows} | S1 | {SQL run captured in evidence/} |

## Interfaces & objects expected to change

<!-- Best current knowledge; refined by /research. -->
| Object | Type | Change |
|---|---|---|
| {SCHEMA.PKG_NAME} | PL/SQL package | {modify proc P} |

## Assumptions & open questions

| # | Assumption / Question | Status | Resolution |
|---|---|---|---|
| Q1 | {…} | open / answered | {…} |

## Constraints

- {e.g. no downtime; must follow repo conventions in .conventions.md; delivery by …}

## History

| Version | Date | Change | Approved by |
|---|---|---|---|
| 1 | {date} | Initial contract | {user} |
