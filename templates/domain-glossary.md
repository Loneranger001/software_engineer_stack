# Domain Glossary — {workspace}

> Business terms mapped to what they ARE in each repo of this workspace. One
> file for every repo and task: `<workspace-root>/work/domain-glossary.md`,
> beside the task workspaces and, like them, never in git. Consulted by
> intake/research/func-design/tech-design/grill/understand BEFORE a term is
> investigated or asked; appended to by whichever stage resolves a term. Rules:
>
> - Mechanical claims (tables, states, code paths) carry a source reference,
>   `<repo>:<path>:<line>` — glossary entries are checkable facts
>   (decision-protocol §1).
> - A term that means different things in two repos keeps ONE entry with a
>   `System meaning (<repo>)` line per repo; the difference is a finding to
>   raise, never smoothed over.
> - Business-semantic lines record who confirmed them and when; anything not
>   yet confirmed is marked `unconfirmed`.
> - Hand-edits by the user always win; skills merge, never overwrite.
> - A brief using a term differently from its entry is ALWAYS an open question
>   (the brief may be wrong, or this file stale) — never silently pick a side.

## {term, e.g. purchase order}

- Meaning: {one plain-language line a business reader understands, no table or code names — TDDs and FDDs copy it verbatim} — `Meaning (<repo>)` per repo only where the business meaning itself differs
- System meaning ({repo}): {row in PO_HEADER (+PO_LINES), keyed by po_id (procurement:src/sql/po_header.sql:3)} — one line per repo where it differs
- States: {PO_HEADER.status ∈ DRAFT|SUBMITTED|APPROVED|CANCELLED (procurement:src/sql/po_header.sql:14)}
- Key semantics: {"approved" mechanically = pkg_po.approve_po sets status +
  approval_dt; two-level rule >50k EUR in pkg_po.check_approval_limit (procurement:pkg_po.pkb:212)}
- Entry points: {pkg_po.approve_po; bin/po_batch_approve.ksh}
- Aliases / traps: {PO; "order" means THIS in procurement briefs but
  SALES_ORDER in fulfillment briefs}
- Resolved: {task-id (date, user-confirmed | from-code | unconfirmed)}
