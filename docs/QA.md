# Q&A — design decisions and how-tos

Questions asked (and answered) while this framework was designed and built.
Each answer is condensed; the linked file is authoritative.

## 1. What happens when the agent hits something it doesn't know — ~90% confident vs genuinely unknown?

Governed by the shared [decision protocol](../core/decision-protocol.md), which every skill loads. Three outcomes:

- **Check it** — anything answerable by reading code / running a query MUST be checked; confidence estimates are reserved for genuine judgment calls.
- **Proceed + log** — only when ALL hold: ~90%+ confidence with citable basis, cheaply reversible, inside the scope contract, no dangerous surface (data changes, external contracts, prod). Recorded in the workspace `ASSUMPTIONS.md` with basis, impact-if-wrong, and reversal step.
- **Stop and ask** — everything else, *regardless of confidence* (a 95%-confident guess about a DELETE predicate still stops). Blocking questions ask immediately; the rest batch at stage boundaries.

Every approval gate ratifies open assumptions; the scope auditor blocks delivery on unratified ones; `/retro` uses corrected assumptions as calibration feedback.

## 2. Can the framework be used outside Claude Code (GitHub Copilot, opencode, …)?

Yes. The fastest route is the plugin: `copilot plugin install ./copilot` (see #15). Beyond that, canonical content stays in `skills/` (harness-neutral bodies; subagent steps carry an inline fallback) and [`scripts/build_copilot.py`](../scripts/build_copilot.py) generates the Copilot layer into any work repo: `.github/skills/<stage>/SKILL.md` (the stages as agent skills — model-invoked, or run as `/intake`, `/implement`, … in VS Code chat), `.github/agents/<name>.agent.md` (the three reviewers as native Copilot custom agents), and `.github/copilot-instructions.md`. A root `AGENTS.md` is generated for any AGENTS.md-aware tool (opencode, Copilot cloud agent). Generated files are marker-protected and regeneration is idempotent — edit `skills/` or `agents/`, regenerate, never edit generated files. (Copilot's SDK also offers programmatic custom agents and fleet-mode orchestration; this framework's sequential, human-gated pipeline doesn't need fleet orchestration — the reviewers are its only isolation points.)

## 3. How does the skill-based framework work — and why skills instead of an orchestrator driving role-specific agents?

It's **instructions and state on disk, executed by one agent session**: skills are staged instruction sets; the `work/<id>/` workspace (STATUS.md, scope contract, evidence) is the shared state; templates/checklists/lessons are data the skills reference and `/retro` evolves.

Orchestrator topologies pay off for parallel, decomposable, human-free work. This lifecycle is the opposite: strictly sequential with five human approval gates — **the user is the orchestrator**, STATUS.md is the dispatch table. Agent-to-agent handoffs lose context; here handoffs travel through full documents that are *also the deliverables*, so coordination costs nothing extra. State on disk beats state in an orchestrator process for fault tolerance and portability. Separate agents are used only where isolation is a feature: the three read-only reviewers (`agents/`), which judge the work without inheriting the author's assumptions. Continuity of context for producing; isolation of context for judging.

## 4. Do the TDD / how-to / other document types follow defined templates?

Yes — nine templates in [`templates/`](../templates), one per document type (scope contract, research notes, TDD, impl doc, test evidence, KB article, how-to, understanding doc, release notes). Skills copy the template and fill every section; the stage checklists verify the load-bearing parts; the doc-fact-checker flags any claim without a source reference; `/retro` is the sanctioned way to evolve a template.

## 5. When code-reviewer.md reviews code, where does its output go?

To the `/implement` run that launched it (review gate, [`skills/implement/SKILL.md`](../skills/implement/SKILL.md) §4). Its report (`VERDICT: APPROVE | FINDINGS` with `[SEV-1/2/3] file:line`) blocks the stage: SEV-1/2 loop back into fix → re-verify → checkpoint-commit; non-trivial waivers need the user. The implement checklist enforces closure before `STATUS.md` flips to done. Known gap: the report itself isn't yet persisted to `evidence/` — the fixes are traceable in commits.

## 6. What is `${CLAUDE_PLUGIN_ROOT}` and why does it matter for Copilot?

Claude Code's plugin-root variable: at runtime it resolves to wherever the plugin is installed, letting skills reference sibling files (`templates/`, `checklists/`, …) from any work repo without hardcoded paths. Copilot doesn't know the variable, so `build_copilot.py` substitutes it at generation time — `.` inside the framework repo, the framework checkout's absolute path when generating into a work repo. Consequences: keep the framework checkout at a stable path, and regenerate per machine (a teammate's clone would contain your paths).

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
claude                          # or open in VS Code with the Copilot adapter generated
/intake ../sample-brief.md DEMO-1
# approve the scope contract, then walk the pipeline:
/research → /tech-design → /grill → /impl-plan → /implement → /deliver → /retro
```

Watch for: STATUS.md gates advancing, open questions surfacing at intake (the sample brief is ambiguous on purpose), the grill producing scenarios about reruns/currency edge cases, evidence files landing, and the scope auditor at deliver. Then try the fast path: `/change-request "return distinct exit code when extract file is empty" CR-1`.

**Mechanical checks** (seconds, no session):

```sh
sh -n scripts/*.sh                                   # script syntax
scripts/new-task.sh T1 /tmp/x full                   # workspace scaffold + STATUS.md
python3 scripts/build_copilot.py && python3 scripts/build_copilot.py  # idempotent, no ${CLAUDE_PLUGIN_ROOT} leakage
scripts/md2docx.sh examples/sample-brief.md          # needs pandoc; prints install hint otherwise
```

With a dev Oracle/Unix environment available, set `SES_DB_CONN` / `SES_KSH_HOST` / `SES_PY` and re-run `/verify-code` on the sample repo to exercise live mode.

## 12. How does build_copilot.py work?

It's a compiler from the canonical framework to Copilot's file conventions ([source](../scripts/build_copilot.py)). Pipeline per run:

1. **Resolve the layout.** The stack root defaults to the script's parent repo; the target defaults to the stack root, or a work repo via `--target`. That fixes where generated files point back at the framework: `.` inside the framework repo, the checkout's absolute path for a work repo, `.github/se-stack` with `--self-contained`, `<plugin-root>` in the `copilot/` plugin. The layout also knows that the plugin and the self-contained bundle ship the reviewers only as `<name>.agent.md` custom agents, and that the bundle keeps skill support files under `.github/skills/` rather than next to the data, so a skill's "run the procedure in `agents/scope-auditor.md`" is rewritten to the file that actually exists there.
2. **Preflight.** Every output path is checked before anything is written; one existing file without the generator marker (e.g. a team's own `copilot-instructions.md`) stops the run with nothing changed.
3. **Skills → agent skills.** Each `skills/*/SKILL.md` becomes `<target>/.github/skills/<name>/SKILL.md`: frontmatter kept (`name`, `description`, and `argument-hint` / `user-invocable` / `disable-model-invocation` where set), `${CLAUDE_PLUGIN_ROOT}` substituted per the layout, support files (`explain.md`, `assets/`) copied alongside with the same substitution. A generated skill directory is rebuilt whole, so a support file dropped upstream disappears too.
4. **Agents → custom agents.** Each `agents/*.md` becomes `<target>/.github/agents/<name>.agent.md`, with its `tools` list mapped to Copilot's tool aliases (`Read` → `read`, `Grep`/`Glob` → `search`, `Bash` → `execute`). Without a `tools` line a Copilot custom agent gets every tool, edit included — the mapping is what makes the reviewers read-only in fact, not just in their instructions.
5. **Shared context.** `<target>/.github/copilot-instructions.md` (the always-on rules: decision protocol, scope discipline, conventions precedence, verification, when to delegate to the custom agents), `AGENTS.md` at the stack root, and the `copilot/` plugin folder are regenerated.
6. **Pruning.** Generated skills and agents whose canonical source is gone are deleted, and so is every generated prompt file (retired output, see #13). Only marker-carrying files are touched.
7. **Check mode.** `--check` rebuilds into a scratch copy with the committed output removed first, then diffs — so stale, missing, and orphaned generated files all fail CI and the pre-commit hook. Regeneration is idempotent (two runs produce byte-identical output).
8. **Knowledge merge.** The bundled `knowledge/` copies (`copilot/knowledge/`, and `.github/se-stack/knowledge/` in self-contained mode) are the one part of the generated output that is *not* disposable: `/retro` appends lessons and decisions there, so a rebuild merges any entries the install copy has and the canonical `knowledge/` doesn't back on top of the fresh copy, rather than replacing the file. Entries are compared whitespace-insensitively, so re-runs never duplicate; multi-line entries and extra files you add to `knowledge/` are preserved too. One consequence of append-only merging: pruning an entry from the canonical `knowledge/` (a `/retro` §4 curation pass) does not propagate — delete the install copy's file and rebuild to push a deletion through. This protects rebuilds, not plugin reinstalls: `copilot plugin install` replaces its cached copy wholesale, so upstream lessons from an installed plugin before reinstalling.

## 13. What happened to the prompt files?

Earlier versions generated `.github/prompts/<stage>.prompt.md` — a compiled copy of each skill, for explicit `/intake`-style invocation in Copilot Chat — because Copilot then only loaded skills when a request matched their description. That reason is gone: VS Code chat lists agent skills as slash commands (with the skill's `argument-hint` in the input box), and prompt files are deprecated in VS Code's Copilot harness. Generating both put every stage in the picker twice, so the generator now emits skills only. Regenerating a work repo deletes the prompt files an earlier version wrote (they carry the generator marker) and leaves any hand-written prompt files alone.

Nothing "calls into" `skills/` at runtime either way — a generated skill is a **compiled copy**: the same instructions with `${CLAUDE_PLUGIN_ROOT}` pre-substituted, *referencing* the framework's data files (templates, checklists, the decision protocol), which the agent reads from disk while executing. So **skills/ is the only place you edit** — after changing a skill, re-run `python3 scripts/build_copilot.py` (per target repo) or Copilot keeps executing the old instructions; the marker protection means you can't accidentally fork behavior by editing a generated file directly.

## 14. Does GitHub Copilot support SKILLs the way Claude Code does?

Yes — same file convention. Copilot's agent skills are `<dir>/SKILL.md` with `name` + `description` frontmatter and an instruction body — exactly this framework's format. VS Code, Copilot CLI, the Copilot app and the cloud agent discover repo skills from `.github/skills/`, `.claude/skills/`, or `.agents/skills/` (personal skills from `~/.copilot/skills`; also `copilot skill add <dir>` and `/skills reload`); the Copilot SDK loads via `skillDirectories`. Remaining differences from Claude Code: **discovery** — this framework's canonical `skills/` root isn't one of Copilot's discovery paths; **path resolution** — Copilot injects skill bodies verbatim, so `${CLAUDE_PLUGIN_ROOT}` would not resolve (each canonical skill carries a path note telling any harness how to resolve it). The generator handles both: it emits `.github/skills/<stage>/SKILL.md` copies with paths pre-substituted, and the `copilot/` plugin folder (#15) makes the whole framework installable in one command. Invocation is no longer a difference: VS Code chat runs skills as `/name` commands.

## 15. Copilot supports plugins — what does that change?

Copilot's [plugin system](https://docs.github.com/en/copilot/concepts/agents/about-plugins) bundles skills + custom agents + hooks + MCP config in one installable unit, and works in Copilot CLI, VS Code and the Copilot app. Install the committed [`copilot/`](../copilot/) folder — `copilot plugin install ./copilot`, or `copilot plugin install OWNER/REPO:copilot` straight from GitHub — never the repository root. Copilot's manifest search does find the root's `.claude-plugin/plugin.json`, but that is the Claude Code flavor: its skills keep unresolved `${CLAUDE_PLUGIN_ROOT}` paths, and its reviewers aren't `NAME.agent.md` files, so they don't load as custom agents. The `copilot/` folder is generated and self-contained: manifest at root, skills with paths rewritten to a `<plugin-root>` convention, `.agent.md` reviewers with read-only tool lists, bundled templates/checklists/protocol/scripts. One compatibility trap when maintaining the manifests: never add a `skills` field to `plugin.json` — Copilot defaults without it, and Claude Code rejects manifests that have it. Practical notes: plugin components are cached and a reinstall replaces the cached copy wholesale (re-run the install after updates; upstream `/retro` lessons first); the Copilot cloud agent enables plugins declaratively via `enabledPlugins` in the work repo's `.github/copilot/settings.json`. Consumption tiers: plugin install → generated `.github/` adapter (repo-scoped, no install) → `AGENTS.md` (everything else).

## 16. How do I resume work I left midway, in a different session?

Open a new session in the same work repo and run the stage command you were in — or just say "resume PROJ-123". Every skill's first step is reading `work/<task-id>/STATUS.md` (stage table, gate states, a **Next action** line) and continuing from there; nothing important lives in the chat session by design. Forgot where you were? `cat work/<id>/STATUS.md`. Forgot the task id? `ls work/`.

Each stage also resumes *within* itself: `/intake` picks up at the first unfinished step and never re-asks answered questions; `/research` continues from the first empty section of the notes; `/grill` skips already-verdicted scenarios in `grill-log.md` and resumes the interview at the first unanswered row; `/implement` reads the branch's checkpoint commits (`<task-id> step N: …`), verifies the last step's evidence, and continues at step N+1 — a dead session costs at most one step; `/deliver` re-runs idempotently. What does NOT carry over is conversational nuance that never got written down — deliberately: the gates force everything decision-relevant into the workspace files (scope contract, ASSUMPTIONS.md, TDD, PARKED.md). If it matters, it's in the workspace. This works across harnesses too — start a task in Claude Code, resume it from Copilot CLI: both read the same files.

## 17. I see two `/intake` commands in VS Code — why?

The same stage is registered twice, from two sources. Most common: you **installed the `copilot/` plugin AND generated the `.github/` adapter** into the workspace — the plugin registers skills at user level, the workspace adds its own. The tiers are alternatives, not layers: pick one per machine (`copilot plugin uninstall software-engineer-stack`, or remove the workspace's generated `.github/` pieces). The other cause is an adapter generated by an older version, which wrote `.github/prompts/intake.prompt.md` next to `.github/skills/intake/SKILL.md` — regenerate and the prompt files are removed (#13). Diagnose by hovering the entries in the picker — the detail line shows each one's source. Either duplicate is harmless to invoke (identical instructions underneath).

## 18. The generated `.github/` skills reference templates in the framework checkout — intentional?

Yes — that's the generator's **default mode**: a thin adapter whose data references point back at the framework checkout by absolute path. Deliberate benefits: no duplicated files, one canonical copy of templates/checklists, and one shared `knowledge/` so `/retro` lessons accumulate in the git-tracked framework repo. The cost: the checkout must stay at a stable path. If you want the workspace to stand alone, re-run with **`--self-contained`** — it bundles templates, checklists, protocol, standards, scripts, and knowledge into `.github/se-stack/` and points every reference there (bundled `knowledge/` is then a per-workspace copy to sync back). Rule of thumb: default mode on your main machine (shared lessons memory wins); self-contained when the workspace must work without the checkout.

## 19. Where does the `work/` folder get created?

In the **folder holding your repos** when the workspace has several (`workspace-root-folder/work/<task-id>/`), and inside the repo only for a standalone repo — resolved by [`scripts/workspace-root.sh`](../scripts/workspace-root.sh) per [repo-resolution](../core/repo-resolution.md), never the framework checkout and not blindly the session's current directory. A task often spans repos, so its workspace (STATUS.md, scope contract, ASSUMPTIONS.md, evidence/, deliverables/, PARKED.md) sits beside them rather than inside one: no repo looks like the owner, no repo's `git status` fills with task files, and no repo needs a `work/` gitignore entry. Set `SES_WORKSPACE_ROOT` to pin a different location; the choice is recorded in STATUS.md and every later stage finds it there. Note that a workspace outside any repo is not versioned — keep it backed up, or make the parent folder its own repository if you want task history in git. Evidence integrity does not depend on that: each checkpoint commit records the SHA-256 of the evidence it rests on, and `scripts/checkpoint.py verify` (run at `/deliver`) fails on any recorded evidence file that is missing or altered — git proves what the evidence was even when it cannot store it. Workspaces created earlier inside a repo keep working (STATUS.md records their root); to move one, move the directory and run `scripts/status.py field <ws> workspace-root <new-root>`.

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

- **`<repo-set>`** — the ANALYSIS scope: every repo under the workspace folder, enumerated by [`scripts/list-repos.sh`](../scripts/list-repos.sh) and recorded in STATUS.md under *Repos analyzed*. Impact analysis, caller/dependent searches, call graphs and dependency maps run across all of it.
- **`<changed-repos>`** — the WRITE scope: the subset the scope contract lists as changeable. Starts as the primary repo; grows only through an approved contract amendment.

Analysis is workspace-wide because the repos are siblings for a reason — one calls another's package, consumes its extract, or reads its tables. The failure being prevented is a silent one: a search that never visited repo-c reports "3 callers" with exactly the same confidence as a search that did, and the reader cannot tell the two apart. So `/research` §1 and `/change-request` §1 run each search in **every** repo and record the command per repo *including the repos that returned nothing* ("searched, no references found"). Findings are cited `<repo>:<path>:<line>` — bare `file:line` stops being unique the moment two repos are in play. `/understand` maps dependencies the same way and groups its diagram nodes by repo.

Writing stays narrow because analysis scope is not permission. Discovering that a sibling repo must change is a finding for the next gate, not a licence to edit it — the scope-auditor treats commits in an analysis-only repo as a violation. When a change legitimately spans repos, the task stays single (one workspace, one contract, one STATUS.md) while the mechanics go per repo: a branch each (named per that repo's rules files), impl-doc steps that each name their repo, per-repo verification with that repo's tooling, code review per repo against its own rules files, and rollback per repo in reverse dependency order. The impl doc must also state the **deploy order** and what the window between deployments looks like — a consumer released before its producer is an outage, and the plan either avoids it or declares it acceptable.

On the fast path, `/change-request` escalates to the full pipeline when changes land in more than one repo: coordinated branches plus a deploy order is not a small change, whatever the diff size suggests.

Two things stay per-repo throughout, and that is deliberate: the repo's rules files and `.domain-glossary.md`. Code written in repo-b follows repo-b's rules, and a term that means different things in two repos is a finding worth raising rather than smoothing over.
