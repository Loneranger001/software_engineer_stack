# Repo resolution — rules

Where every stack skill reads and writes. Resolve BEFORE touching files; none
of these is "the current directory". Why each rule exists, and the failure it
prevents: `${CLAUDE_PLUGIN_ROOT}/core/repo-resolution-rationale.md` — read
it only when a case here is ambiguous.

**Names**
- `<work-repo>` — repo the task changes (holds `.git`, `.conventions.md`,
  `.domain-glossary.md`).
- `<workspace-root>` — directory holding `work/<task-id>/`; defaults to
  `<work-repo>`.
- `<repos-folder>` — folder the repos sit in (parent of `<work-repo>` when
  repos are siblings; otherwise ask).
- `<repo-set>` — ANALYSIS scope: every repo under `<repos-folder>`.
- `<changed-repos>` — WRITE scope: starts as `[<work-repo>]`.

**Resolve**
1. Workspace exists → `${CLAUDE_PLUGIN_ROOT}/scripts/status.py show <ws>`
   (`work-repo`, `workspace-root`, `repos-analyzed`; `<ws>` =
   `<workspace-root>/work/<id>`). Recorded values win; never re-derive from
   cwd. Stop here.
2. No workspace (or fields absent): `git rev-parse --show-toplevel` → that
   repo. Fails → child dirs with `.git`: one → use it and say so; several →
   ASK (decision-protocol §3); none → ask for the path.
3. Repo set: `${CLAUDE_PLUGIN_ROOT}/scripts/list-repos.sh <repos-folder>`;
   show the list and confirm. An exclusion is the user's call, recorded in
   the scope contract's out-of-scope table with the reason (scope-affecting).
4. Record via
   `${CLAUDE_PLUGIN_ROOT}/scripts/new-task.sh <task-id> <workspace-root> <pipeline> <work-repo> <repo-set>`
   (paths land absolutised).

**Paths**
- Repo-level files always prefixed: `<work-repo>/.conventions.md`, never bare.
- Task files: `<workspace-root>/work/<task-id>/…`.
- git, test runners, and code greps run with the target repo as cwd.

**Analysis covers every repo in `<repo-set>`**
- Enumerate first and record the list (STATUS `repos-analyzed` + notes).
- Search every repo; record the command per repo. Zero hits is reported as
  "searched, no references found" with the command — never omitted.
- Cite `<repo>:<path>:<line>`, never bare `file:line`.
- Read each repo's own `.conventions.md` / `.domain-glossary.md`; the same
  term meaning different things in two repos is a finding to raise.

**Writing is confined to `<changed-repos>`**
- It grows only through an approved scope-contract change; analysis finding
  that a sibling must change is a finding for the gate, not a licence to edit.
- Multi-repo task: ONE workspace and STATUS.md; each impl-doc step names one
  repo, and its verification and rollback run there; each changed repo gets
  its own branch (named by its conventions), commits, and conventions;
  branches recorded per repo; the impl doc states deploy ORDER and whether
  the intermediate state is acceptable.
- Repos outside `<changed-repos>` are read-only: no code, no `work/`, no
  branch. Exception: /repo-profile writes that repo's own `.conventions.md`.
