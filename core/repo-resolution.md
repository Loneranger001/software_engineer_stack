# Repo resolution — rules

Where every stack skill reads and writes. Resolve BEFORE touching files; none
of these is "the current directory". Why each rule exists, and the failure it
prevents: `<root>/core/repo-resolution-rationale.md` — read
it only when a case here is ambiguous.

**Names**
- `<work-repo>` — repo the task changes (holds `.git`).
- `<workspace-root>` — directory holding `work/<task-id>/` and the one domain
  glossary, `work/domain-glossary.md`: the folder holding the repos in a
  multi-repo workspace, else the repo itself — always what
  `ses workspace-root <work-repo>` prints
  (`$SES_WORKSPACE_ROOT` pins it).
- `<repos-folder>` — folder the repos sit in (parent of `<work-repo>` when
  repos are siblings; otherwise ask).
- `<repo-set>` — ANALYSIS scope: every repo under `<repos-folder>`.
- `<changed-repos>` — WRITE scope: starts as `[<work-repo>]`.
- repo rules — a repo's own rules files (AGENTS.md, CLAUDE.md,
  CODING_STANDARDS.md, CONTRIBUTING.md, Copilot instructions, …), exactly as
  `ses repo-rules <repo> [changed files]` lists
  them. Follow them. Precedence: nested AGENTS.md nearest the file > the
  repo's root rules > the surrounding file's style (for what the rules leave
  open) > framework `standards/`. Never restyle untouched lines to satisfy a
  rule. Two rules files that contradict each other are an open question,
  never a silent pick.

**Resolve**
1. Workspace exists — `<workspace-root>/work/<id>/STATUS.md` (a workspace
   created before this rule may sit in `<work-repo>/work/`; look there too) →
   `ses status show <ws>`
   (`work-repo`, `workspace-root`, `repos-analyzed`; `<ws>` =
   `<workspace-root>/work/<id>`). Recorded values win; never re-derive from
   cwd. Stop here.
2. No workspace (or fields absent): `git rev-parse --show-toplevel` → that
   repo. Fails → child dirs with `.git`: one → use it and say so; several →
   ASK (decision-protocol §3); none → ask for the path.
3. Repo set: `ses list-repos <repos-folder>`;
   show the list and confirm. An exclusion is the user's call, recorded in
   the scope contract's out-of-scope table with the reason (scope-affecting).
4. Record via
   `ses new-task <task-id> auto <pipeline> <work-repo> <repo-set>`
   (`auto` = the workspace-root rule above; paths land absolutised).
   Exit 3 = that task id already has a workspace for another work-repo or
   pipeline, or under another root: show the user its message and ask —
   same task → resume it (step 1), different task → a new id. Never pick.

**Paths**
- Glossary: `<workspace-root>/work/domain-glossary.md`, never bare — one for
  every repo and task, like `work/` never in git, holding ONLY terms whose
  meaning holds in every repo. A legacy `<repo>/.domain-glossary.md` met
  along the way: its global entries move in, repo-specific ones don't; tell
  the user, whose call the old file is.
- Task files: `<ws>/…`, where `<ws>` = `<workspace-root>/work/<task-id>`; a
  workspace-relative name like `evidence/` or `scope-contract.md` always
  means `<ws>/evidence/`, `<ws>/scope-contract.md` — never relative to cwd.
- git, test runners, and code greps run with the target repo as cwd.

**Analysis covers every repo in `<repo-set>`**
- Enumerate first and record the list (STATUS `repos-analyzed` + notes).
- Search every repo with `ses search --ws <ws>
  [--ref origin/<mainline>] -- <patterns>`: counts first, one command and
  sha recorded per repo, zero hits reported as "searched, no references
  found" — never omitted. Open only the files that matter (`git grep -n …
  -- <path>`). A recorded search row may be reused while that repo's sha is
  unchanged; re-search only repos whose sha moved.
- Cite `<repo>:<path>:<line>`, never bare `file:line`.
- Read each repo's own repo rules. A term meaning different things in two
  repos stays out of the glossary — the task defines it per repo — and the
  difference is a finding to raise.

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
