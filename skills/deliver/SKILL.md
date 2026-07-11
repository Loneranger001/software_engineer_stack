---
name: deliver
description: Package a finished task - scope audit, evidence bundle, release notes, document conversion to Word/PDF/Confluence, branch push. The final gate before handover. Use when implementation (or a document task) is complete.
argument-hint: "[task-id]"
---

# /deliver — audited, packaged handover

Turn a finished implementation (or document task) into a delivered package:
audited against scope, evidenced, and converted to the formats the user needs.

## 0. Preamble

1. Load lessons tagged `stage:deliver` from
   `${CLAUDE_PLUGIN_ROOT}/knowledge/lessons.md`.
2. Locate the workspace; verify the prior stage is done (`implement: done`,
   or the document pipeline's `fact-check: done`).

## 1. Scope audit (blocking)

1. Launch the `scope-auditor` agent with: the scope contract, the full branch
   diff (or produced documents), PARKED.md, and the evidence directory.
2. Outcomes:
   - PASS → proceed.
   - Violations → either remove the out-of-scope change (preferred) or get an
     explicit written user waiver / scope-contract version bump. Re-run the
     audit after fixes. Never deliver with an unresolved violation.

## 2. Consistency sweep

The documents must match what was actually built:

- tdd.md and impl-doc.md vs the final diff — update stale sections and mark
  them `(updated at delivery: <reason>)`; substantive divergence needs the
  user's ack since those documents were approved.
- Every acceptance criterion → evidence file → PASS. Missing evidence means
  going back to /implement's verification, not papering over.

## 3. Package

1. Fill `${CLAUDE_PLUGIN_ROOT}/templates/release-notes.md` →
   `work/<id>/release-notes.md` (deployment + rollback usable stand-alone).
2. Convert deliverables per the user's needs using
   `${CLAUDE_PLUGIN_ROOT}/scripts/md2docx.sh | md2pdf.sh | md2confluence.sh`
   into `work/<id>/deliverables/`. Ask once which formats are wanted if not
   already recorded in STATUS.md; verify each produced file is non-empty.
3. Push the task branch (`git push -u origin <branch>`; retry with backoff on
   network failure). Do NOT open a PR / merge unless the user asks.

## 4. Close

1. Self-check with `${CLAUDE_PLUGIN_ROOT}/checklists/deliver.md`.
2. Report to the user: what was delivered, where (branch, deliverables/),
   evidence summary, PARKED.md follow-ups.
3. Update STATUS.md: `deliver: done`, next action `/retro`.
4. Prompt the user to run /retro while the task is fresh — it is how the
   framework improves.

## Fault tolerance

Every sub-step is idempotent (re-running conversions overwrites, re-pushing is
safe, the audit can re-run). On resume, check which of §1–§4 already completed
via STATUS.md log entries and artifact existence.
