# Research Notes — {TASK_ID}: {TITLE}

> Every finding MUST carry a source reference: `file:line`, object name + query used,
> document section, or URL. A finding without a source is a guess — label it as such.

- Scope contract: ./scope-contract.md (version {n})
- Researched by: Claude on {date}

<!-- handoff:start -->
## Handoff summary
<!-- Written last, at this stage's gate, and updated in the same edit as any
     amendment. Later stages read ONLY this block unless they need a section's
     detail. One line per ID; max 40 lines. Check: ses handoff check <file>. -->
- Contract version: {n}
- Recommended option: {one line} (decision lands in /tech-design)
- Affected: {repo}:{path} — {role, one line}
- Callers: {repo-a}: {n} ({where}); {repo-b}: none (searched, command in §Cross-repo search record)
- Data: {table} — {volume / key constraint}
- Repo rules binding this change: {repo}: {file — the rule}
- Repo-specific terms: {Upload: repo1 → TABLE1, repo2 → TABLE2; the brief means repo1's} | none
- Risks: {one line each}
- Blocking questions: {none | Q# one line}
- Evidence: evidence/research-*.txt
<!-- handoff:end -->

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
<!-- summary, and only this table tells them apart. Rows come from -->
<!-- ses search; later stages reuse a row while its sha is unchanged. -->
| Repo | Ref@sha | Search command | Result |
|---|---|---|---|
| {repo-a} | {origin/main@1a2b3c4} | {git -C … grep -c -I -E -e PKG_X origin/main --} | {4 match(es) in 2 file(s) — see call graph} |
| {repo-b} | {origin/main@5d6e7f8} | {git -C … grep -c -I -E -e PKG_X origin/main --} | {searched, no references found} |

### Data model

| Table / view | Relevant columns | Volumes / constraints | Source |
|---|---|---|---|

### Call graph / dependencies

{Who calls the affected objects, what they call. Include the queries or grep
commands used to establish this, so the result is reproducible.}

### Business terms

<!-- Every term intake marked as a research target, grounded in every repo. -->
<!-- Same meaning in every repo → `global`: one row, also written to the -->
<!-- glossary. Meaning differs by repo → one row per repo; it stays out of the -->
<!-- glossary, and TDD/FDD §1 define it from here for the repo they concern. -->
| Term | Scope | Meaning | Source |
|---|---|---|---|
| {Order} | global | {Order means purchase order; it exists in ORDHEAD (header) and ORDSKU (detail).} | {schema-repo:ddl/ordhead.sql:1} |
| {Upload} | {repo1} | {loads the day's file into TABLE1} | {repo1:bin/upload.ksh:12} |
| {Upload} | {repo2} | {loads the day's file into TABLE2} | {repo2:src/upload.py:40} |

### Repo rules that apply

{Rules files per repo (ses repo-rules output) and the relevant rules from them / standards/, e.g. naming, error handling,
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
