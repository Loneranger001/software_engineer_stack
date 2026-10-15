# software-engineer-stack

An end-to-end software engineering lifecycle framework for PL/SQL, SQL, KSH,
and Python codebases: brief → research → technical design → implementation
plan → verified code → audited delivery, plus fast paths for change requests
and documentation. The same `skills/` run in Claude Code, GitHub Copilot and
Codex. Full docs: README.md.

## How any agent uses it

1. Every framework script runs as `ses <command>` (`bin/ses`; `ses help`
   lists them) and every framework file is `<root>/…`, where `<root>` is what
   `ses root` prints. Never construct paths to the framework by guessing.
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
   non-zero when a gate is not met). Checkpoint commits carry the step record
   and evidence hashes. Conversation history and in-session progress are the
   harness's job.
5. The reviewers in `agents/` (scope-auditor, code-reviewer,
   doc-fact-checker) run as subagents where the harness has them — the
   Claude Code plugin ships them; `ses install copilot|codex` installs
   wrappers — and as separate fresh passes held to their report formats
   everywhere else.
6. Framework changes: edit `skills/`, `agents/`, `templates/`,
   `checklists/`, `core/`, `standards/`, `scripts/`, `bin/`; CI and
   `.githooks/pre-commit` run `scripts/check_knowledge.py` and the tests in
   `tests/`. Nothing is generated.
