# Repo resolution — rationale

> The binding rules are in `repo-resolution.md` (the short card every skill
> reads). This file explains why each rule exists and the failure it
> prevents; read it when a case is ambiguous or a rule seems not to fit. If
> the two ever disagree, the card wins — fix this file.


The shared rule for every stack skill, resolved BEFORE reading or writing
anything. Analysis and writing have DIFFERENT scopes: analysis spans every repo
in the workspace, writing is confined to the repos the scope contract names.
Four things to resolve, and none of them is "the current directory":

- **`<work-repo>`** — the repository whose code the task changes: the directory
  containing its `.git`. Its own rules files (AGENTS.md, CODING_STANDARDS.md,
  … — listed by `ses repo-rules`) live in it.
- **`<workspace-root>`** — the directory holding `work/<task-id>/` and the
  workspace's one domain glossary, `work/domain-glossary.md`. In a
  multi-repo workspace it is the folder holding the repos, so task state sits
  beside the repos rather than inside one of them: a task usually spans
  several repos, and putting its workspace in one repo would make that repo
  look like the owner, pollute its `git status`, and need a gitignore entry
  in every repo. A standalone repo keeps `work/` inside itself.
  `ses workspace-root <work-repo>` applies the rule; `$SES_WORKSPACE_ROOT` pins it.
- **`<repos-folder>`** — the folder the repos sit in (the editor workspace
  folder). The parent of `<work-repo>` when repos are siblings.
- **`<repo-set>`** — every repo in ANALYSIS scope: by default all repos under
  `<repos-folder>`, enumerated by `ses list-repos <repos-folder>`. This
  is the search space for impact analysis, call graphs, and dependency mapping.
  It is not the write scope.

## Why this is a rule and not an assumption

A VS Code workspace rooted at a *parent folder* containing several repos is a
normal setup:

```
workspace-root-folder/        ← editor/session cwd, NOT a repo
├── repo-a/  .git  AGENTS.md
├── repo-b/  .git  CODING_STANDARDS.md
├── repo-c/  .git
├── repo-d/  .git  AGENTS.md
└── work/           task workspaces (workspace-root)
```

There, cwd is not a repo at all. A bare relative reference like `AGENTS.md`
resolves against the parent folder, finds nothing (or the wrong file), and the
skill silently concludes the repo has no rules — then ignores rules or re-asks
knowledge that is sitting in the child repo. That failure is invisible:
nothing errors, the answers just get worse.

The layout also means a task's *analysis* scope is usually wider than its
*write* scope: the repos are siblings because they talk to each other, so
impact crosses them even when the change doesn't. Both scopes are resolved
below and neither is guessed.

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
3. **The repo set** (analysis scope): `repos-analyzed:` from STATUS.md if
   recorded; otherwise enumerate with
   `ses list-repos <repos-folder>`, where
   `<repos-folder>` is the folder holding the repos (the parent of
   `<work-repo>` when they are siblings, else ask). Show the user the list and
   confirm it before analysis — including any repo they want excluded, which
   is recorded as an exclusion rather than silently dropped.
4. Record all of it in `STATUS.md` as soon as the workspace exists —
   `ses new-task <task-id> auto <pipeline> <work-repo> <repo-set>`
   writes the paths absolutised (`auto` applies the workspace-root rule). Later stages read them back per step 1.

## Using them

- Files are ALWAYS addressed with their prefix: rules files through
  `ses repo-rules <work-repo>`, the glossary as
  `<workspace-root>/work/domain-glossary.md`. Never bare
  relative — the bare form is only correct when cwd happens to be the repo,
  which is exactly the assumption that breaks.
- Task artifacts are always `<workspace-root>/work/<task-id>/…`.
- Shell/tool calls that must run inside the repo (git, test runners, grep over
  the codebase) run with `<work-repo>` as their working directory, not the
  session cwd.

## Analysis spans every repo — always

A workspace holding several repos usually holds them because they are RELATED:
one calls another's package, consumes its extract, reads its tables, or is
deployed alongside it. So impact analysis, caller/dependent searches, call
graphs, and dependency maps run across the whole `<repo-set>`, never only
`<work-repo>`.

This is not optional care — it is the blast-radius guarantee. A caller living
in a sibling repo that the search never visited is indistinguishable, in the
output, from no caller at all: the analysis reports "3 callers" with the same
confidence either way, and the missed one breaks in production. Searching one
repo and reporting workspace-wide impact is a false negative the reader cannot
detect.

Rules for cross-repo analysis:

1. **Enumerate before searching.** Run `ses list-repos <repos-folder>`
   and record the resulting list in the workspace (STATUS.md `repos-analyzed:`
   and the analysis/research notes). An analysis whose repo list isn't written
   down cannot be audited later.
2. **Search every repo in the set, and show it.** Record the command per repo.
   A repo with zero hits is reported as *searched, no references found* with
   the command that found nothing — never omitted. "Nothing depends on this"
   is a claim that requires evidence from every repo, exactly like /understand
   §3 requires showing the search that found nothing.
3. **Qualify every reference with its repo**: `<repo-name>:<path>:<line>`.
   Bare `file:line` is ambiguous the moment two repos are in play, and
   ambiguous references defeat the accuracy guarantee they exist to serve.
4. **Narrowing the set is a user decision, recorded.** If the user scopes
   analysis to fewer repos ("ignore the archive repo"), that goes in the scope
   contract's out-of-scope table with the reason — never assumed because a
   repo looks unrelated. Per decision-protocol §3 this is scope-affecting.
5. **Each repo answers in its own dialect.** Read the rules files of each
   repo you analyze. The same term can mean different things in two repos,
   and that mismatch is itself a finding worth raising rather than smoothing
   over — which is why the workspace keeps ONE glossary,
   `work/domain-glossary.md`, holding every repo's meaning of a term in one
   entry. Per-repo glossaries split that mismatch across files nobody
   compared, and a glossary inside a repo had to be committed, which tangled
   it with task branches; in `work/` it never reaches git.

## Writing is confined to the repos the contract names

`<changed-repos>` is the subset of `<repo-set>` the task may modify. It starts
as `[<work-repo>]` and grows ONLY through the scope contract, with the user's
approval — analysis discovering that a sibling repo must change is a finding to
present at the gate, not a licence to edit it.

For a task that legitimately spans repos:

- The task workspace stays single: one `work/<task-id>/` under
  `<workspace-root>`, one scope contract, one STATUS.md. Splitting state per
  repo breaks resumability.
- Every impl-doc step names its repo; the step's verification and rollback run
  in that repo.
- Each changed repo gets its own branch (its own rules files, else its existing
  branch naming, decide the name) and its own checkpoint commits. Record the branch per repo in
  STATUS.md.
- Code written in a repo follows THAT repo's rules files, not the primary
  repo's. Rules files are the team's own: the framework reads and follows
  them but never writes to them — a rule worth adding is proposed to the user.
- Where repos depend on each other, the impl doc states the deploy ORDER and
  what the intermediate state looks like — a consumer deployed before the
  producer is a broken window between deployments, and the plan must say
  whether that window is acceptable.
- A repo in `<repo-set>` but not in `<changed-repos>` is read-only context:
  never write code, `work/`, or a branch into it.
