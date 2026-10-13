---
name: func-design
description: Produce a functional design document (FDD) - what the system does, when, and under which business rules, with each component's logic as numbered plain-language steps and data named at table/column level, but no code, SQL, pseudocode, or DDL. Works forward (a proposed change, from an approved scope contract or a brief) or as-built (existing functionality, verified against the code); fact-checked, linted for code-level content, and user-approved. Use when a functional design, functional specification, FDD, or business-readable design of a package, job, or interface is needed, before or alongside the technical design.
argument-hint: "[task-id] | <brief path or component> [as-built]"
---

# /func-design — functional design document

> Path note: `${CLAUDE_PLUGIN_ROOT}` is this framework's root — the ancestor
> directory of this file containing `plugin.json`/`skills/`. Claude Code resolves
> it automatically; other harnesses resolve it from this file's location.

Produce `<ws>/fdd.md` and get it user-approved. The FDD is the contract for
WHAT the solution does, readable by the business; the TDD says HOW. The
defining rule is the abstraction level — see **Abstraction rules** below,
which govern every section.

Two modes, same template (`${CLAUDE_PLUGIN_ROOT}/templates/fdd.md`):
- **forward** — a proposed change: requirements come from the scope contract
  or a brief; existing behaviour it relies on is still read from the code.
- **as-built** — existing functionality described at functional level: every
  statement is a claim about the code and is verified like /document.

## 0. Preamble

1. Load applicable lessons: `${CLAUDE_PLUGIN_ROOT}/scripts/lessons.sh func-design` — it prints only
   the matching entries; don't read lessons.md whole.
2. Decide where it runs:
   - **Attached** — a task-id of an existing full-lifecycle task
     (`status.py get <ws> pipeline` is `full`; `<ws>` =
     `<workspace-root>/work/<id>`): forward mode. Gate:
     `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/status.py require <ws> research=done`
     — non-zero exit = stop. Take `<work-repo>` from `status.py get <ws> work-repo`
     (`${CLAUDE_PLUGIN_ROOT}/core/repo-resolution.md`). Read
     scope-contract.md fully — every in-scope S# must become at least one
     FR#, every acceptance criterion A# a scenario. For research, read its
     handoff summary (`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/handoff.py show <ws>/research-notes.md`)
     and open sections when designing the component they concern. If
     `tech-design` is already approved, the TDD is an input too and the FDD
     must agree with it — a disagreement goes to the user, never silently
     resolved in either document. No stage is added to the task; progress is
     recorded in the `fdd` field (§3).
   - **Standalone** — anything else (a brief, or a component to describe
     as-built). Resolve `<work-repo>`, `<workspace-root>`, and the
     `<repo-set>` per `${CLAUDE_PLUGIN_ROOT}/core/repo-resolution.md`
     (enumerate with `${CLAUDE_PLUGIN_ROOT}/scripts/list-repos.sh <repos-folder>`
     and confirm the list with the user — actors and interfaces are searched
     across all of them), then create the workspace:
     `${CLAUDE_PLUGIN_ROOT}/scripts/new-task.sh <task-id> auto func-design <work-repo> <repo-set>`
     (or resume from `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/status.py show <ws>`).
     Record the mode and what it starts from:
     `status.py field <ws> fdd-mode <forward|as-built>` and
     `status.py field <ws> source "<brief path | component(s)>"`.
3. Agree the scope with the user in two sentences — which function or
   components, which aspects, intended audience — and record it
   (`status.py field <ws> doc-scope "<the two sentences>"`). Attached mode
   inherits the contract's scope instead.
4. Read `<work-repo>/.domain-glossary.md` (business terms are referenced, not
   re-defined) and the rules files `${CLAUDE_PLUGIN_ROOT}/scripts/repo-rules.sh <work-repo>`
   lists. If they — or the user, with a client-mandated FDD template —
   prescribe a format, map the content onto it and record the choice
   (`status.py field <ws> doc-format "..."`); the abstraction rules still
   apply. If that format requires content the lint flags (a data-type column,
   say), record the kinds (`status.py field <ws> fdd-lint-allow "DATATYPE"`)
   and pass them as `--allow` — never otherwise.
