# Repo resolution — rules

Where every stack skill reads and writes. Resolve BEFORE touching files; none
of these is "the current directory". Why each rule exists, and the failure it
prevents: `${CLAUDE_PLUGIN_ROOT}/core/repo-resolution-rationale.md` — read
it only when a case here is ambiguous.

**Names**
- `<work-repo>` — repo the task changes (holds `.git` and
  `.domain-glossary.md`).
- `<workspace-root>` — directory holding `work/<task-id>/`: the folder holding
  the repos in a multi-repo workspace, else the repo itself — always what
  `${CLAUDE_PLUGIN_ROOT}/scripts/workspace-root.sh <work-repo>` prints
  (`$SES_WORKSPACE_ROOT` pins it).
- `<repos-folder>` — folder the repos sit in (parent of `<work-repo>` when
  repos are siblings; otherwise ask).
- `<repo-set>` — ANALYSIS scope: every repo under `<repos-folder>`.
- `<changed-repos>` — WRITE scope: starts as `[<work-repo>]`.
- repo rules — a repo's own rules files (AGENTS.md, CLAUDE.md,
  CODING_STANDARDS.md, CONTRIBUTING.md, Copilot instructions, …), exactly as
  `${CLAUDE_PLUGIN_ROOT}/scripts/repo-rules.sh <repo> [changed files]` lists
  them. Follow them. Precedence: nested AGENTS.md nearest the file > the
  repo's root rules > the surrounding file's style (for what the rules leave
  open) > framework `standards/`. Never restyle untouched lines to satisfy a
  rule. Two rules files that contradict each other are an open question,
  never a silent pick.

**Resolve**
1. Workspace exists — `<workspace-root>/work/<id>/STATUS.md` (a workspace
   created before this rule may sit in `<work-repo>/work/`; look there too) →
   `${CLAUDE_PLUGIN_ROOT}/scripts/status.py show <ws>`
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
   `${CLAUDE_PLUGIN_ROOT}/scripts/new-task.sh <task-id> auto <pipeline> <work-repo> <repo-set>`
   (`auto` = the workspace-root rule above; paths land absolutised).

**Paths**
- Repo-level files always prefixed: `<work-repo>/.domain-glossary.md`, never
  bare.
- Task files: `<workspace-root>/work/<task-id>/…`.
- git, test runners, and code greps run with the target repo as cwd.

**Analysis covers every repo in `<repo-set>`**
- Enumerate first and record the list (STATUS `repos-analyzed` + notes).
- Search every repo; record the command per repo. Zero hits is reported as
  "searched, no references found" with the command — never omitted.
- Cite `<repo>:<path>:<line>`, never bare `file:line`.
- Read each repo's own repo rules and `.domain-glossary.md`; the same term
  meaning different things in two repos is a finding to raise.

**Writing is confined to `<changed-repos>`**
- It grows only through an approved scope-contract change; analysis finding
  that a sibling must change is a finding for the gate, not a licence to edit.
- Multi-repo task: ONE workspace and STATUS.md; each impl-doc step names one
  repo, and its verification and rollback run there; each changed repo gets
  its own branch (named per its repo rules), commits, and rules;
  branches recorded per repo; the impl doc states deploy ORDER and whether
  the intermediate state is acceptable.
- Repos outside `<changed-repos>` are read-only: no code, no `work/`, no
  branch.
