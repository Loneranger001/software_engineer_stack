# Functional Design Document — {TASK_ID}: {TITLE}

- Status: draft | user-approved ({date})
- Audience: {business | technical} — {who: business owner, functional analysts, UAT testers, developers}
- Author: Claude, reviewed by {user}
<!-- technical:start -->
- Mode: forward (proposed change) | as-built (existing behaviour) | change (a change already built)
- Inputs: {scope-contract.md v{n} + research-notes.md | brief: {path} | code: {repo}@{sha} | change: {repo} {base-sha}..{head-sha}}
<!-- technical:end -->

<!-- FUNCTIONAL LEVEL ONLY (skills/func-design/SKILL.md, "Abstraction rules"):
     WHAT the system does, WHEN, under WHICH business rules, with WHAT effect
     on data — never HOW it is coded. Allowed: component names, table.column
     names and code values (in §7, mapped to the business words the steps
     use), file names, numbered plain-language steps, decision tables,
     mermaid business flows. Not allowed: code, SQL, pseudocode, DDL, data
     types, indexes, hints, commit points, variable names, error codes.
     Mechanical floor: ses fdd-lint <file>.
     PLAIN WRITING (<root>/standards/writing.md): about the system, never
     about how this document was made — no research, task, scope contract,
     or stage names; no coined noun stacks; no slashes between words; short
     sentences. Mechanical floor: ses prose-lint <file>.
     Stakeholders get a rendered view (ses fdd-view): the business
     audience drops the handoff summary, every technical:start/end region,
     Appendix A, and sections that say only "None." — keep the markers
     around developer-only detail. -->

<!-- handoff:start -->
## Handoff summary
<!-- Written last, at this stage's gate, and updated in the same edit as any
     amendment. /tech-design reads ONLY this block unless it needs a section's
     detail. Every FR/BR/EX/TS/Q ID in the body appears here; max 40 lines —
     group IDs on one line where needed. Check: ses handoff check <file>. -->
- Contract version: {n | none (standalone or change request)}
- Purpose: {one line}
- Requirements: FR1 {…}; FR2 {…}
- Traceability: S1 → FR1, FR2 (attached mode; standalone: brief §… → FR…)
- Components: §5.1 {component} — {new | changed | context} — FR1
- Business rules: BR1 {…}; BR2 {…}
- Data: {entity — read | create | update, one line each} (§7)
- Interfaces: {direction — counterpart — content} (§8)
- Exceptions: EX1 {…}
- Scenarios: TS1 → FR1 (A1)
- Open questions: Q1 {…} | none
<!-- handoff:end -->

## In short

<!-- For the reader who stops here. Four to eight plain sentences: what
     changes (as-built: what the function does), who notices, when it
     happens, and what the reader must decide or check. No IDs, no table or
     column names, nothing about how this document was made. Write it last,
     from the finished body, and update it with every revision. -->

{Today, a purchase order waits for the weekly run before it goes to the
vendor. After this change, the nightly run sends each approved order on the
day that the buyer approves it. Buyers no longer send EDI orders by hand.
Orders for vendors that do not accept EDI go on the buyer's exception report,
as they do today.}

### Before and after this change

<!-- Forward and change modes — the stakeholders' main view of what the
     change does; change mode fills both columns from the code (before = base
     commit, after = head commit). Each row is concrete: "orders reach the
     vendor the same night", not "improved processing". As-built mode: delete
     this subsection. -->
| Aspect | Before | After this change |
|---|---|---|
| {how orders reach vendors} | {…} | {…} |

## 1. Purpose and business context

{The business problem, who benefits, and what changes for them — two
paragraphs at most, readable by someone who has not seen the brief.}

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

## 2. Scope

### 2.1 Functional requirements

<!-- WHAT the system must do, one testable statement per row. Attached mode:
     every in-scope S# of the contract is the source of at least one FR.
     Standalone forward: cite the brief section. As-built: cite Appendix A. -->
| # | Requirement (what the system must do) | Source |
|---|---|---|
| FR1 | {Send every approved purchase order to its vendor once, on the day it is approved} | {S1} |

### 2.2 Out of scope

<!-- Attached mode: the scope contract's N# items. State "None." when there
     are none. -->
{What a reader might expect in this design but it does not cover.}

## 3. Actors, triggers and schedule

| Actor / trigger | Type | When / frequency | Initiates |
|---|---|---|---|
| {Nightly batch schedule} | {scheduler} | {daily 02:00, after the receipts load} | {§5.1} |
| {Buyer} | {user} | {on demand} | {§5.2} |

## 4. Functional overview

### Process flow

