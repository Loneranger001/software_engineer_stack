# Technical Design Document — {TASK_ID}: {TITLE}

- Status: draft | user-approved ({date})
- Inputs: scope-contract.md v{n}, research-notes.md
- Author: Claude, reviewed by {user}

<!-- ONE DOCUMENT FOR PEOPLE AND AGENTS: the user reads and approves it,
     and /grill, /impl-plan and the reviewers work from it. Keep it complete
     and traceable, and write every sentence in plain words and short
     sentences per <root>/standards/writing.md (check: ses prose-lint <file>).
     - Say what the system does and what the design changes. Never say how
       the design was made: no research, task, scope contract, or stage
       names.
     - Say the thing, then give its ID in brackets or in a column.
     - Cite code references as <repo>:<path>:<line>, never bare file:line
       and never research-notes.md: the fact-checker verifies them, and a
       reader handed the TDD can follow them. Signatures and pseudocode go in code blocks, not in sentences. -->

<!-- handoff:start -->
## Handoff summary
<!-- Written last, at this stage's gate, and updated in the same edit as any
     amendment. Later stages read ONLY this block unless they need a section's
     detail. One line per ID; max 40 lines. Check: ses handoff check <file>. -->
- Contract version: {n}
- Approach: {two lines at most}
- Components: §4.1 {repo}:{object} — {change}; §4.2 …
- Traceability: S1 → §4.1, §5
- Data changes: {object — DDL one-liner, backfill yes/no} (§5)
- Interface impact: {repo}:{caller} — {impact, one line} (§6)
- Verification: A1 → {unit|integration|regression}; TS1 → {…}; G2 → {…} (§7)
- Operational: {deploy/runtime one-liner} (§8)
- Top risks: {one line each} (§11)
<!-- handoff:end -->

## 1. Overview

<!-- Lead with what the reader needs most. A reader who stops here knows
     the approach, the main risk, and what to decide. -->
{What changes and why, in one or two short paragraphs that a person who has
not read the brief can follow. For example: "The nightly order job will send
approved orders to EDI vendors each night instead of each week. The change
adds one procedure to PKG_ORDER_EDI and one column to ORDHEAD. The main risk
is a longer nightly run."}

Business terms used in this document:

<!-- One row per business term this document relies on, so it reads on its -->
<!-- own when handed over. A global term: its `Meaning` line copied VERBATIM -->
<!-- from <workspace-root>/work/domain-glossary.md, never paraphrased — the -->
<!-- doc-fact-checker flags a row that differs. A term the glossary leaves -->
<!-- out because its meaning differs by repo: define it here for the repo -->
<!-- this document concerns, from the research notes, naming the repo. -->

| Term | Meaning |
|---|---|
| {Order} | {Order means purchase order; it exists in ORDHEAD (header) and ORDSKU (detail).} |
| {Upload (repo1)} | {repo1 only: loads the day's file into TABLE1} |

## 2. Requirements traceability

<!-- Every in-scope item from the scope contract must map to at least one design section.
     With an approved fdd.md, each of its FR# items gets a row too, even
     when the FDD is approved after this TDD (the TDD is then re-approved). -->
| Scope item | Design section(s) |
|---|---|
| S1 | §4.1, §5 |

## 3. Current state

<!-- Condensed from research-notes.md: carry over its code references, not
     the notes themselves. -->
{How the function works today, with a code reference (repo:path:line) for
each claim.}

### As-is flow

<!-- Must match the research call graph — the fact-checker verifies diagrams
     against the actual call order. Keep source refs under the diagram. -->
```mermaid
flowchart TD
    {trigger/schedule} --> {entry point}
    {entry point} --> {component} --> {data object / file}
```

{One paragraph that walks through the diagram, with a code reference for
each step.}

## 4. Proposed design

### To-be flow

<!-- Same notation as the as-is diagram; highlight what changes (new/changed
     nodes marked, e.g. with `:::changed` or a note). -->
```mermaid
flowchart TD
    {as-is flow with the changed/new hops marked}
```

{One paragraph: what differs from as-is, and why.}

### 4.1 {Component / object 1}

- Object: {SCHEMA.PKG_NAME or path}
- Change type: new | modify | drop
- Design: {signatures, pseudocode where useful, data flow}
- Error handling: {…}
- Source references for claims about existing behaviour: {repo:path:line}

### 4.2 {Component / object 2}

## 5. Data model changes

| Object | DDL summary | Migration / backfill | Rollback |
|---|---|---|---|

## 6. Interface impact

<!-- "None" must be backed by the research call graph and the search across
     every repo in the analysis scope, not only the repo being changed. Write
     the result as a fact about the system ("No other program in repo-a,
     repo-b or repo-c reads this table"), not as a report of the search. -->
{Which callers are affected, which interfaces change, and how existing
callers keep working.}

| Repo | Caller | Impact | Changes here? | How it keeps working |
|---|---|---|---|---|
| {repo-b} | {src/py/loader.py:88} | {new column in extract} | no | {ignores unknown columns — verified} |

## 7. Verification approach

<!-- Every acceptance criterion from the scope contract appears here, and
     with an approved fdd.md each of its test scenarios (TS#) too. One row
     per test: the first cell names every criterion that test proves
     ("A1, TS1") — no duplicate rows. `ses handoff check` and `ses coverage`
     fail a contract A# or FDD TS# that no row names. A criterion with no
     viable test blocks TDD approval — fix the design or renegotiate the
     criterion. /grill adds G# IDs (grill-log scenario #) for the edge cases
     it closes, to an existing row or a new one; they get tests like any A#.
     The detailed test plan lands in impl-doc §3. -->
| Criteria (A#, TS# from the FDD, G# from /grill) | Test type (unit / integration / regression) | Sketch |
|---|---|---|
| {A1, TS1} | {…} | {…} |

## 8. Operational impact

<!-- Batch reality check. "None" must be stated per line, not implied. -->
- Schedule and trigger changes: {…}
- Restartability: {how the changed job behaves on rerun after failure}
- File handoffs: {new or changed files, and whether their consumers know}
- Logging & monitoring: {new log lines, alerts, what ops should watch}
- Run duration and volumes: {expected change, basis}

## 9. Non-functional considerations

- Performance: {expected volumes, plans, indexes}
- Security: {grants, injection surfaces, secrets}
- Operability: {anything not already covered in §8}

## 10. Alternatives considered

| Alternative | Why rejected |
|---|---|

## 11. Risks & mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|

## 12. Out of scope

<!-- The scope contract's exclusions (N#) that a reader might expect here. -->
{What a reader might expect in this design but it does not cover.}
