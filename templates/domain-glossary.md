# Domain Glossary — {repo}

> Business terms mapped to what they ARE in this system. Lives at the work
> repo root as `.domain-glossary.md`, sibling to `.conventions.md`. Consulted
> by intake/research/grill/tech-design BEFORE a term is investigated or asked;
> appended to by whichever stage resolves a term. Rules:
>
> - Mechanical claims (tables, states, code paths) carry a source reference —
>   glossary entries are checkable facts (decision-protocol §1).
> - Business-semantic lines record who confirmed them and when. Entries seeded
>   by /repo-profile without confirmation are marked `seeded — unconfirmed`.
> - Hand-edits by the user always win; skills merge, never overwrite.
> - A brief using a term differently from its entry is ALWAYS an open question
>   (the brief may be wrong, or this file stale) — never silently pick a side.

## {term, e.g. purchase order}

- System meaning: {row in PO_HEADER (+PO_LINES), keyed by po_id (src/sql/po_header.sql:3)}
- States: {PO_HEADER.status ∈ DRAFT|SUBMITTED|APPROVED|CANCELLED (src/sql/po_header.sql:14)}
- Key semantics: {"approved" mechanically = pkg_po.approve_po sets status +
  approval_dt; two-level rule >50k EUR in pkg_po.check_approval_limit (pkg_po.pkb:212)}
- Entry points: {pkg_po.approve_po; bin/po_batch_approve.ksh}
- Aliases / traps: {PO; "order" means THIS in procurement briefs but
  SALES_ORDER in fulfillment briefs}
- Resolved: {task-id (date, user-confirmed | from-code | seeded — unconfirmed)}
