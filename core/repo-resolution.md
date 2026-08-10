# Repo resolution — where the files actually are

The shared rule for every stack skill, resolved BEFORE reading or writing
anything. Two paths matter, and neither of them is "the current directory":

- **`<work-repo>`** — the repository whose code the task changes: the directory
  containing its `.git`. Repo-level memory lives at its root —
  `.conventions.md` (from /repo-profile) and `.domain-glossary.md`.
- **`<workspace-root>`** — the directory holding `work/<task-id>/`. Defaults to
  `<work-repo>`; the user may point it elsewhere (e.g. workspaces kept outside
  the repo).

## Why this is a rule and not an assumption

A VS Code workspace rooted at a *parent folder* containing several repos is a
normal setup:

```
workspace-root-folder/        ← editor/session cwd, NOT a repo
├── repo-a/  .git  .conventions.md
├── repo-b/  .git  .conventions.md
├── repo-c/  .git  .conventions.md
└── repo-d/  .git  .conventions.md
```

There, cwd is not a repo at all. A bare relative reference like
`.conventions.md` resolves against the parent folder, finds nothing, and the
skill silently concludes the repo was never profiled — then re-derives or
re-asks knowledge that is sitting in the child repo. That failure is invisible:
nothing errors, the answers just get worse.

## Resolving

1. **A workspace exists** (a task is in progress): read `work-repo:` and
   `workspace-root:` from its `STATUS.md`. They are recorded as absolute paths
   and they WIN over any inference — never re-derive them from cwd.
2. **No workspace yet** (or the fields are absent — a workspace scaffolded by
   an older version): resolve from the current directory, then record the
   result.
   - `git rev-parse --show-toplevel` succeeds → that is `<work-repo>`.
   - It fails (cwd is above the repos): list immediate subdirectories
     containing `.git`.
     - Exactly one → use it, and state which one you picked.
     - More than one → **ask** which repo this task is about. This is
       `decision-protocol.md` §3: two readings are both defensible, and
       guessing wrong writes files into the wrong repository.
     - None → ask the user for the repo path.
3. Record both paths in `STATUS.md` as soon as the workspace exists —
   `scripts/new-task.sh <task-id> <workspace-root> <pipeline> <work-repo>`
   writes them, absolutised. Later stages read them back per step 1.

## Using them

- Repo-level artifacts are ALWAYS written with the prefix:
  `<work-repo>/.conventions.md`, `<work-repo>/.domain-glossary.md`. Never bare
  relative — the bare form is only correct when cwd happens to be the repo,
  which is exactly the assumption that breaks.
- Task artifacts are always `<workspace-root>/work/<task-id>/…`.
- Shell/tool calls that must run inside the repo (git, test runners, grep over
  the codebase) run with `<work-repo>` as their working directory, not the
  session cwd.

## Tasks that touch more than one repo

One task has exactly one `<work-repo>` — the repo being changed. Other repos
are read-only context: name them in the scope contract's interfaces table,
cite them as `<repo-name>:<path>:<line>` in research, and never write
`.conventions.md`, `work/`, or code into them. A change genuinely needed in a
second repo is a second task (or a scope-contract item with its own approval),
not a side effect of this one.