<!-- Business-level: nodes are business actions and decisions ("Select
     approved orders", "Vendor accepts EDI?"), not code units. Group by actor
     or system where that helps. As-built: must match the traced flow;
     forward: built from the research call graph plus the proposed change. -->
```mermaid
flowchart TD
    T([trigger]) --> S1[business step]
    S1 --> D{decision?}
    D -- yes --> S2[business step]
    D -- no --> X[exception path — EX1]
```

{One paragraph that walks through the diagram.}

## 5. Component functional design

<!-- One subsection per component the function involves (package, procedure,
     script, program, job). Logic is numbered plain-language steps in business
     words: what the step reads or changes and the rule it applies — never
     loops, cursors, SQL, or variables. A step names its rule in a few words
     with the ID at the end ("Check that the vendor accepts EDI orders
     (BR1)"), and its failure path the same way (EX1); the words agree with
     §6 and §9. Table and column names and code values go in §7; with
     audience=technical a step may add the `table.column` in brackets after
     the business words. A 400-line procedure becomes 5–10 steps, each 20
     words at most. Litmus test: two developers could implement these steps
     differently and both satisfy them.
     Mark components shown only for context as "context — unchanged"; in
     change mode, mark each new or changed step "(new)" / "(changed)". -->

### 5.1 {Component name} — {new | changed | context — unchanged}

- Purpose: {one sentence}
- Invoked by / when: {actor or caller from §3}
<!-- technical:start -->
- Inputs:

  | Input | Business meaning | Mandatory | Valid values / default |
  |---|---|---|---|
  | {run date} | {the business day being processed} | {no} | {defaults to today} |

<!-- technical:end -->
- Processing logic:
  1. {Find every approved purchase order that the system has not sent to
     its vendor.}
  2. {Check that the vendor accepts EDI orders (BR1). If it does not, skip
     the order and put it on the buyer's exception report (EX1).}
  3. {(new) Write the other orders to the vendor file (§8). Mark each of
     them as sent.}
- Outputs and effects: {the records it creates or changes and what that
  means to the business, the files it produces, the notifications it sends}
- Exceptions: {EX1, …}
- Requirements met: {FR1, …}

### 5.2 {Component name}

## 6. Business rules and validations

<!-- The full statement of each rule lives here, once. A §5 step names the
     rule in a few words with its ID; those words must agree with this
     table. Multi-condition rules get a decision table below. -->
| # | Rule | Applies to | When violated |
|---|---|---|---|
| BR1 | {An order is sent only if its vendor is EDI-enabled} | {§5.1 step 2} | {order skipped, reported as EX1} |

Decision table — {rule ID}:

| {Condition A} | {Condition B} | Outcome |
|---|---|---|
| {yes} | {yes} | {…} |

## 7. Data

<!-- The business view of the data the function reads or changes and what it
     MEANS. A column appears only when it carries meaning a reader needs. No
     DDL, data types, lengths as types, indexes, or storage — a business limit
     is stated in words ("up to 30 characters"). This is where the business
     words of §5 ("approved", "sent") map to tables, columns, and code
     values. -->

### 7.1 Data elements

| Entity (table / file / message) | Attribute | Business meaning | Usage | New / existing |
|---|---|---|---|---|
| {ORDHEAD} | {EDI_SENT_IND} | {whether the order has been sent to the vendor} | {read, update} | {existing} |

### 7.2 Status and code values

| Attribute | Value | Meaning | Set by |
|---|---|---|---|
| {ORDHEAD.STATUS} | {A} | {approved} | {buyer approval, outside this function} |
| {ORDHEAD.EDI_SENT_IND} | {N, Y} | {not sent to the vendor yet; sent} | {§5.1 step 3 sets Y} |

## 8. Interfaces

| Direction | Counterpart | What is exchanged (business content) | File / message | Frequency |
|---|---|---|---|---|
| {outbound} | {vendor EDI gateway} | {approved order lines} | {PO_{yyyymmdd}.dat} | {daily} |

{Field-level content, when the audience needs it: field → business meaning →
source attribute. A layout with positions and types is the counterpart's
contract — cite it rather than restate it.}

## 9. Exceptions and error handling

| # | Situation | System behaviour | Who is informed, how | Business recovery |
|---|---|---|---|---|
| EX1 | {vendor not EDI-enabled} | {order skipped, run continues} | {buyer, exception report} | {enable the vendor or send manually; the next run picks the order up} |

## 10. Reports, screens and notifications

{What users see or receive — or "None", stated explicitly.}

## 11. Security and access

{Who may run, see, or approve what; segregation of duties; sensitive data
handled — in business roles, not grants.}

## 12. Operational expectations

<!-- Business view, one line each; "None" stated, not implied. -->
- Volumes: {…}
- Timing window and service level: {…}
- Rerun behaviour: {what a rerun does to records already processed}
- Audit and retention: {…}

## 13. Dependencies and open questions

Dependencies: {other changes, data, or teams this design relies on — or "None".}

| # | Question | Owner | Status |
|---|---|---|---|
| Q1 | {…} | {…} | {open | answered: … | deferred by {user}, {date}: …} |

## 14. Functional test scenarios

<!-- Business scenarios a UAT tester can run. Every FR# appears at least once;
     attached mode: every acceptance criterion A# of the contract too. -->
| # | Scenario | Given | When | Then | Covers |
|---|---|---|---|---|---|
| TS1 | {approved order, EDI vendor} | {…} | {nightly run} | {order in the file, marked sent} | {FR1, A1} |

## 15. Sign-off

| Role | Name | Date | Decision |
|---|---|---|---|

<!-- technical:start -->
## Appendix A. Source references

<!-- The fact table: every statement about EXISTING behaviour (all of an
     as-built or change FDD) → its source. Change mode cites the head commit
     for "after" claims and the base commit for "before" claims. The
     doc-fact-checker verifies each row; a claim about existing behaviour
     with no row is a finding. Proposed behaviour traces to §2.1 instead.
     Dropped from the business view. -->
| Section | Claim | Source |
|---|---|---|
| {§5.1 step 1} | {orders are selected by status and sent indicator} | {repo:path:line} |
<!-- technical:end -->
