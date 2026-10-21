# Domain Glossary — {workspace}

> Global business terms: what a term means in EVERY repo of this workspace.
> One file, `<workspace-root>/work/domain-glossary.md`, beside the task
> workspaces and, like them, never in git. Read by
> intake/research/func-design/tech-design/grill/understand BEFORE a term is
> investigated or asked. Rules:
>
> - Be selective. A term goes in only if its meaning holds in every repo —
>   checked across all of them (`ses search`), never assumed from one. A
>   meaning that varies by repo ("upload" loads one table in repo1, another in
>   repo2) stays OUT: the task that needs it defines it per repo in its
>   research notes and design documents, cited `<repo>:<path>:<line>`.
> - Each entry is one functional statement — what the term means and where it
>   lives — which TDDs and FDDs copy verbatim. Facts in it carry a source
>   reference: entries are checkable (decision-protocol §1).
> - A repo found using a listed term differently means the entry is not
>   global after all: raise it with the user, who corrects or removes it.
> - `Resolved` records who confirmed the meaning and when; anything not yet
>   confirmed is `unconfirmed`.
> - Hand-edits by the user always win; skills merge, never overwrite.
> - A brief using a term differently from its entry is ALWAYS an open question
>   (the brief may be wrong, or this file stale) — never silently pick a side.

## {Order}

- Meaning: {Order means purchase order; it exists in ORDHEAD (header) and ORDSKU (detail).}
- Source: {schema-repo:ddl/ordhead.sql:1, schema-repo:ddl/ordsku.sql:1}
- Aliases: {PO, purchase order}
- Resolved: {task-id (date, user-confirmed | from-code | unconfirmed)}
