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

Yes. Canonical content stays in `skills/` (harness-neutral bodies; subagent steps carry an inline fallback). [`scripts/build_copilot.py`](../scripts/build_copilot.py) generates the Copilot layer into any work repo: `.github/prompts/<stage>.prompt.md` (invoked as `/intake`, `/implement`, … in Copilot Chat agent mode), `.github/agents/<name>.agent.md` (the three reviewers as native Copilot custom agents), and `.github/copilot-instructions.md`. A root `AGENTS.md` is generated for any AGENTS.md-aware tool (opencode, Copilot coding agent). Generated files are marker-protected and regeneration is idempotent — edit `skills/` or `agents/`, regenerate, never edit generated files. (Copilot's SDK also offers programmatic custom agents and fleet-mode orchestration; this framework's sequential, human-gated pipeline doesn't need fleet orchestration — the reviewers are its only isolation points.)

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

Three passes plus a persistent memory. `/intake` builds a **term inventory** from the brief and looks each term up in the work repo's `.domain-glossary.md`; unknown terms become research targets, and a term the brief uses differently from its entry is always an open question. `/research` **grounds** unresolved terms in checkable facts (decision-protocol §1): what a purchase order *is* — tables, state values, the proc whose execution *is* "approval" — read from the code with `file:line` evidence, never imagined; pure business semantics (approval limits, who may approve) stay questions for you. `/grill` challenges any term the brief bends or that's still unconfirmed. Every resolution is written to `.domain-glossary.md` ([template](../templates/domain-glossary.md)) marked `from-code` or `user-confirmed` — so next month's brief mentioning "purchase order" gets the answer from the glossary instead of re-asking you. `/repo-profile` seeds the glossary with the repo's core entities; the doc-fact-checker flags documents that contradict confirmed entries; hand-edits win.

## 11. How do I test the framework?

Two layers:

**End-to-end dry run** (the real test) — no live DB needed; it exercises the static-fallback path:

```sh
cd examples/sample-repo
claude                          # or open in VS Code with the Copilot adapter generated
/repo-profile                   # → .conventions.md
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

It's a ~130-line compiler from the canonical framework to Copilot's file conventions ([source](../scripts/build_copilot.py)). Pipeline per run:

1. **Resolve roots.** The stack root defaults to the script's parent repo; the target defaults to the stack root, or a work repo via `--target`. One decision follows: `root_ref` — how generated files will point back at the framework. Inside the stack repo it's `.` (relative paths); for an external work repo it's the stack checkout's absolute path.
2. **Skills → prompt files.** Each `skills/*/SKILL.md` is parsed (frontmatter + body) and re-emitted as `<target>/.github/prompts/<name>.prompt.md`: Copilot frontmatter (`description` kept, `mode: agent` added, Claude-only keys dropped), every `${CLAUDE_PLUGIN_ROOT}` replaced with `root_ref`, and a header line pointing at the shared decision protocol.
3. **Agents → custom agents.** Each `agents/*.md` becomes `<target>/.github/agents/<name>.agent.md` — a native Copilot custom agent. The `tools` restriction is deliberately omitted (Copilot tool names vary per surface; default is all tools); the read-only constraint is stated in the prompt body instead.
4. **Shared context.** `<target>/.github/copilot-instructions.md` (the always-on rules: decision protocol, scope discipline, conventions precedence, verification, when to delegate to the custom agents) and `AGENTS.md` at the stack root (universal entry point for AGENTS.md-aware tools) are regenerated.
5. **Safety.** Every generated file carries a marker comment; the script refuses to overwrite any existing file without the marker — your hand-written files can never be clobbered. Regeneration is idempotent (running twice produces byte-identical output).

## 13. What are the prompt files for — do they access the SKILLs?

No — nothing "calls into" `skills/` at runtime. A prompt file is a **compiled copy** of a skill: the same instructions, re-packaged for a different loader. `skills/intake/SKILL.md` and `.github/prompts/intake.prompt.md` differ only in frontmatter dialect and path resolution — Claude Code loads the SKILL.md natively and resolves `${CLAUDE_PLUGIN_ROOT}` itself at runtime; Copilot loads the prompt file into the chat context when you type `/intake`, with the framework paths already baked in at generation time. (The prompt file does *reference* the framework's data files — templates, checklists, the decision protocol — which the Copilot agent then reads from disk while executing; it just doesn't read SKILL.md.)

Two practical consequences: **skills/ is the only place you edit** — after changing a skill, re-run `python3 scripts/build_copilot.py` (per target repo) or Copilot keeps executing the old instructions; and the marker protection means you can't accidentally fork behavior by editing a prompt file directly.
