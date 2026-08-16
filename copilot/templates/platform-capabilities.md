# Platform Capabilities — {ESTATE / TEAM NAME}

- Profiled: {date} by /estate-profile
- Repos scanned: {repo-a, repo-b, …} (the recorded analysis scope)
- Confirmed by: {user} on {date} — sections 2–8 are USER-OWNED, not inferred
- Refresh when: older than ~6 months, a new system enters the estate, or a
  platform decision changes a status below

> What the estate can actually build with. Lives at `<estate-root>` as
> `.platform-capabilities.md`, the estate-level sibling of the repo-level
> `.conventions.md` and `.domain-glossary.md` (core/repo-resolution.md).
> Read by /architecture and /tech-design BEFORE any integration is proposed.
>
> **The closed-world rule.** A mechanism that is not listed below with status
> `in-use` or `available` MUST NOT appear in a proposed design. It may appear
> only in the Alternatives section of the document, marked
> `REQUIRES NEW PLATFORM CAPABILITY`, carrying the approval path and lead time
> from §7. Designing on a capability the estate does not have is the failure
> this file exists to prevent.
>
> Rules:
>
> - `in-use` rows carry a source reference (`<repo>:<file>:<line>` or a run
>   output) — presence is a checkable fact (decision-protocol §1).
> - Every other status is a USER STATEMENT with a date. A scan can prove
>   presence; it can never prove permission. Never upgrade a status from
>   evidence alone.
> - Absence is a claim too: an `absent` row records the search that found
>   nothing, exactly like /understand §3.
> - Hand-edits by the user always win; /estate-profile merges, never
>   overwrites.
> - Never copy credentials, connect strings, or secret values into this file —
>   name the secret store, not the secret.

## 1. Capability inventory

<!-- The table every design is checked against. One row per mechanism, not per
     project. Status vocabulary:
       in-use            running in production today, with evidence
       available         exists and is sanctioned for NEW use
       deprecated        present, but no new use permitted
       requires-approval obtainable via §7, with a lead time
       forbidden         ruled out by policy
       absent            not present in the estate (record the search)
     Only in-use and available may carry a design. -->

| Capability | Mechanism / product | Status | Evidence / who said so | Notes & limits |
|---|---|---|---|---|
| File transfer | {SFTP to feedhost01} | in-use | {repo-a:bin/run_extract.ksh:23} | {batch window 02:00–04:00} |
| Scheduling | {Control-M} | in-use | {repo-a:jobs/daily.jil:1} | {new job needs ops ticket, 2 days} |
| DB-to-DB | {Oracle DB link} | deprecated | {user, 2026-08-16} | {DBA froze new links; use extract files} |
| Messaging / events | {none} | absent | {scan: 0 hits, 4 repos, messaging pattern} | {no broker in the estate} |
| Synchronous API | {…} | {…} | {…} | {…} |
| ETL tooling | {…} | {…} | {…} | {…} |
| Object storage | {…} | {…} | {…} | {…} |
| Container runtime | {…} | {…} | {…} | {…} |
| Notification | {…} | {…} | {…} | {…} |
| Secrets store | {…} | {…} | {…} | {…} |
| Monitoring / alerting | {…} | {…} | {…} | {…} |

## 2. Systems & ownership

<!-- The boxes a high-level architecture is allowed to draw. "Can we change
     it?" is the single most design-shaping column: a system you can only
     integrate around produces a different architecture than one you own. -->

| System | Authoritative for | Owning team | Can we change it? | How we reach it today |
|---|---|---|---|---|
| {ORDERS} | {purchase orders, approval state} | {Procurement IT} | no — integrate around | {nightly extract, repo-a:…} |

## 3. Reference integration patterns

<!-- The highest-value section: the patterns to COPY. A design that reuses a
     proven pattern needs no platform argument; one that invents a pattern
     does. Each row points at a working example. -->

| Pattern | When to use it | Working example | Notes |
|---|---|---|---|
| {Nightly extract → SFTP → loader} | {system-to-system bulk data, T+1 acceptable} | {repo-a:bin/run_balance_extract.ksh} | {the house default for batch feeds} |

## 4. Runtime & hosting

| Aspect | Reality | Source |
|---|---|---|
| Hosts / platform | {on-prem AIX batch hosts; no container platform} | {user, date} |
| Database(s) + version | {Oracle 19c} | {…} |
| Language runtimes available on the servers | {Python 3.6 (system), KSH 93, no pip network access} | {…} |
| New schema / instance obtainable? | {yes, DBA request, ~2 weeks} | {…} |
| Outbound network from batch hosts | {none — internal only} | {…} |

## 5. Environments

| Environment | Exists | Reachable from here | Prod-like data | Notes |
|---|---|---|---|---|
| dev | {…} | {…} | {…} | {…} |
| test / UAT | {…} | {…} | {…} | {…} |
| prod | {…} | no | — | {…} |

## 6. Constraints & house NFRs

<!-- Org policy, not per-project choices. These bound every design. -->

- Batch windows: {…}
- Data retention: {…}
- PII / sensitive data handling: {…}
- Audit requirements: {…}
- Availability / SLA expectations: {…}
- Security rules that rule mechanisms out: {…}

## 7. Procurement & approval path

<!-- Turns "we can't" into "we can, and here is the cost" — which is a
     legitimate architectural trade-off, where a silent assumption is not. -->

| New capability type | Approver | Typical lead time | Notes |
|---|---|---|---|
| {new middleware / broker} | {architecture board} | {2 quarters} | {needs a business case} |
| {new server / host} | {infra} | {6 weeks} | {…} |
| {new third-party library} | {security review} | {2 weeks} | {internal mirror only} |

## 8. Explicitly ruled out

<!-- The negative list — more useful than the positive one, because it is what
     stops a plausible-but-unbuildable design. Each entry says WHO ruled it
     out and when, so it can be revisited rather than treated as physics. -->

| Ruled out | Reason | Stated by | Date |
|---|---|---|---|
| {Kafka / any new broker} | {no broker operated; would need board approval} | {user} | {…} |
| {public cloud} | {data residency policy} | {…} | {…} |

## 9. Open questions

| # | Question | Blocks what | Who can answer |
|---|---|---|---|

## 10. Confirmation log

| Date | Sections confirmed | By | Changes made |
|---|---|---|---|
