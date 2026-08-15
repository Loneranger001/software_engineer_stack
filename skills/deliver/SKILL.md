---
name: deliver
description: Package a finished task - scope audit, evidence bundle, release notes, document conversion to Word/PDF/Confluence, branch push. The final gate before handover. Use when implementation (or a document task) is complete.
argument-hint: "[task-id]"
---

# /deliver — audited, packaged handover

> Path note: `${CLAUDE_PLUGIN_ROOT}` is this framework's root — the ancestor
> directory of this file containing `plugin.json`/`skills/`. Claude Code resolves
> it automatically; other harnesses resolve it from this file's location.

Turn a finished implementation (or document task) into a delivered package:
audited against scope, evidenced, and converted to the formats the user needs.

## 0. Preamble

1. Load lessons tagged `stage:deliver` from
   `${CLAUDE_PLUGIN_ROOT}/knowledge/lessons.md`.
2. Locate the workspace; verify the prior stage is done (`implement: done`,
   or the document pipeline's `fact-check: done`). Take `<work-repo>`,
   `<workspace-root>`, and the changed repos with their branches from STATUS.md
   (`${CLAUDE_PLUGIN_ROOT}/core/repo-resolution.md`) — handover paths and git
   operations use them, not the session cwd. A change spanning repos is
   audited, released, and handed over as ONE delivery: per-repo branches and
   diffs, a single release note stating the deploy ORDER across them.
3. Unknowns follow `${CLAUDE_PLUGIN_ROOT}/core/decision-protocol.md`; at this
   stage almost nothing qualifies for proceed-and-log — delivery questions
   (formats, handover targets) are cheap to ask, so ask.

## 1. Scope audit (blocking)

1. Resolve ASSUMPTIONS.md first: every `open` entry is presented to the user
   for ratification or correction (decision-protocol §4) — nothing ships on
   an unratified guess.
2. Run the audit procedure in `${CLAUDE_PLUGIN_ROOT}/agents/scope-auditor.md`
   with: the scope contract, the full branch diff (or produced documents),
   PARKED.md, ASSUMPTIONS.md, and the evidence directory — as a subagent
   where the harness supports it; otherwise execute the procedure yourself as
   a separate, fresh audit pass held to its report format.
3. Outcomes:
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

## 3a. Publish back to Atlassian (opt-in)

`md2confluence.sh` produces text for the user to paste. When the deliverable
should actually land in Confluence, or the task's Jira issue should carry the
outcome, the tool skills do it directly. Both are **outward-facing writes**, so
decision-protocol §3 applies without exception: **ask before every one**, show
what will be posted and where, and take silence as no. Nothing here is implied
by "deliver" — if the user hasn't asked, the pasteable output is the delivery.

**Confluence.** Convert the Markdown deliverable to Confluence storage format
(HTML — `pandoc -f gfm -t html`), then publish:

```bash
# first publish
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/write.py \
    create --space <SPACE> --title "<title>" --body-file <deliverable>.html [--parent <page-id>]

# re-delivery: update the page recorded in STATUS.md, never create a second one
python3 ${CLAUDE_PLUGIN_ROOT}/skills/confluence-ops/utils/confluence/write.py \
    update <page-id> --body-file <deliverable>.html
```

- Record the page id and URL in STATUS.md and in `work/<id>/deliverables/`.
  That record is what makes re-running /deliver idempotent — without it, a
  second run publishes a duplicate page instead of a new version.
- Mermaid blocks in the deliverable are rendered to SVG and attached
  automatically when `mmdc` is installed; without it they fall back to a code
  block. Say which one happened rather than letting the user discover it.
- Never use `move` as part of delivery — it is a copy-then-delete that loses
  history, comments and attachments.

**Jira.** When the task came from an issue (STATUS.md `brief-source`), report
the outcome on it:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/jira-ops/utils/jira/write.py \
    comment PROJ-1234 --file work/<id>/deliverables/jira-comment.json
```

- The comment states what shipped, the branch, and links to the published
  page — it is a handover note, not a paste of the whole release notes.
- Draft it, show the user the exact text, post it only on approval.
- **Transitioning the issue is a separate ask**, and the helper refuses to move
  an issue assigned to someone else without `--force`. Do not pass `--force` on
  the user's behalf: if the issue is someone else's, report that and stop.
- A failed post is reported, never retried silently into a duplicate comment.

## 4. Close

1. Self-check with `${CLAUDE_PLUGIN_ROOT}/checklists/deliver.md`.
2. Report to the user: what was delivered, where (branch, deliverables/,
   plus any Confluence page or Jira issue written to in §3a), evidence
   summary, PARKED.md follow-ups.
3. Update STATUS.md: `deliver: done`, next action `/retro`.
4. Prompt the user to run /retro while the task is fresh — it is how the
   framework improves.

## Fault tolerance

Every sub-step is idempotent (re-running conversions overwrites, re-pushing is
safe, the audit can re-run). On resume, check which of §1–§4 already completed
via STATUS.md log entries and artifact existence.

The Atlassian writes in §3a are the exception that has to be made idempotent by
hand: a second `create` makes a second page and a second `comment` makes a
second comment. Read STATUS.md for an already-published page id and `update` it
instead, and re-confirm with the user before re-posting a comment.
