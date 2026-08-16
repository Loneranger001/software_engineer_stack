# Repo resolution — where the files actually are

The shared rule for every stack skill, resolved BEFORE reading or writing
anything. Analysis and writing have DIFFERENT scopes: analysis spans every repo
in the workspace, writing is confined to the repos the scope contract names.
Five things to resolve, and none of them is "the current directory":

- **`<work-repo>`** — the repository whose code the task changes: the directory
  containing its `.git`. Repo-level memory lives at its root —
  `.conventions.md` (from /repo-profile) and `.domain-glossary.md`.
- **`<estate-root>`** — where ESTATE-level memory lives:
  `.platform-capabilities.md` (from /estate-profile), the inventory of
  integration mechanisms the estate actually has. Resolution order below.
- **`<workspace-root>`** — the directory holding `work/<task-id>/`. Defaults to
  `<work-repo>`; the user may point it elsewhere (e.g. workspaces kept outside
  the repo).
- **`<repos-folder>`** — the folder the repos sit in (the editor workspace
  folder). The parent of `<work-repo>` when repos are siblings.
- **`<repo-set>`** — every repo in ANALYSIS scope: by default all repos under
  `<repos-folder>`, enumerated by `scripts/list-repos.sh <repos-folder>`. This
  is the search space for impact analysis, call graphs, and dependency mapping.
  It is not the write scope.

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
   `${CLAUDE_PLUGIN_ROOT}/scripts/list-repos.sh <repos-folder>`, where
   `<repos-folder>` is the folder holding the repos (the parent of
   `<work-repo>` when they are siblings, else ask). Show the user the list and
   confirm it before analysis — including any repo they want excluded, which
   is recorded as an exclusion rather than silently dropped.
4. **The estate root** (platform memory): `platform-capabilities:` from
   STATUS.md if recorded; else `<repos-folder>` when the repos are siblings
   under one folder; else `<work-repo>`. /estate-profile states the absolute
   path it wrote to and records it back into STATUS.md, so later stages read it
   rather than re-deriving.
5. Record all of it in `STATUS.md` as soon as the workspace exists —
   `scripts/new-task.sh <task-id> <workspace-root> <pipeline> <work-repo> <repo-set>`
   writes the paths absolutised. Later stages read them back per step 1.

## Using them

- Repo-level artifacts are ALWAYS written with the prefix:
  `<work-repo>/.conventions.md`, `<work-repo>/.domain-glossary.md`. Never bare
  relative — the bare form is only correct when cwd happens to be the repo,
  which is exactly the assumption that breaks.
- Estate-level artifacts take the estate prefix:
  `<estate-root>/.platform-capabilities.md`. Conventions are a property of a
  repo; integration technology is a property of the ESTATE — one broker, one
  scheduler, one file-transfer host serve every repo — so this file is shared
  by the whole repo set rather than duplicated per repo.
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

1. **Enumerate before searching.** Run `scripts/list-repos.sh <repos-folder>`
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
5. **Each repo answers in its own dialect.** Read the `.conventions.md` and
   `.domain-glossary.md` of each repo you analyze; the same term can mean
   different things in two repos, and that mismatch is itself a finding worth
   raising rather than smoothing over.

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
- Each changed repo gets its own branch (its own `.conventions.md` decides the
  branch name) and its own checkpoint commits. Record the branch per repo in
  STATUS.md.
- Code written in a repo follows THAT repo's conventions, not the primary
  repo's.
- Where repos depend on each other, the impl doc states the deploy ORDER and
  what the intermediate state looks like — a consumer deployed before the
  producer is a broken window between deployments, and the plan must say
  whether that window is acceptable.
- A repo in `<repo-set>` but not in `<changed-repos>` is read-only context:
  never write code, `work/`, or a branch into it. (`/repo-profile` writing
  `.conventions.md` is the deliberate exception — that is a per-repo cache,
  and each repo owns its own.)
