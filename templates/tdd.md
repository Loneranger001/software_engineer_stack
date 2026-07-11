# Technical Design Document — {TASK_ID}: {TITLE}

- Status: draft | user-approved ({date})
- Inputs: scope-contract.md v{n}, research-notes.md
- Author: Claude, reviewed by {user}

## 1. Overview

{What is being built/changed and why — one or two paragraphs, understandable by
someone who has not read the brief.}

## 2. Requirements traceability

<!-- Every in-scope item from the scope contract must map to at least one design section. -->
| Scope item | Design section(s) |
|---|---|
| S1 | §4.1, §5 |

## 3. Current state

{Condensed from research-notes.md, with source references retained.}

## 4. Proposed design

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
justified with the call-graph evidence from research.}

## 7. Non-functional considerations

- Performance: {expected volumes, plans, indexes}
- Security: {grants, injection surfaces, secrets}
- Operability: {logging, monitoring, restartability of batch jobs}

## 8. Alternatives considered

| Alternative | Why rejected |
|---|---|

## 9. Risks & mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|

## 10. Out of scope

{Restate the contract's exclusions that readers might otherwise expect here.}
