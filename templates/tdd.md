# Technical Design Document — {TASK_ID}: {TITLE}

- Status: draft | user-approved ({date})
- Inputs: scope-contract.md v{n}, research-notes.md
- Author: Claude, reviewed by {user}

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
- Verification: A1 → {unit|integration|regression}; G2 → {…} (§7)
- Operational: {deploy/runtime one-liner} (§8)
- Top risks: {one line each} (§11)
<!-- handoff:end -->

## 1. Overview

{What is being built/changed and why — one or two paragraphs, understandable by
someone who has not read the brief.}

Business terms relied on (see `<work-repo>/.domain-glossary.md`):
{purchase order, approved, …} — the glossary entry is authoritative; this
document does not re-define terms.

## 2. Requirements traceability

<!-- Every in-scope item from the scope contract must map to at least one design section.
     With an approved fdd.md, each of its FR# items gets a row too. -->
| Scope item | Design section(s) |
|---|---|
| S1 | §4.1, §5 |

## 3. Current state

{Condensed from research-notes.md, with source references retained.}

### As-is flow

<!-- Must match the research call graph — the fact-checker verifies diagrams
     against the actual call order. Keep source refs under the diagram. -->
```mermaid
flowchart TD
    {trigger/schedule} --> {entry point}
    {entry point} --> {component} --> {data object / file}
```

{One paragraph walking the diagram; source: research-notes.md §call graph.}

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
- Source references for claims about existing behaviour: {file:line}

### 4.2 {Component / object 2}

## 5. Data model changes

| Object | DDL summary | Migration / backfill | Rollback |
|---|---|---|---|

## 6. Interface impact

{Callers affected, contract changes, backward compatibility. "None" must be
justified with the call-graph evidence from research — evidence covering every
repo in the analysis scope, not only the repo being changed.}

| Repo | Caller | Impact | Changes here? | How it keeps working |
|---|---|---|---|---|
| {repo-b} | {src/py/loader.py:88} | {new column in extract} | no | {ignores unknown columns — verified} |

## 7. Verification approach

<!-- Every acceptance criterion from the scope contract appears here. A
     criterion with no viable test blocks TDD approval — fix the design or
     renegotiate the criterion. /grill adds G# rows (grill-log scenario #) for
     the edge cases it closes; they get tests like any A#. The detailed test
     plan lands in impl-doc §3. -->
| Criterion (A#, or G# from /grill) | Test type (unit / integration / regression) | Sketch |
|---|---|---|
| A1 | {…} | {…} |

## 8. Operational impact

<!-- Batch reality check. "None" must be stated per line, not implied. -->
- Schedule / trigger changes: {…}
- Restartability: {how the changed job behaves on rerun after failure}
- File handoffs: {new/changed files, consumers informed?}
- Logging & monitoring: {new log lines, alerts, what ops should watch}
- Run duration / volumes: {expected change, basis}

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

{Restate the contract's exclusions that readers might otherwise expect here.}
