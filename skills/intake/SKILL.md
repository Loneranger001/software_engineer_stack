---
name: intake
description: Start a new engineering task from a solution design document or requirement brief. Parses the brief into a requirements summary and a scope contract, creates the task workspace, and gates on user approval of scope. Use when the user receives a new SDD, requirement brief, or work request.
argument-hint: <path-to-brief-or-pasted-requirements> [task-id]
---

# /intake — brief to approved scope contract

You are starting a new task in the software-engineer-stack lifecycle. Your output
is a task workspace containing a requirements summary and a **scope contract**
the user has explicitly approved. Nothing downstream may begin before that approval.

## 0. Preamble (every stack skill starts this way)

1. Read `${CLAUDE_PLUGIN_ROOT}/knowledge/lessons.md` and note lessons tagged
   `stage:intake` or matching this repo/language mix. Apply them.
2. Determine the work repo (current directory unless the user says otherwise).

## 1. Create the workspace

1. Ask for a task id if none was given (Jira key or short slug).
2. Run `${CLAUDE_PLUGIN_ROOT}/scripts/new-task.sh <task-id> <workspace-root> full`.
   - Workspace root defaults to the work repo. If `work/` shouldn't be committed
     there, remind the user to gitignore it (don't edit .gitignore unasked).
   - If the workspace already exists, read its STATUS.md and RESUME from the
     recorded state instead of starting over.

## 2. Ingest the brief

1. Accept the brief as: a file path (md/txt), a docx/pdf (convert with
   `pandoc -t markdown` or extract text; if conversion fails, ask the user to
   paste the content), or pasted text.
2. Store the original (or its converted markdown) as `work/<id>/brief.md` so the
   task is self-contained.
3. Read the ENTIRE brief. Long documents: read in chunks; never summarize from
   the first section alone.

## 3. Extract requirements — accuracy rules

- Walk the brief section by section. Classify every statement that implies work
  as: in-scope item, exclusion, constraint, assumption, or open question.
- **Nothing is silently dropped**: if you choose to ignore a sentence, it must
  appear under exclusions or open questions.
- **Nothing is silently invented**: do not add requirements the brief doesn't
  state. Improvements you spot go to open questions ("Should X also…?").
- Ambiguity is never resolved by assumption. Collect open questions and ask the
  user in one batch (use AskUserQuestion when available).
- Do a first scan of the repo for the objects the brief names, to populate the
  "interfaces & objects expected to change" table. If `.conventions.md` is
  missing, suggest running /repo-profile after intake.

## 4. Draft the scope contract

1. Copy `${CLAUDE_PLUGIN_ROOT}/templates/scope-contract.md` to
   `work/<id>/scope-contract.md` and fill every section.
2. Each in-scope item must be checkable; each must have at least one acceptance
   criterion stating HOW it will be verified (query, test, run).
3. Run `${CLAUDE_PLUGIN_ROOT}/checklists/intake.md` against your draft; fix gaps.

## 5. Approval gate

1. Present the scope contract to the user: objective, in-scope list, exclusions,
   acceptance criteria, open questions. Ask explicitly: "Approve this scope
   contract? Work will be limited to exactly this."
2. Incorporate feedback and re-present until approved. Record approver and date
   in the contract, set version 1.
3. Only after approval: update STATUS.md (`intake: approved`), append to its log,
   set next action to `/research`.

## Fault tolerance

- If interrupted at any point, the next /intake run must detect the existing
  workspace via STATUS.md and continue (e.g. brief ingested but contract
  undrafted → resume at step 4).
- Never overwrite an approved scope contract. Scope changes bump the version via
  a new explicit user approval, recorded in the contract's History table.
