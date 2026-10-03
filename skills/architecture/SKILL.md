---
name: architecture
description: Produce a high-level architecture at project kickoff - systems in play, every integration between them, the end-to-end flow, data ownership, and key decisions - grounded in the platform inventory so it only proposes mechanisms the estate actually has. Gates on user approval and splits into work packages for /intake. Use when starting a project or initiative that spans systems, before detailed scope exists.
argument-hint: "<brief-path-or-description> [id]"
---

# /architecture — systems, integrations, flow; nothing finer

> Path note: `${CLAUDE_PLUGIN_ROOT}` is this framework's root — the ancestor
> directory of this file containing `plugin.json`/`skills/`. Claude Code resolves
> it automatically; other harnesses resolve it from this file's location.

Produce `work/<id>/architecture.md` and get it user-approved. It answers who
talks to whom, what moves, by which mechanism, who owns each side, and what
happens when it breaks. It deliberately does NOT answer how any one component
is built — that is /tech-design, once per work package.

Two failure modes this stage exists to prevent:

1. **The unbuildable design** — proposing a mechanism the estate does not
   have. Prevented by the closed-world rule against
   `<estate-root>/.platform-capabilities.md`.
2. **The premature design** — drifting into tables, columns and pseudocode
   before scope exists. Prevented by the altitude rule, and by §13 of the
   document, which records what was deliberately left undecided.

Where this sits: BEFORE /intake. An architecture usually spawns several tasks,
so it runs in its own workspace (pipeline `architecture`), and each work
package it produces goes through /intake as a separate task with this document
as part of its brief.

## 0. Preamble

1. Load lessons tagged `stage:architecture` (and `platform`, `integration`)
   from `${CLAUDE_PLUGIN_ROOT}/knowledge/lessons.md`.
2. Resolve `<work-repo>`, `<workspace-root>`, `<repo-set>` and `<estate-root>`
   per `${CLAUDE_PLUGIN_ROOT}/core/repo-resolution.md`. Greenfield is normal
   here — the new system may have no repo yet — but the systems it integrates
   WITH usually do, and those belong in `<repo-set>`.
3. Unknowns follow `${CLAUDE_PLUGIN_ROOT}/core/decision-protocol.md`. At this
   altitude most unknowns are genuinely the user's or another team's to
   answer: expect to ask more than you assume. Choosing an integration
   mechanism is never a proceed-and-log call — it shapes everything after it.

## 1. Workspace & framing

1. Ask for an id if none was given (initiative key or short slug, e.g.
   `PROJ-ARCH`). Run
   `${CLAUDE_PLUGIN_ROOT}/scripts/new-task.sh <id> <workspace-root> architecture <work-repo> <repo-set>`.
   An existing workspace → read its STATUS.md and RESUME at the recorded stage.
2. Ingest the input as `work/<id>/brief.md`: a document (convert docx/pdf with
   `pandoc -t markdown`), pasted text, or — common at kickoff — just a verbal
   description. A description is fine; write down what the user said, in
   their words, before interpreting it.
3. Extract: desired outcomes, systems named, constraints stated, non-goals,
   and business terms (look each up in `<work-repo>/.domain-glossary.md`;
   unknown ones are open questions).
4. Ask ONE framing batch for what the input does not settle, each with a
   proposed default where you have a basis:
   - What triggers the flow (an event, a schedule, a person)?
   - Which systems are fixed (must integrate around) and which are ours to
     change?
   - Latency the outcome actually needs (minutes? T+1?) — the single most
     mechanism-deciding answer, and the one most often left implicit.
   - Order-of-magnitude volume, and growth.
   - Who are the downstream consumers of the result?
5. STATUS.md: `frame: done`.

## 2. Ground in the platform inventory

1. Read `<estate-root>/.platform-capabilities.md` in full.
   - **Missing** → stop and recommend /estate-profile first; explain that
     without it every mechanism is a guess. If the user declines, record that
     decision ({who}, {date}) in the document header as
     `UNGROUNDED — no platform inventory`, mark every mechanism in §5 as an
     assumption, and say so again at the approval gate. Ungrounded is a user
     decision, never a default.
   - **Older than ~6 months**, or the user mentions a platform change →
     suggest a refresh before drafting.
2. List the usable set: §1 rows with status `in-use` or `available`, the §3
   reference patterns, the §6 house NFRs, the §8 negative list. Nothing else
   is available to the proposed design.
