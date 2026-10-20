---
name: func-design
description: Produce a functional design document (FDD) - what the system does, when, and under which business rules, with each component's logic as numbered plain-language steps and data named at table/column level, but no code, SQL, pseudocode, or DDL. Works forward (a proposed change, from an approved scope contract or a brief), as-built (existing functionality), or for a change already implemented (before vs after, from the delivered diff); fact-checked against the code, linted for code-level content, user-approved, and rendered for a business or technical audience. Use when a functional design, functional specification, FDD, or business-readable description of a package, job, interface, or change is needed - including after the change was built - to discuss with non-technical stakeholders.
argument-hint: "<task-id> | brief <path> | as-built <component> | change <repo> <base>..<head>   [audience=business|technical]"
---

# /func-design — functional design document

> Framework files: `<root>` is what `ses root` prints — run it once. Every
> framework script runs as `ses <command>` (`ses help` lists them). If `ses`
> is not on PATH, use `python3 <skill-dir>/../../bin/ses` in its place —
> `<skill-dir>` is the folder this SKILL.md was loaded from — here and for
> every `ses` below. If neither runs, stop and ask the user (README →
> Install); never guess another path.

Produce `<ws>/fdd.md`, get it user-approved, and render it for its audience.
The FDD tells stakeholders WHAT the solution does, in their language; the TDD
says HOW. It is optional in every lifecycle — nothing gates on it. The
defining rule is the abstraction level — see **Abstraction rules** below.

## Invocation

| You type | Mode | Runs |
|---|---|---|
| `/func-design PROJ-123` | forward, or change once implemented | attached to that task |
| `/func-design brief docs/brief.md` | forward — a proposed change | standalone |
| `/func-design as-built ORDER_EDI_SQL` | as-built — existing functionality | standalone |
| `/func-design change repo-a main..feature/PROJ-123` | change — what a built change did | standalone |

Append `audience=technical` to keep developer detail in the rendered
document; the default `audience=business` is for non-technical stakeholders.
With no arguments, show this table and ask which case applies.

One template for all modes (`<root>/templates/fdd.md`):
- **forward** — requirements come from the scope contract or a brief;
  existing behaviour it relies on is still read from the code.
- **as-built** — a component as it stands, every statement verified against
  the code like /document.
