---
name: intake
description: Start a new engineering task from a solution design document or requirement brief. Parses the brief into a requirements summary and a scope contract, creates the task workspace, and gates on user approval of scope. Use when the user receives a new SDD, requirement brief, or work request.
argument-hint: <path-to-brief-or-pasted-requirements> [task-id]
---

# /intake — brief to approved scope contract

> Framework files: `<root>` is what `ses root` prints — run it once. Every
> framework script runs as `ses <command>` (`ses help` lists them). If `ses`
> is not on PATH, use `python3 <skill-dir>/../../bin/ses` in its place —
> `<skill-dir>` is the folder this SKILL.md was loaded from — here and for
> every `ses` below. If neither runs, stop and ask the user (README →
> Install); never guess another path.

You are starting a new task in the software-engineer-stack lifecycle. Your output
is a task workspace containing a requirements summary and a **scope contract**
the user has explicitly approved. Nothing downstream may begin before that approval.

## 0. Preamble (every stack skill starts this way)

1. Load applicable lessons: `ses lessons intake`,
   re-run with `--repo <work-repo name> --lang <languages>` once step 2 and
   the brief tell you them. Apply them; don't read the lesson files whole.
2. Resolve `<work-repo>`, `<workspace-root>`, and the `<repo-set>` per
   `<root>/core/repo-resolution.md` — do NOT assume the current
   directory is the repo. If cwd is a parent folder holding several repos, ask
   which one this task is anchored in before creating anything, and enumerate
   the rest with `ses list-repos <repos-folder>`:
   they are all in ANALYSIS scope by default, because siblings in a workspace
   usually call each other. Show the user the list and confirm it; a repo they
   want excluded becomes an exclusion row, not a silent omission.
3. Unknowns follow `<root>/core/decision-protocol.md`: check
   checkable facts; proceed only on high-confidence, reversible, in-scope
   calls logged to the workspace ASSUMPTIONS.md; stop and ask for everything
   else.

## 1. Create the workspace

1. Ask for a task id if none was given (Jira key or short slug).
2. Run `ses new-task <task-id> auto full <work-repo> <repo-set>`
   (`<repo-set>` comma-separated — it lands in STATUS.md as the recorded
   analysis scope every later stage searches).
   - Pass `auto` as `<workspace-root>`: `work/` goes in the folder holding
     the repos (multi-repo workspace) or the repo itself (standalone) — as
     `ses workspace-root <work-repo>` prints. When it lands inside a repo,
     `ses new-task` keeps it out of git itself (a local `.git/info/exclude`
     entry — never committed, the team's `.gitignore` untouched); pass on any
     WARNING it prints that `work/` is already tracked.
   - Both paths land in STATUS.md absolutised; every later stage reads them
     from there instead of re-deriving from its own cwd.
   - If the workspace already exists, read it with
     `ses status show <ws>`
     (`<ws>` = `<workspace-root>/work/<id>`) and RESUME from the recorded
     state instead of starting over.
   - Run `ses status validate <ws>`; a workspace that fails validation (e.g.
     one scaffolded by an older version, missing `workspace-root`) is fixed
     before anything else is written into it.

## 2. Ingest the brief

1. Accept the brief as: a file path (md/txt), a docx/pdf (convert with
   `pandoc -t markdown` or extract text; if conversion fails, ask the user to
   paste the content), or pasted text.
2. Store the original (or its converted markdown) as `<ws>/brief.md` so the
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
  user in one batch (through the harness's ask-user tool where it has one).
- **Term inventory**: list every business/functional term the brief leans on
  ("purchase order", "approved", "settlement"), then look each up in
  `<work-repo>/.domain-glossary.md`. Known terms: link the entry in the scope
  contract instead of re-defining. Unknown terms: mark as research targets.
  A term the brief uses DIFFERENTLY from its glossary entry is ALWAYS an open
  question — the brief may be wrong or the glossary stale; never silently
  pick a side.
- Do a first scan **across every repo in `<repo-set>`** for the objects the
  brief names (`ses search --ws <ws> --
  <names>` — counts first, every repo), to populate the "interfaces & objects expected to change" table
  — each row carries its repo. A brief written against one repo routinely
  implicates others; finding that at intake is cheap, finding it during
  /implement is not.
- Fill the contract's "Repos" section: which repos are analyzed, which are
  expected to CHANGE (the write scope — everything else is read-only context),
  and any repo excluded from analysis with the user's reason.
- Run `ses repo-rules <repo>` for each repo expected to change
  and note the rules files it lists in the contract's constraints; a repo with
  none falls back to framework `standards/` and its surrounding code.

## 4. Draft the scope contract

1. Copy `<root>/templates/scope-contract.md` to
   `<ws>/scope-contract.md` and fill every section.
2. Each in-scope item must be checkable; each must have at least one acceptance
   criterion stating HOW it will be verified (query, test, run).
3. Run `<root>/checklists/intake.md` against your draft; fix gaps.
4. Write the **handoff summary** block last (one line per S#/N#/A#/Q#, the
   repos, the objects expected to change) and run
   `ses handoff check <ws>/scope-contract.md` — it must pass. Every
   later stage reads this block instead of the whole contract.

## 5. Approval gate

1. Present the scope contract to the user, starting from its handoff summary
   (later stages work from it, so the user approves it too): objective,
   in-scope list, exclusions, acceptance criteria, open questions — plus any open ASSUMPTIONS.md entries
   for ratification (decision-protocol §4). Ask explicitly: "Approve this scope
   contract? Work will be limited to exactly this."
2. Incorporate feedback and re-present until approved — every revision
   updates the handoff summary in the same edit, and `ses handoff check` must
   pass on the version the user approves. Record approver and date in the
   contract, set version 1. Any later scope change bumps the version
   and updates the summary in the same edit (`ses handoff check` flags every
   downstream summary still on the old version).
3. Only after approval:
   `ses status set <ws> intake=approved --note "by <who>, contract v1" --next "Run /research."`.

## Fault tolerance

- If interrupted at any point, the next /intake run must detect the existing
  workspace via STATUS.md and continue (e.g. brief ingested but contract
  undrafted → resume at step 4).
- Never overwrite an approved scope contract. Scope changes bump the version via
  a new explicit user approval, recorded in the contract's History table.
