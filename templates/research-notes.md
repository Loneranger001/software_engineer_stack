# Research Notes — {TASK_ID}: {TITLE}

> Every finding MUST carry a source reference: `file:line`, object name + query used,
> document section, or URL. A finding without a source is a guess — label it as such.

- Scope contract: ./scope-contract.md (version {n})
- Researched by: Claude on {date}

## Summary of findings

{3–8 bullets: the load-bearing facts that will shape the design.}

## Current-state analysis

### Affected code

| Repo | Object / file | Language | Role today | Key facts | Source |
|---|---|---|---|---|---|
| {repo-a} | {src/plsql/pkg_x.pks} | PL/SQL | {…} | {…} | {repo-a:pkg_x.pks:42-88} |

### Cross-repo search record

<!-- Every repo in the analysis scope, including those with no hits — a repo -->
<!-- that was never searched and a repo with no callers look identical in a -->
<!-- summary, and only this table tells them apart. -->
| Repo | Search command | Result |
|---|---|---|
| {repo-a} | {grep -rn "PKG_X" .} | {4 references — see call graph} |
| {repo-b} | {grep -rn "PKG_X" .} | {searched, no references found} |

### Data model

| Table / view | Relevant columns | Volumes / constraints | Source |
|---|---|---|---|

### Call graph / dependencies

{Who calls the affected objects, what they call. Include the queries or grep
commands used to establish this, so the result is reproducible.}

### Repo conventions that apply

{Relevant entries from each changed repo's <repo>/.conventions.md / standards/, e.g. naming, error handling,
logging, deployment layout.}

## External research

| Topic | Finding | Source (URL / doc) |
|---|---|---|

## Options considered

| Option | Sketch | Pros | Cons |
|---|---|---|---|
| 1 | {…} | {…} | {…} |

## Risks discovered

| Risk | Impact | Mitigation idea |
|---|---|---|

## Out-of-scope findings

{Logged to PARKED.md — list the PARKED entry IDs here for cross-reference.}

## Open questions for the user

| # | Question | Blocking? |
|---|---|---|
