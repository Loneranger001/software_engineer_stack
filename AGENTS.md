# software-engineer-stack

An end-to-end software engineering lifecycle framework for PL/SQL, SQL, KSH,
and Python codebases: brief → research → technical design → implementation
plan → verified code → audited delivery, plus fast paths for change requests
and documentation, packaged as a GitHub Copilot plugin (Claude Code and Codex
packaging is parked in `parked/`). Full docs: README.md.

## How any agent uses it

1. Every framework script runs as `ses <command>` (`bin/ses`; `ses help`
   lists them) and every framework file is `<root>/…`, where `<root>` is what
   `ses root` prints. Without `ses` on PATH, run `bin/ses` from the plugin
   folder the skill was loaded from. Never construct paths by guessing.
2. Read `<root>/core/decision-protocol.md` first — it governs every unknown
   (check facts; proceed-and-log only narrow, reversible calls; otherwise ask)
   — and `<root>/core/repo-resolution.md`, which fixes where files are read
   and written (`<work-repo>` = the repo holding `.git`; `<workspace-root>` =
   the directory holding `work/`; both recorded in the task's STATUS.md,
   neither assumed to be the current directory).
3. Each lifecycle stage is a self-contained skill. Execute the one matching
   the task:

| Command | Purpose | Instructions |
|---|---|---|
| `/change-request` | Fast path for a small change to an existing interface. | `skills/change-request/SKILL.md` |
| `/deliver` | Scope audit, evidence bundle, release notes, document conversion, branch push. | `skills/deliver/SKILL.md` |
| `/document` | How-to, KB article, or understanding document, verified against the code. | `skills/document/SKILL.md` |
| `/func-design` | Functional design document — what, when, which business rules; no code. | `skills/func-design/SKILL.md` |
| `/grill` | Adversarial interrogation of the TDD before the implementation document. | `skills/grill/SKILL.md` |
| `/impl-plan` | Implementation document from the approved TDD. | `skills/impl-plan/SKILL.md` |
| `/implement` | Execute the impl doc step by step, verified and checkpoint-committed. | `skills/implement/SKILL.md` |
| `/intake` | Start a task from a solution design document or requirement brief. | `skills/intake/SKILL.md` |
| `/meeting-minutes` | Structured minutes from notes or a transcript. | `skills/meeting-minutes/SKILL.md` |
| `/research` | Source-referenced investigation of the codebase and external sources. | `skills/research/SKILL.md` |
| `/retro` | Capture lessons and propose framework improvements. | `skills/retro/SKILL.md` |
| `/tech-design` | Technical design document with full traceability. | `skills/tech-design/SKILL.md` |
| `/understand` | Code-verified working understanding of an existing interface. | `skills/understand/SKILL.md` |
| `/verify-code` | Run PL/SQL, SQL, KSH, or Python against live dev environments. | `skills/verify-code/SKILL.md` |

4. Task state lives in `work/<task-id>/`: the stage documents (each opening
   with a handoff summary), `scope-contract.md` (scope truth),
   `ASSUMPTIONS.md`, `PARKED.md`, `evidence/`, and a minimal `STATUS.md`
   whose gates are checked and set only with `ses status` (`require` exits
   non-zero when a gate is not met). The one domain glossary — only terms whose
   meaning holds in every repo — sits beside them as `work/domain-glossary.md`. Checkpoint
   commits carry the step record and evidence hashes. Conversation history
   and in-session progress are the harness's job.
5. The reviewers in `com.github.copilot/agents/` (scope-auditor,
   code-reviewer, doc-fact-checker) run apart from the authoring session as
   `<root>/core/reviewers.md` describes: the plugin's custom agent, else a
   fresh subagent, else a separate fresh pass held to the report format.
6. Task workspaces never go into git: `ses new-task` excludes `work/`
   locally when it sits inside a repo, commits stage files by name, and
   `ses checkpoint` refuses or fails on workspace files.
7. Framework changes: edit `skills/`, `com.github.copilot/agents/`,
   `templates/`, `checklists/`, `core/`, `standards/`, `scripts/`, `bin/`; a
   release bumps the version in `plugin.json`. CI and `.githooks/pre-commit`
   run `scripts/check_knowledge.py` and the tests in `tests/`. Nothing is
   generated.
