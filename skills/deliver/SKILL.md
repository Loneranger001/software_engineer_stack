---
name: deliver
description: Package a finished task - scope audit, evidence bundle, release notes, document conversion to Word/PDF/Confluence, branch push. The final gate before handover. Use when implementation (or a document task) is complete.
argument-hint: "[task-id]"
---

# /deliver — audited, packaged handover

> Framework files: `<root>` is what `ses root` prints — run it once. Every
> framework script runs as `ses <command>` (`ses help` lists them). If `ses`
> is not on PATH, use `python3 <skill-dir>/../../bin/ses` in its place —
> `<skill-dir>` is the folder this SKILL.md was loaded from — here and for
> every `ses` below. If neither runs, stop and ask the user (README →
> Install); never guess another path.

Turn a finished implementation (or document task) into a delivered package:
audited against scope, evidenced, and converted to the formats the user needs.

## 0. Preamble

1. Load applicable lessons: `ses lessons deliver` — it prints only
   the matching entries; don't read the lesson files whole.
2. Locate the workspace and gate on the prior stage:
   `ses status require <ws> implement=done`
   (`<ws>` = `<workspace-root>/work/<id>`); for the document pipeline
   (`ses status get <ws> pipeline`) gate on `fact-check=done` instead.
   Non-zero exit = stop. Take `<work-repo>`,
   `<workspace-root>`, and the changed repos with their branches from STATUS.md
   (`<root>/core/repo-resolution.md`) — handover paths and git
   operations use them, not the session cwd. A change spanning repos is
   audited, released, and handed over as ONE delivery: per-repo branches and
   diffs, a single release note stating the deploy ORDER across them.
3. Unknowns follow `<root>/core/decision-protocol.md`; at this
   stage almost nothing qualifies for proceed-and-log — delivery questions
   (formats, handover targets) are cheap to ask, so ask.

## 1. Scope audit (blocking)

1. Resolve ASSUMPTIONS.md first: every `open` entry is presented to the user
   for ratification or correction (decision-protocol §4) — nothing ships on
   an unratified guess.
2. Run the audit procedure in `<root>/com.github.copilot/agents/scope-auditor.agent.md`
   with: the scope contract, each changed repo's path, mainline and branch
   (the auditor reads the diff itself via `ses review-diff`) or the produced
   documents,
   PARKED.md, ASSUMPTIONS.md, and the evidence directory (it runs
   `ses checkpoint verify` against the hashes in the checkpoint commits) —
   delegated per `<root>/core/reviewers.md`.
3. Outcomes:
   - PASS → proceed.
   - Violations → either remove the out-of-scope change (preferred) or get an
     explicit written user waiver / scope-contract version bump. Re-run the
     audit after fixes. Never deliver with an unresolved violation.

## 2. Consistency sweep

The documents must match what was actually built:

- tdd.md, impl-doc.md, and fdd.md (when present) vs the final diff — update
  stale sections and mark
  them `(updated at delivery: <reason>)`, updating each document's handoff
  summary — and, for fdd.md and tdd.md, its review version, re-stamped — in
  the same edit (`ses handoff check <ws>` must pass); substantive
  divergence needs the user's ack since those documents were approved.
- Every acceptance criterion → evidence file → PASS. Missing evidence means
  going back to /implement's verification, not papering over.

## 3. Package

1. Fill `<root>/templates/release-notes.md` →
   `<ws>/release-notes.md` (deployment + rollback usable stand-alone),
   written to `<root>/standards/writing.md`;
   `ses prose-lint <ws>/release-notes.md` must pass.
2. Convert deliverables per the user's needs using
   `ses md2docx | ses md2pdf | ses md2confluence`
   into `<ws>/deliverables/`. Ask once which formats are wanted unless
   `ses status get <ws> formats` already answers it, and record the answer
   (`ses status field <ws> formats "<docx,pdf,...>"`); verify each produced
   file is non-empty. A design goes out as its review version, rendered
   with `ses review-version render <ws>/fdd.md` (or `<ws>/tdd.md`) into
   `<ws>/deliverables/` and converted from there — never fdd.md or tdd.md
   directly. A developer who asks for the full FDD gets
   `ses fdd-view <ws>/fdd.md --audience technical`.
3. Push every changed repo's task branch (the `branch.<repo>` fields:
   `git -C <repo> push -u origin <branch>`; retry with backoff on network
   failure). Only those branches leave the machine — the task workspace
   (`work/`, deliverables included) is never committed or pushed, and the
   audit's `ses checkpoint verify` has already proven no workspace file is on
   them. Do NOT open a PR / merge unless the user asks.

## 4. Close

1. Self-check with `<root>/checklists/deliver.md`.
2. Report to the user: what was delivered, where (branch, deliverables/),
   evidence summary, PARKED.md follow-ups.
3. Record: `ses status set <ws> deliver=done --next "Run /retro."`
4. Prompt the user to run /retro while the task is fresh — it is how the
   framework improves.

## Fault tolerance

Every sub-step is idempotent (re-running conversions overwrites, re-pushing is
safe, the audit can re-run). On resume, check which of §1–§4 already completed
from the artifacts themselves: the audit report, release-notes.md, the files in
deliverables/, and whether each branch is on its remote.
