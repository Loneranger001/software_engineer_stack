# Q&A — design decisions and how-tos

Questions asked (and answered) while this framework was designed and built.
Each answer is condensed; the linked file is authoritative.

## 1. What happens when the agent hits something it doesn't know — ~90% confident vs genuinely unknown?

Governed by the shared [decision protocol](../core/decision-protocol.md), which every skill loads. Three outcomes:

- **Check it** — anything answerable by reading code / running a query MUST be checked; confidence estimates are reserved for genuine judgment calls.
- **Proceed + log** — only when ALL hold: ~90%+ confidence with citable basis, cheaply reversible, inside the scope contract, no dangerous surface (data changes, external contracts, prod). Recorded in the workspace `ASSUMPTIONS.md` with basis, impact-if-wrong, and reversal step.
- **Stop and ask** — everything else, *regardless of confidence* (a 95%-confident guess about a DELETE predicate still stops). Blocking questions ask immediately; the rest batch at stage boundaries.

Every approval gate ratifies open assumptions; the scope auditor blocks delivery on unratified ones; `/retro` uses corrected assumptions as calibration feedback.

## 2. Can the framework be used outside Claude Code (GitHub Copilot, Codex, …)?

Yes — the repository is one plugin in three formats, and the same `skills/` and `agents/` run unchanged in Claude Code, GitHub Copilot and Codex. Nothing is generated per harness. Claude Code reads `.claude-plugin/`; Copilot reads the root `plugin.json` (the open Agent Plugins 1.0 format: `skills/`, plus Copilot's reviewer files in `com.github.copilot/agents/`) and our `.claude-plugin/marketplace.json`; Codex reads `.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json`. Install is two commands per harness (README → Installation). Instructions never name a harness-specific path: every script runs as `ses <command>` and every framework file is `<root>/…` (#6, #12). Reviewers run apart from the authoring session per `core/reviewers.md`: the plugin's agents (Claude Code, Copilot; Codex after `ses setup codex`), else a fresh subagent, else a separate fresh pass. Any AGENTS.md-aware tool can also follow the root `AGENTS.md` directly.

## 3. How does the skill-based framework work — and why skills instead of an orchestrator driving role-specific agents?

It's **instructions and state on disk, executed by one agent session**: skills are staged instruction sets; the `work/<id>/` workspace (STATUS.md, scope contract, evidence) is the shared state; templates/checklists/lessons are data the skills reference and `/retro` evolves.

Orchestrator topologies pay off for parallel, decomposable, human-free work. This lifecycle is the opposite: strictly sequential with five human approval gates — **the user is the orchestrator**, STATUS.md is the dispatch table. Agent-to-agent handoffs lose context; here handoffs travel through full documents that are *also the deliverables*, so coordination costs nothing extra. State on disk beats state in an orchestrator process for fault tolerance and portability. Separate agents are used only where isolation is a feature: the three read-only reviewers (`agents/`), which judge the work without inheriting the author's assumptions. Continuity of context for producing; isolation of context for judging.

## 4. Do the TDD / how-to / other document types follow defined templates?

Yes — nine templates in [`templates/`](../templates), one per document type (scope contract, research notes, TDD, impl doc, test evidence, KB article, how-to, understanding doc, release notes). Skills copy the template and fill every section; the stage checklists verify the load-bearing parts; the doc-fact-checker flags any claim without a source reference; `/retro` is the sanctioned way to evolve a template.

## 5. When code-reviewer.md reviews code, where does its output go?

To the `/implement` run that launched it (review gate, [`skills/implement/SKILL.md`](../skills/implement/SKILL.md) §4). Its report (`VERDICT: APPROVE | FINDINGS` with `[SEV-1/2/3] file:line`) blocks the stage: SEV-1/2 loop back into fix → re-verify → checkpoint-commit; non-trivial waivers need the user. The implement checklist enforces closure before `STATUS.md` flips to done. Known gap: the report itself isn't yet persisted to `evidence/` — the fixes are traceable in commits.

## 6. What is `<root>`, and what happened to `${CLAUDE_PLUGIN_ROOT}`?

`<root>` is the framework directory — wherever it is installed — as printed by `ses root`. Each skill opens with a note telling the agent to run `ses root` once and read `<root>/templates/…`, `<root>/core/…` from there. Up to 0.6 the skills used `${CLAUDE_PLUGIN_ROOT}`, which only Claude Code substitutes; every other harness needed a generated copy with the path baked in (four copies of every skill, and none for Codex). `ses` finds its own root by resolving its real path, so it works from a plugin cache, a checkout, or a symlink in `~/.local/bin` — and the same SKILL.md is correct everywhere. Claude Code puts the plugin's `bin/` on PATH; Copilot and Codex don't, so each skill falls back to `python3 <skill-dir>/../../bin/ses` — every harness tells the model which file a skill was loaded from (Codex lists each skill with its path), and the path resolves through symlinks. If neither works the skill stops and asks rather than guessing. `tests/test_skill_flow.py` fails on any `${CLAUDE_PLUGIN_ROOT}` or `scripts/x.py` path in an instruction file, and on any `ses <command>` that doesn't exist.

## 7. Does tdd.md include diagrams? Were more sections needed?

Now yes (v0.2.1): §3 carries an **as-is** mermaid flow and §4 a **to-be** flow — both must be drawn from the research call graph, and the doc-fact-checker verifies diagrams against real call order. Also added: **§7 Verification approach** (every acceptance criterion mapped to a test type before design approval — an untestable criterion blocks the TDD) and **§8 Operational impact** (schedule, restartability, file handoffs, monitoring, run duration — explicit "none" required). Deliberately not added: deployment steps (impl-doc owns them), assumptions (ASSUMPTIONS.md covers it).

## 8. If research can't answer everything, does the framework grill the user? How is edge-case completeness ensured?

Since v0.3, yes — the [`/grill`](../skills/grill/SKILL.md) stage runs between tech-design and impl-plan (impl-plan refuses to start without `grill: done` or an explicit waiver). Phase 1 self-grills the TDD with concrete scenarios per mandatory category (data, lifecycle, interface, temporal, environment, security/ops) using the task's real objects: covered scenarios must cite the design, evidence-resolvable gaps are fixed into the TDD on the spot, the rest become questions. Phase 2 interviews the user with those questions — concrete scenarios with proposed defaults, theme by theme, follow-ups included — until each is answered (landed in the TDD) or explicitly deferred (verbatim into TDD §11 Risks). `grill-log.md` records the full scenario table as completeness evidence. Inspired by mattpocock's grill-with-docs / domain-modeling skills.

## 9. Where does AGENTS.md go for GitHub Copilot?

At the **root of the repo you're working in** (next to `.git`), not inside `.github/`. VS Code Copilot Chat agent mode reads the workspace root's `AGENTS.md` (`chat.useAgentsMdFile`, on by default); the Copilot coding agent reads the repo root too (nested ones supported, closest wins). `.github/copilot-instructions.md` is the one that lives under `.github/`; when both exist their contents are combined.

## 10. How does the framework make sense of business terms — e.g. "purchase order must be approved"?

Three passes plus a persistent memory. `/intake` builds a **term inventory** from the brief and looks each term up in the work repo's `.domain-glossary.md`; unknown terms become research targets, and a term the brief uses differently from its entry is always an open question. `/research` **grounds** unresolved terms in checkable facts (decision-protocol §1): what a purchase order *is* — tables, state values, the proc whose execution *is* "approval" — read from the code with `file:line` evidence, never imagined; pure business semantics (approval limits, who may approve) stay questions for you. `/grill` challenges any term the brief bends or that's still unconfirmed. Every resolution is written to `.domain-glossary.md` ([template](../templates/domain-glossary.md)) marked `from-code` or `user-confirmed` — so next month's brief mentioning "purchase order" gets the answer from the glossary instead of re-asking you. The doc-fact-checker flags documents that contradict confirmed entries; hand-edits win.

## 11. How do I test the framework?

Two layers:

**End-to-end dry run** (the real test) — no live DB needed; it exercises the static-fallback path:

```sh
cd examples/sample-repo
claude                          # or copilot / codex, with the plugin installed
/intake ../sample-brief.md DEMO-1
# approve the scope contract, then walk the pipeline:
/research → /tech-design → /grill → /impl-plan → /implement → /deliver → /retro
```

Watch for: STATUS.md gates advancing, open questions surfacing at intake (the sample brief is ambiguous on purpose), the grill producing scenarios about reruns/currency edge cases, evidence files landing, and the scope auditor at deliver. Then try the fast path: `/change-request "return distinct exit code when extract file is empty" CR-1`.

**Mechanical checks** (seconds, no session):

```sh
python3 -m unittest discover -s tests                # scripts, ses, skill wiring, examples
python3 scripts/check_knowledge.py                   # decisions log + lesson format
bin/ses new-task T1 /tmp/x full                      # workspace scaffold + STATUS.md
bin/ses setup codex --skills --home /tmp/h --dry-run # what a no-plugin setup would link/write
claude plugin validate .                             # Claude Code plugin + marketplace manifests
bin/ses md2docx examples/sample-brief.md             # needs pandoc; prints install hint otherwise
```

With a dev Oracle/Unix environment available, set `SES_DB_CONN` / `SES_KSH_HOST` / `SES_PY` and re-run `/verify-code` on the sample repo to exercise live mode.

## 12. How does `ses` work?

It is one ~220-line Python file ([`bin/ses`](../bin/ses)) with two jobs. **Dispatch**: `ses <command> [args]` maps a short name to a script in `scripts/` (`status` → `status.py`, `search` → `xsearch.py`, `review-diff` → `review-diff.sh`, …) and `exec`s it, so exit codes pass straight through — `ses status require` still exits 3 when a gate is not met. `ses root` prints the framework directory. **Setup** (optional): `ses setup <claude|copilot|codex>` links `ses` into `~/.local/bin`; for Codex it also writes the reviewers as `~/.codex/agents/<name>.toml` with a read-only sandbox, because Codex plugins can't ship agents. `--skills` additionally links the skills and reviewers into the harness's user folders (`~/.claude/skills`, `~/.copilot/skills`, `~/.agents/skills`) for use without the plugin system. It refuses to replace anything it did not create, `--dry-run` shows the plan, and `--remove` deletes only its own links and files (the shared `ses` link last).

## 13. What happened to the prompt files and the generated `.github/` copies?

Removed in 0.7, together with `scripts/build_copilot.py` and the `copilot/` plugin folder. They existed only because Copilot could not resolve `${CLAUDE_PLUGIN_ROOT}`; with `ses` (#6) the canonical skills work as-is, and current VS Code lists agent skills as slash commands, so separate prompt files bought nothing. If you generated an adapter into a work repo with an older version, its files carry the line `generated by software-engineer-stack scripts/build_copilot.py` — delete those files (`grep -rl` for that line under `.github/`), then install the plugin (README → Installation). `ses repo-rules` and `ses review-diff` still recognise and skip such files, so a leftover never gets mistaken for the repo's own rules.

## 14. Does GitHub Copilot support SKILLs the way Claude Code does?

Yes — same file convention: `<dir>/SKILL.md` with `name` + `description` frontmatter and an instruction body. Copilot discovers plugin skills, personal skills in `~/.copilot/skills` and `~/.agents/skills`, and repo skills in `.github/skills/`, `.claude/skills/` or `.agents/skills/`; it loads a skill when a request matches its description, and VS Code also lists skills as slash commands. Codex uses the same format, discovering `~/.agents/skills` and `.agents/skills` up to the repo root (it follows symlinks). The one thing neither substitutes is `${CLAUDE_PLUGIN_ROOT}` — which is why the skills now reach the framework through `ses` instead (#6). Frontmatter beyond `name`/`description` (`argument-hint`, `user-invocable`) is a Claude Code extension; the other harnesses work from `name` and `description`.

## 15. How does one repository install as a plugin in three harnesses?

Each harness reads its own manifest and ignores the others'. **Claude Code**: `.claude-plugin/plugin.json` + `marketplace.json`; it loads `skills/`, the reviewers from `agents/`, and puts `bin/` on PATH. **Copilot**: a root `plugin.json` that declares the open [Agent Plugins 1.0](https://github.com/agentplugins/agent-plugins-spec) schema, which takes precedence over `.claude-plugin/plugin.json`; skills load from `skills/` and Copilot-specific agents from `com.github.copilot/agents/`. Both harnesses name an agent after its file — Copilot expects `NAME.agent.md`, which Claude Code would call `NAME.agent` — so the three reviewers exist twice — `agents/` is canonical, and a test fails if a Copilot copy drifts (real files, not symlinks, so no loader can skip them). Copilot also accepts the Claude Code tool names in the reviewers' `tools:` line (`Read`, `Grep`, `Glob`, `Bash` are documented aliases). Copilot's marketplace lookup includes `.claude-plugin/marketplace.json`, so one marketplace file serves both. **Codex**: `.codex-plugin/plugin.json` (`"skills": "./skills/"`) and a marketplace at `.agents/plugins/marketplace.json` whose plugin source is the repository root. Codex plugins can't bundle agents yet (openai/codex #18988, #28491), hence the optional `ses setup codex`. All three installs were tested with the real CLIs; `tests/test_plugin_manifests.py` keeps the manifests' name, version and description in step.

## 16. How do I resume work I left midway, in a different session?

Open a new session — in any harness — and run the stage command you were in, or just say "resume PROJ-123". Every skill starts from the task workspace: `ses status show <ws>` (gates, repos, branches, a **Next action** line), the stage documents' handoff summaries, and for `/implement` the branch's checkpoint commits. Forgot where you were? `cat work/<id>/STATUS.md` — it is a dozen lines on purpose. Forgot the task id? `ls work/`.

The split is deliberate. **The harness owns the session**: conversation history, its own resume (`claude --resume`, `codex resume`, `copilot --resume`), compaction, and in-session progress tracking (todo/plan tools). **The workspace owns the task**: what was approved and when (gate lines with date and note), what is in scope (the contract), what was assumed (ASSUMPTIONS.md), what was built and proven (checkpoint commits carrying evidence hashes). Harness state is per machine, per harness, and compaction drops detail without telling you; the workspace is readable by every harness and every person, and it is what the scope auditor checks. So nothing about the task is kept only in chat, and nothing that git or a stage document already records is duplicated into STATUS.md (no log, no step counter).

Each stage also resumes *within* itself: `/intake` picks up at the first unfinished step and never re-asks answered questions; `/research` continues from the first empty section of the notes; `/grill` skips already-verdicted scenarios in `grill-log.md` and resumes the interview at the first unanswered row; `/implement` runs `ses checkpoint resume` (last `<task-id> step N` commit, branch check, uncommitted files classified), verifies the last step's evidence, and continues at step N+1 — a dead session costs at most one step; `/deliver` re-runs idempotently. Start a task in Claude Code, resume it in Codex or Copilot: all three read the same files.

## 17. I see two `/intake` commands — why?

The same skill is registered from two sources. Usual causes: the plugin **and** `ses setup <harness> --skills` on the same harness (pick one; `ses setup <harness> --remove` undoes the links); or a leftover adapter generated by an older version into the work repo's `.github/` (delete it, #13). Copilot also reads `~/.agents/skills`, so `ses setup codex --skills` is visible to Copilot too — Copilot keeps the first skill of each name, so that one shows once. Invoking either duplicate is harmless — same instructions underneath — but remove it.

## 18. Where do `/retro` lessons go, and why not into the framework's `knowledge/`?

Into your own lessons file, `${SES_HOME:-~/.ses}/lessons.md`, through `ses lessons --add` (which rejects a line whose tags the stage filter couldn't match). An installed framework is replaceable: Claude Code installs a marketplace plugin into a versioned cache directory and swaps it on update, so a lesson appended there would vanish. `~/.ses/` lives outside every install, survives updates, and is read by every harness on the machine — a lesson learned in Codex is applied in Claude Code the next day. `ses lessons <stage>` reads both your file and the framework's `knowledge/lessons.md` (the shipped, curated set). A lesson every user should get is promoted into the framework checkout's `knowledge/lessons.md` and committed there; framework edits (`skills/`, `templates/`, …) likewise go into your checkout, never into an installed copy (`skills/retro/SKILL.md` §3).

## 19. Where does the `work/` folder get created?

In the **folder holding your repos** when the workspace has several (`workspace-root-folder/work/<task-id>/`), and inside the repo only for a standalone repo — resolved by `ses workspace-root` ([script](../scripts/workspace-root.sh)) per [repo-resolution](../core/repo-resolution.md), never the framework checkout and not blindly the session's current directory. A task often spans repos, so its workspace (STATUS.md, scope contract, ASSUMPTIONS.md, evidence/, deliverables/, PARKED.md) sits beside them rather than inside one: no repo looks like the owner, no repo's `git status` fills with task files, and no repo needs a `work/` gitignore entry. Set `SES_WORKSPACE_ROOT` to pin a different location; the choice is recorded in STATUS.md and every later stage finds it there. Workspaces are never committed anywhere — when `work/` would land inside a repository, `ses new-task` excludes it locally through `.git/info/exclude` (README → Keeping `work/` out of git) — so back the folder up if you need its history. Evidence integrity does not depend on that: each checkpoint commit records the SHA-256 of the evidence it rests on, and `ses checkpoint verify` (run at `/deliver`) fails on any recorded evidence file that is missing or altered — git proves what the evidence was even when it cannot store it. Workspaces created earlier inside a repo keep working (STATUS.md records their root); to move one, move the directory and run `ses status field <ws> workspace-root <new-root>`.

## 20. Should each stage run in its own session, or all of them in one?

Either works — the framework is session-agnostic by construction (#16), and nothing breaks whichever you pick. If you want a rule of thumb: **one session per gate**, with a genuinely fresh session before `/grill` and `/impl-plan`.

**Why separate sessions are slightly better.** A fresh session is a free audit of your own documents. `/impl-plan` already demands the impl doc be executable by "some session with no memory of this conversation" — the same standard applies upstream, and a cold start is the only way to test it. If a fresh `/tech-design` has to re-ask something you settled during `/intake`, that gap is a real defect in the scope contract, and you want it surfaced at the design gate rather than after `/deliver` hands the work to someone else. Staying in one session hides that failure mode: the agent still remembers the conversational nuance that never got written down, so an under-documented contract looks fine right up until someone resumes cold. `/grill` is the strongest case for a clean break — it interrogates the TDD adversarially, and the context that just *wrote* the TDD is anchored on its own reasoning, so it grills its own assumptions least hard. Isolation of context for judging, continuity for producing (#3), applied to your own sessions.

**A workable grouping:** `/intake` → `/research` together (research targets come straight out of the intake Q&A); `/tech-design` either way; `/grill` **fresh**; `/impl-plan` **fresh**; `/implement` in its own session (long and context-heavy, resumable mid-way from checkpoint commits); `/deliver` → `/retro` together. `/clear` mid-session gives the same fresh-context effect as a new session.

One caveat: the audit value only exists if you honor the gates. If you approve a scope contract without reading it, a fresh session downstream just re-asks the same questions and the benefit turns into friction.

## 21. My VS Code workspace root is a parent folder holding several repos — is that supported? Whose coding rules apply?

Supported — it is the layout the framework is built around. Coding rules are **per repo**: each repo's own rules files (`AGENTS.md`, `CODING_STANDARDS.md`, `CONTRIBUTING.md`, Copilot instructions, nested `AGENTS.md` near the code — listed by [`scripts/repo-rules.sh`](../scripts/repo-rules.sh)) govern code in that repo and override the framework defaults in `standards/`. Four repos can have four different sets, so nothing is merged across them; `.domain-glossary.md` is per-repo for the same reason. Task state, by contrast, belongs to the workspace: `work/` sits in the parent folder (#19).

What that layout *does* change is which directory counts as "the repo":

```
workspace-root-folder/        ← session cwd, NOT a repo
├── repo-a/  .git  AGENTS.md
├── repo-b/  .git  CODING_STANDARDS.md
├── …
└── work/<task-id>/
```

The rule is [core/repo-resolution.md](../core/repo-resolution.md): `<work-repo>` is the directory containing `.git` (`git rev-parse --show-toplevel`, or — when cwd sits above the repos — the single child repo, else **ask** which one), `<workspace-root>` is the directory holding `work/`, and both are written to `STATUS.md` absolutised by `new-task.sh` so later stages read them instead of re-deriving from their own cwd. Every skill addresses repo-level files with that prefix (`<work-repo>/.domain-glossary.md`) and finds rules files with `repo-rules.sh <work-repo>`, never by a bare filename — from the parent folder, a bare `AGENTS.md` lookup finds nothing (or the wrong file) and the stage silently proceeds without the repo's rules.

Practical guidance: open the parent folder as the window root if that is how you work; expect a "which repo is this task about?" question when a stage has no STATUS.md to read it from, and name the repo when you know it.

## 22. A task's analysis spans all repos in the workspace — how is that handled?

By separating two scopes that used to be one ([core/repo-resolution.md](../core/repo-resolution.md)):

- **`<repo-set>`** — the ANALYSIS scope: every repo under the workspace folder, enumerated by [`scripts/list-repos.sh`](../scripts/list-repos.sh) and recorded in STATUS.md as `repos-analyzed`. Impact analysis, caller/dependent searches, call graphs and dependency maps run across all of it.
- **`<changed-repos>`** — the WRITE scope: the subset the scope contract lists as changeable. Starts as the primary repo; grows only through an approved contract amendment.

Analysis is workspace-wide because the repos are siblings for a reason — one calls another's package, consumes its extract, or reads its tables. The failure being prevented is a silent one: a search that never visited repo-c reports "3 callers" with exactly the same confidence as a search that did, and the reader cannot tell the two apart. So `/research` §1 and `/change-request` §1 run each search in **every** repo and record the command per repo *including the repos that returned nothing* ("searched, no references found"). Findings are cited `<repo>:<path>:<line>` — bare `file:line` stops being unique the moment two repos are in play. `/understand` maps dependencies the same way and groups its diagram nodes by repo.

Writing stays narrow because analysis scope is not permission. Discovering that a sibling repo must change is a finding for the next gate, not a licence to edit it — the scope-auditor treats commits in an analysis-only repo as a violation. When a change legitimately spans repos, the task stays single (one workspace, one contract, one STATUS.md) while the mechanics go per repo: a branch each (named per that repo's rules files), impl-doc steps that each name their repo, per-repo verification with that repo's tooling, code review per repo against its own rules files, and rollback per repo in reverse dependency order. The impl doc must also state the **deploy order** and what the window between deployments looks like — a consumer released before its producer is an outage, and the plan either avoids it or declares it acceptable.

On the fast path, `/change-request` escalates to the full pipeline when changes land in more than one repo: coordinated branches plus a deploy order is not a small change, whatever the diff size suggests.

Two things stay per-repo throughout, and that is deliberate: the repo's rules files and `.domain-glossary.md`. Code written in repo-b follows repo-b's rules, and a term that means different things in two repos is a finding worth raising rather than smoothing over.