5. Unknowns follow `${CLAUDE_PLUGIN_ROOT}/core/decision-protocol.md`.
   Existing behaviour is checked in the code, never estimated. A business rule
   the brief or contract does not settle is the user's call — it becomes a
   Q# and is asked at the stage boundary (immediately if it blocks the
   design), never invented. Only narrow presentation calls qualify for
   proceed-and-log to ASSUMPTIONS.md.

## Abstraction rules

Functional = what happens, when, under which rule, with what effect on data.
Technical = how it is coded. The FDD holds only the first.

| Belongs in the FDD | Belongs in the TDD (or nowhere) |
|---|---|
| Component names (package, procedure, script, job) as identifiers | Code, SQL, PL/SQL blocks, shell or Python snippets |
| Processing logic as numbered plain-language steps; decision tables for multi-condition rules | Pseudocode mirroring code: loops, cursors, bulk binds, assignments, variable names |
| `table.column` names where they pin down business meaning, with code values and what they mean | DDL, data types, precision, indexes, partitions, hints, sequences |
| Business limits in words ("up to 30 characters", "2 decimal places") | `VARCHAR2(30)`, `NUMBER(12,2)` |
| Parameters by name, business meaning, valid values | Parameter types and defaults written as code |
| What a failure means to the business, who is told, how it is recovered | Exception-handler mechanics, `ORA-` codes, log-table internals |
| Rerun behaviour as a business effect ("already-sent orders are not resent") | Commit points and how restartability is implemented |
| Interface content by business meaning, file name pattern, frequency | Transport mechanics; record offsets and types (cite the counterpart's contract instead) |

Litmus test for every sentence: a business analyst or UAT tester can read
it, and two developers could implement it differently and both satisfy it.
A step that only makes sense to someone reading the code is lifted to its
business effect or moved to the TDD.

- ✗ `FOR r IN c_po LOOP IF r.status = 'A' …` — code.
- ✗ "Open cursor c_po on ORDHEAD, bulk-collect into the order table, loop" — code in prose.
- ✓ "Select every purchase order that is approved (`ORDHEAD.STATUS` = 'A')
  and not yet sent to the vendor (`ORDHEAD.EDI_SENT_IND` = 'N')."

As-built mode reads the code to learn the logic; translating it to this level
is the job — summarise, don't transcribe. A 400-line procedure is 5–10 steps.

`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/fdd_lint.py <ws>/fdd.md` flags code-level content
mechanically (non-mermaid code blocks, SQL/PL/SQL/shell/Python constructs,
data types). It is a floor, not the judgment: a finding is fixed by lifting
the content to the functional level, never by rewording around the pattern,
and a clean lint does not excuse a step that fails the litmus test.

## 1. Analyze

1. Requirements:
   - forward, attached — every in-scope S# → one or more FR#, each citing its
     S#. An FR# with no S# is out of scope: drop it, or stop and ask for a
     contract version bump. Out-of-scope findings go to PARKED.md.
   - forward, standalone — extract FR# from the brief, each citing its
     section; anything ambiguous becomes a Q#.
   - as-built — read the target code completely and trace one real flow
     end-to-end, error paths included. If /understand left an interface map
     for it (`<workspace-root>/work/*/interface-map.md`), start from it — check its recorded
     commit for staleness, then deepen rather than re-derive.
2. Existing behaviour, in either mode, comes from the code, not the brief or
   folklore: entry points, callers and schedules (§3 actors), data read and
   changed (§7), outputs and their consumers (§8), error paths (§9). Search
   every repo in `<repo-set>` with
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/xsearch.py --ws <ws> -- <patterns>` (counts first) and
   keep its per-repo rows in evidence — "no other consumer" needs the search
   that found none. Attached mode reuses research's rows while a repo's sha
   is unchanged.
3. Confirm every existing table, column, and code value the FDD will name
   against the schema — DDL in the repo, or the live data dictionary where
   `$SES_DB_CONN` is reachable (read-only queries, output captured with
   `${CLAUDE_PLUGIN_ROOT}/scripts/capture.sh` into `evidence/`). Proposed
   ones are marked `new` in §7.1 and must not collide with an existing name.
4. Build Appendix A (claim → source) as you go — it is the fact-checker's
   input and the resume point.
5. Standalone: `status.py set <ws> analyze=done`.

## 2. Draft

1. Copy `${CLAUDE_PLUGIN_ROOT}/templates/fdd.md` → `<ws>/fdd.md`.
2. Fill §2.1 FIRST. Every FR# must land in at least one §5 step and one §14
   scenario; attached mode, every A# appears in §14 too. An FR# with no
   natural home in §5 means the design is incomplete.
3. §4 flow at business level — the traced flow (as-built) or the research
   call graph plus the proposed change (forward), never from memory.
4. §5: one subsection per component the function involves; unchanged ones
   only where a reader needs them for context, marked so. Steps reference
   BR#, EX#, and `table.column` — every rule stated once in §6, every
   failure path once in §9 with its business recovery.
5. Write for the stated audience. No section is dropped: "None" is stated,
   with the reason where it is not obvious.
6. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/fdd_lint.py [--allow <kinds>] <ws>/fdd.md`
   (kinds from `status.py get <ws> fdd-lint-allow`, if recorded) and fix
   every finding per the abstraction rules.
7. Standalone: `status.py set <ws> draft=done`.

## 3. Quality gates

1. Self-check with `${CLAUDE_PLUGIN_ROOT}/checklists/func-design.md`.
2. Run the fact-check procedure in
   `${CLAUDE_PLUGIN_ROOT}/agents/doc-fact-checker.md` on fdd.md — as a
   subagent where the harness supports it, otherwise as a separate fresh pass
   in its report format. Resolve every finding; fixes keep the functional
   level (a WRONG step is corrected in plain language, not replaced by the
   code it summarises). Standalone: `status.py set <ws> fact-check=done`.
3. Write the **handoff summary** block now — after the fact-check fixes —
   then run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/handoff.py check <ws>/fdd.md` and the lint
   again; both must pass.
4. Present the FDD for approval, starting from the summary: requirements and
   traceability, business rules, exceptions, open Q# items, plus open
   ASSUMPTIONS.md entries for ratification (decision-protocol §4). Approval
   with a Q# still open needs the user to defer it explicitly, recorded in
   its §13 status. Iterate until approved — each revision updates the summary
   in the same edit and re-runs the handoff check and lint. Record approval +
   date in the FDD header.
5. Record:
   - Attached: `status.py field <ws> fdd "approved <date>" --log "FDD approved"`.
     While `tech-design` is pending:
     `status.py next <ws> "Run /tech-design — the TDD realises the approved FDD."`
   - Standalone (gate first: `status.py require <ws> fact-check=done`):
     `status.py set <ws> approval=approved --next "Deliver the FDD (/func-design §4)."`

## 4. Deliver (standalone)

Attached mode skips this: the FDD ships in the task's /deliver package.

1. Ask which output formats are needed unless `status.py get <ws> formats`
   answers it, and record them (`status.py field <ws> formats "<docx,pdf,...>"`).
   Convert via `${CLAUDE_PLUGIN_ROOT}/scripts/md2docx.sh | md2pdf.sh | md2confluence.sh`
   into `<ws>/deliverables/`; verify each file is non-empty.
2. Present the FDD and where it is; list deferred Q# items so the user can
   close them.
3. `status.py set <ws> deliver=done`.

## Changes after approval

Never edit an approved FDD silently — a change needs re-approval and a note
in the header. Attached mode: when /tech-design, /grill, or /implement finds
the FDD wrong or incomplete, the FDD is amended and re-approved first; the TDD
never quietly departs from it.

## Fault tolerance

Write incrementally. On resume, diff §2.1 against §5 and §14 to find FR#
without a home, and Appendix A against §5 to find unsourced steps; standalone
stage state comes from `status.py show <ws>`.
