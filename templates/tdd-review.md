# {Title} — technical design

- Status: draft | approved by {name} on {date}
- For: {who reviews it: tech lead, developers, operations}

<!-- REVIEW VERSION — what people read and approve. Write it from the
     fact-checked tdd.md (the agent version) and keep it in step: every
     change to tdd.md changes this file in the same edit (checked by:
     ses review-version check <ws>/tdd.md).
     - Simple first: two pages is the aim, four the most. A reader who stops
       after "In short" knows the approach, the main risk, and what to
       decide.
     - Plain words and short sentences: <root>/standards/writing.md (check:
       ses prose-lint <file>). Program, table, and file names are fine;
       signatures, pseudocode, DDL, traceability tables, and source
       references stay in tdd.md.
     - Say what the design does. Never say how it was made — no research,
       task, scope contract, or stage names.
     - No visible IDs. End each paragraph, row, or bullet with a hidden
       anchor that names the tdd.md IDs it covers: an HTML comment that
       starts with "covers:", as in the rows below. Every scope item (S),
       requirement (FR), acceptance criterion (A), and grill case (G) of
       tdd.md is covered somewhere.
     - A section with nothing to say holds one line ("None."), or is
       deleted when a reader would not miss it. -->

## In short

{The nightly order job will send approved orders to EDI vendors each night
instead of each week. The change adds one procedure to PKG_ORDER_EDI and one
column to ORDHEAD. The main risk is a longer nightly run. You must decide
whether the old weekly job stays as a fallback for one month.}

## What changes

| Where | What changes | Why |
|---|---|---|
| {PKG_ORDER_EDI (database package)} | {A new procedure sends approved orders each night} | {Vendors get orders on the day of approval} <!-- covers: S1 --> |

## Data changes

{What changes in the database, how existing rows are filled, and how to
undo it — or "None."}

## Who else is affected

{Each other program or team that uses what changes, and how it keeps
working. If nothing else uses it, say so, and name the repositories that
you checked: "No other program in repo-a or repo-b reads this column."}

## How it is tested

| What is checked | How |
|---|---|
| {An approved order reaches the vendor file on the same night} | {Integration test on the development database} <!-- covers: A1 --> |

## Running it

{Changes to the schedule, what a rerun after a failure does, new logs or
alerts, and the change in run time — or "No change."}

## Risks

| Risk | What reduces it |
|---|---|
| {…} | {…} |

## Options not chosen

| Option | Why not |
|---|---|
| {…} | {…} |

## Questions for you

1. {…}

## Approval

| Name | Role | Date | Decision |
|---|---|---|---|