- **change** — a change already built, described as before vs after. The
  delivered code is the source of truth for what it does; the contract or
  TDD, where they exist, are context. Where the code departs from them, tell
  the user — whether the code or the plan is right is their call (a Q#),
  never smoothed over in the FDD.

## 0. Preamble

1. Load applicable lessons: `ses lessons func-design` — it prints only
   the matching entries; don't read the lesson files whole.
2. Workspace and gate (`<ws>` = `<workspace-root>/work/<id>`):
   - **Attached** (a task-id): take `<work-repo>` from `ses status get <ws> work-repo`
     (`<root>/core/repo-resolution.md`) and the mode from the
     task's pipeline (`ses status get <ws> pipeline`) and progress:
     - `full`, `ses status get <ws> implement` not done — **forward**. Gate:
       `ses status require <ws> research=done`.
       Read scope-contract.md fully (every in-scope S# becomes at least one
       FR#, every A# a scenario) and research's handoff summary
       (`ses handoff show <ws>/research-notes.md`), opening
       sections when designing the component they concern. If `tech-design`
       is approved, the TDD is an input too and the FDD must agree with it —
       a disagreement goes to the user, never resolved silently in either.
     - `full`, implemented — **change**. Gate: `ses status require <ws> implement=done`.
       The change is each `branch.<repo>` field against that repo's mainline;
       contract and TDD are context.
     - `change-request` — **change**. Gate: `ses status require <ws> verify=done`.
       The change is the CR branch; `analysis.md` (its mini contract) is
       context.
     No stage is added to the task; progress is recorded in the `fdd` field (§3).
   - **Standalone** (`brief`, `as-built`, `change`): resolve `<work-repo>`,
     `<workspace-root>`, and the `<repo-set>` per
     `<root>/core/repo-resolution.md` (enumerate with
     `ses list-repos <repos-folder>` and confirm
     the list with the user — actors and interfaces are searched across all
     of them), then create the workspace:
     `ses new-task <task-id> auto func-design <work-repo> <repo-set>`
     (or resume from `ses status show <ws>`).
     Record `ses status field <ws> fdd-mode <forward|as-built|change>` and
     `ses status field <ws> source "<brief path | component(s) | repo base..head>"`.
   - **Change mode, either way**: pin the refs, which move —
     `git -C <repo> rev-parse <base> <head>` → `ses status field <ws> change-base <sha>`
     and `ses status field <ws> change-head <sha>` (one pair per repo for a
     multi-repo change: `change-base.<repo>`, `change-head.<repo>`).
3. Audience: from the invocation, else `business`. Record it:
   `ses status field <ws> fdd-audience <business|technical>`. Agree the scope
   in two sentences — which function, change, or components; which aspects;
   who will read it — and record it (`ses status field <ws> doc-scope "..."`).
   Attached forward mode inherits the contract's scope instead.
4. Read `<work-repo>/.domain-glossary.md` (business terms are referenced, not
   re-defined) and the rules files `ses repo-rules <work-repo>`
   lists. If they — or the user, with a client-mandated FDD template —
   prescribe a format, map the content onto it and record the choice
   (`ses status field <ws> doc-format "..."`); the abstraction rules still
   apply. If that format requires content the lint flags (a data-type column,
   say), record the kinds (`ses status field <ws> fdd-lint-allow "DATATYPE"`)
   and pass them as `--allow` — never otherwise.
5. Unknowns follow `<root>/core/decision-protocol.md`.
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

As-built and change modes read the code to learn the logic; translating it to
this level is the job — summarise, don't transcribe. A 400-line procedure is
5–10 steps.

Developer-only detail that the fact-checker needs but stakeholders don't —
component input tables, Appendix A — sits between `<!-- technical:start -->`
and `<!-- technical:end -->`; the business view drops it (§4).

`ses fdd-lint <ws>/fdd.md` flags code-level content
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
   - change — read the diff stat-first and file by file:
     `ses review-diff <repo> <change-base> <change-head>`, then
     `--file <path>` for each file in its review list. For each changed
     component, read the code at both ends (`git -C <repo> show <sha>:<path>`)
     — a diff hunk alone hides the surrounding flow that gives it meaning.
     FR# are what the change makes the system do, each citing the head
     commit; attached, also the S# it meets. A change with no S# or a planned
     S# with no change is reported to the user as a Q#.
2. Existing behaviour, in every mode, comes from the code, not the brief or
   folklore: entry points, callers and schedules (§3 actors), data read and
   changed (§7), outputs and their consumers (§8), error paths (§9). Search
   every repo in `<repo-set>` with
   `ses search --ws <ws> -- <patterns>` (counts first) and
   keep its per-repo rows in evidence — "no other consumer" needs the search
   that found none. Attached mode reuses research's rows while a repo's sha
   is unchanged.
3. Confirm every existing table, column, and code value the FDD will name
   against the schema — DDL in the repo, or the live data dictionary where
   `$SES_DB_CONN` is reachable (read-only queries, output captured with
   `ses capture` into `evidence/`). New ones are
   marked `new` in §7.1 and must not collide with an existing name.
4. Build Appendix A (claim → source) as you go — it is the fact-checker's
   input and the resume point. Change mode cites the head commit for "after"
   claims and the base commit for "before" claims.
5. Standalone: `ses status set <ws> analyze=done`.

## 2. Draft

1. Copy `<root>/templates/fdd.md` → `<ws>/fdd.md`.
2. Fill §2.1 FIRST. Every FR# must land in at least one §5 step and one §14
   scenario; attached forward mode, every A# appears in §14 too. An FR# with
   no natural home in §5 means the design is incomplete.
3. §4: the business-level flow — the traced flow (as-built, change) or the
   research call graph plus the proposed change (forward), never from
   memory. Forward and change modes fill **Before and after this change**:
   for stakeholders it is the most-read part of the document, so every row
   is concrete ("orders reach the vendor the same night", not "improved
   processing").
4. §5: one subsection per component the function involves; unchanged ones
   only where a reader needs them for context, marked so. Change mode marks
   each step `(new)` or `(changed)`. Steps reference BR#, EX#, and
   `table.column` — every rule stated once in §6, every failure path once in
   §9 with its business recovery. Keep each component's Inputs table, and
   Appendix A, inside the technical markers.
5. Write for the recorded audience; for `business`, a sentence that needs
   the technical regions to make sense is rewritten. No section is dropped:
   "None" is stated, with the reason where it is not obvious.
6. Run `ses fdd-lint [--allow <kinds>] <ws>/fdd.md`
   (kinds from `ses status get <ws> fdd-lint-allow`, if recorded) and fix
   every finding per the abstraction rules.
7. Standalone: `ses status set <ws> draft=done`.

## 3. Quality gates

1. Self-check with `<root>/checklists/func-design.md`.
2. Run the fact-check procedure in
   `<root>/com.github.copilot/agents/doc-fact-checker.agent.md` on fdd.md —
   delegated per `<root>/core/reviewers.md`; pass the mode and, in change mode, the repo with
   `change-base`/`change-head`. Resolve every finding; fixes keep the
   functional level (a WRONG step is corrected in plain language, not
   replaced by the code it summarises). Standalone:
   `ses status set <ws> fact-check=done`.
3. Write the **handoff summary** block now — after the fact-check fixes —
   then run `ses handoff check <ws>/fdd.md` and the lint
   again; both must pass.
4. Render the audience view (§4 step 1) and present the FDD from it, then
   the summary: requirements and traceability, before vs after, business
   rules, exceptions, open Q# items, plus open ASSUMPTIONS.md entries for
   ratification (decision-protocol §4). Approval with a Q# still open needs
   the user to defer it explicitly, recorded in its §13 status. Iterate until
   approved — each revision updates the summary in the same edit and re-runs
   the handoff check and lint. Record approval + date in the FDD header.
5. Record:
   - Attached: `ses status field <ws> fdd "approved <date> by <who>"`.
     Forward mode while `tech-design` is pending:
     `ses status next <ws> "Run /tech-design — the TDD realises the approved FDD."`
   - Standalone (gate first: `ses status require <ws> fact-check=done`):
     `ses status set <ws> approval=approved --next "Deliver the FDD (/func-design §4)."`

## 4. Deliver

1. Render the view for the recorded audience:
   `ses fdd-view <ws>/fdd.md --audience <fdd-audience>`
   → `<ws>/fdd.<audience>.md`. `business` drops the handoff summary, the
   technical regions, and Appendix A; `technical` keeps them. Both drop
   template guidance. Never hand stakeholders `fdd.md` itself.
2. Ask which output formats are needed unless `ses status get <ws> formats`
   answers it, and record them (`ses status field <ws> formats "<docx,pdf,...>"`).
   Convert the view (not fdd.md) via
   `ses md2docx | ses md2pdf | ses md2confluence`
   into `<ws>/deliverables/`; verify each file is non-empty. Attached
   forward mode can leave conversion to the task's /deliver package — it
   converts the same view.
3. Present the FDD and where it is; list deferred Q# items so the user can
   close them.
4. Standalone: `ses status set <ws> deliver=done`.

## Changes after approval

Never edit an approved FDD silently — a change needs re-approval and a note
in the header. Attached forward mode: when /tech-design, /grill, or
/implement finds the FDD wrong or incomplete, the FDD is amended and
re-approved first; the TDD never quietly departs from it. Change mode: if
the code changes after approval, re-pin `change-head` and re-run from §1.

## Fault tolerance

Write incrementally. On resume, diff §2.1 against §5 and §14 to find FR#
without a home, and Appendix A against §5 to find unsourced steps; standalone
stage state comes from `ses status show <ws>`.