3. Gather VERIFIED facts about existing systems — lightly. Reuse what exists
   before tracing anything: platform inventory §2–§3, any
   `work/*/interface-map.md` or understanding docs for these systems. Trace in
   code only what a decision needs (e.g. "does system A already produce a
   daily extract?"). This is not /research: if confirming a fact would take
   a deep investigation, it is an open question for §12, not a reason to
   descend.

## 3. Draft

Copy `${CLAUDE_PLUGIN_ROOT}/templates/architecture.md` →
`work/<id>/architecture.md`. Fill in this order, because each step is derived
from the previous one and the diagrams must agree with the tables:

1. §1 context & goals, §3 systems in play.
2. **§5 integration inventory — before any diagram.** One row per thing that
   moves between two systems. For each row, choose the mechanism by this
   rule, in order:
   1. A platform inventory **§3 reference pattern** that fits the row's
      latency, volume and failure needs. A reused pattern needs no further
      argument — cite it in "Reference patterns reused".
   2. Otherwise, any §1 mechanism with status `in-use` or `available` that
      meets the house NFRs (§6).
   3. Otherwise — **no usable mechanism fits** — STOP and ask
      (decision-protocol §3: scope-affecting, high blast radius). Present
      the options concretely: relax the requirement (e.g. accept T+1),
      reuse a mechanism with a stated limitation, or acquire a new capability
      at the §7 cost. Whatever the user picks is recorded in §8 as a decision;
      a new capability lands in §9.
   - `deprecated` mechanisms are never chosen, even though they are in use —
     that is exactly the case the status exists for.
   - "Failure & recovery posture" is never blank. If it cannot be stated, the
     row is not designed yet.
3. §2 context diagram and §4 flow — drawn FROM §5: every edge is a row, every
   row is an edge.
4. §6 data ownership, §7 boundaries, §8 key decisions (only decisions that
   shape the architecture — the rest go to §13), §9 alternatives, §10 NFR
   fit, §11 risks.
5. §13 deliberately left to design, §14 work packages. Every §5 row is
   covered by a work package or explicitly marked out of scope.

### The altitude rule

Write at the level of systems, flows and contracts. Self-check every section
before moving on:

- No table or column names, DDL, procedure signatures, class names,
  pseudocode, or file layouts. Name the DATA ("approved purchase orders"),
  not its storage.
- If a decision seems to need that detail, make the decision at system level
  ("A sends a daily full extract; B reconciles") and record the detail as a
  §13 item for the work package's tech-design.
- Exception: an existing interface may be NAMED to anchor a VERIFIED claim
  ("A's existing nightly extract, repo-a:bin/run_balance_extract.ksh") — a
  citation, not a design of its internals.

### Accuracy

- Tag every claim in §3–§7 `VERIFIED`, `PROPOSED`, or `EXTERNAL` (template
  header). A `VERIFIED` claim without a source is a finding; a `PROPOSED`
  claim worded as existing behaviour ("A sends…" for something not yet built)
  is a finding.
- `EXTERNAL` claims about another team's system carry who said so and when;
  unconfirmed ones go to §12 with the team that can answer.
- Platform facts the user tells you that the inventory lacks ("B's team
  exposes a REST API we're allowed to use") are offered back to
  `<estate-root>/.platform-capabilities.md` with {who}, {date}, after the user
  confirms — so the next architecture does not re-ask. Never edit the
  inventory silently.

STATUS.md: `draft: done`.

## 4. Stress pass

Attack the draft at architecture altitude — whether the DESIGN has an answer,
not whether code handles it (that is /grill's job later, per package). For
every §5 row, instantiate concrete scenarios with the real systems, at least
one per category (or `n/a` with a reason), recorded in §15:

- **Data**: partial delivery, duplicates, empty feed, unexpected volume spike
- **Lifecycle**: same feed delivered twice, sender fails mid-run, receiver
  down when data arrives, replay after an outage
- **Interface**: the other team changes their side; version skew; a consumer
  nobody listed
- **Temporal**: holidays and month-end, cut-off times, late or backdated data,
  time zones between systems
- **Environment**: transfer host or scheduler down, network partition between
  zones, one side's maintenance window
- **Security/ops**: sensitive data crossing a boundary, credentials and
  rotation, who is alerted and who fixes it

Verdicts: `covered` (cite the §), `fixed` (edit the document now — usually
§5 failure posture — and cite it), or `open`. Open items that need domain
knowledge go to the user in themed rounds with a proposed default (use
AskUserQuestion where available, up to 4 per round). The user may answer,
defer it to a work package's /grill (record in §13), or accept the risk
(record in §11 with their ack). Unanswered is not a terminal state.

STATUS.md: `stress: done`.

## 5. Quality gates

1. Self-check with `${CLAUDE_PLUGIN_ROOT}/checklists/architecture.md`.
2. Run `${CLAUDE_PLUGIN_ROOT}/agents/doc-fact-checker.md` on architecture.md
   (architecture mode — it verifies `VERIFIED` claims against the code, checks
   every §5 mechanism against the platform inventory, cross-checks §2/§4
   against §5, and flags altitude violations). As a subagent where the
   harness supports it, otherwise a separate fresh pass held to its report
   format. Resolve every finding.

## 6. Approval gate

1. Present: the §2 context diagram, the §5 inventory, the §8 decisions, every
   §9 alternative with its cost, open §12 questions, the §14 work packages,
   open ASSUMPTIONS.md entries for ratification (decision-protocol §4) — and,
   if applicable, the UNGROUNDED warning first, not last.
2. Iterate until approved; record approver and date in the header.
3. STATUS.md: `approve: approved`, next action: run /intake once per work
   package with `architecture.md` as part of the brief.

Never edit an approved architecture silently. A change after approval —
including one forced by a work package's /tech-design — is re-presented,
re-approved, and noted in the header.

## How later stages use this document

- **/intake** for a work package records the document's path as
  `architecture:` in the task STATUS.md, and traces in-scope items to the §5
  rows the package covers.
- **/tech-design** for that package conforms to it: same systems, same
  mechanisms, same ownership. A design that needs to deviate says so, and the
  deviation goes back to this document for re-approval — it is not absorbed
  quietly into the TDD.

## Fault tolerance

STATUS.md tracks `frame → draft → stress → approve`; rerun to resume. During
drafting, §5 is the backbone: on resume, diff §5 against §2/§4 and §14 to find
what is unfinished. §15 rows already verdicted are skipped on a re-run of the
stress pass.
