# Software Engineer Stack

A Claude Code skill framework covering the full software engineering lifecycle for codebases spanning **PL/SQL, SQL, KSH, and Python**. It turns a solution design document or requirement brief into researched, designed, implemented, verified, and packaged deliverables — while staying **accurate, fault-tolerant, self-improving, and scope-disciplined**.

## The lifecycle

```mermaid
flowchart LR
    A[/intake/] -->|scope contract approved| B[/research/]
    B --> C[/tech-design/]
    C -->|TDD approved| G[/grill/]
    G -->|design survived interrogation| D[/impl-plan/]
    D -->|impl doc approved| E[/implement/]
    E --> F[/deliver/]
    F --> G[/retro/]

    CR[/change-request/] -.fast path.-> F
    DOC[/document/] -.standalone.-> F
```

| Command | What it does | Gate |
|---|---|---|
| `/intake <brief>` | Parse a solution design / requirement brief into a requirements summary and a **scope contract** | User approves scope contract |
| `/research` | Investigate the codebase and external sources; every finding carries a source reference | Checklist |
| `/tech-design` | Produce a technical design document traceable to requirements and research | User approves TDD |
| `/grill` | Adversarial interrogation of the TDD: concrete edge-case scenarios per category (data, lifecycle, interface, temporal, environment, security/ops); gaps fixed from evidence, the rest grilled out of you until answered or explicitly deferred | Zero open questions |
| `/impl-plan` | Produce an implementation document: ordered steps, test plan, rollback plan | User approves impl doc |
| `/implement` | Execute the impl doc step by step on a branch, verifying each step | Code review + verification evidence |
| `/deliver` | Scope audit, evidence bundle, release notes, Word/PDF/Confluence conversion | Scope auditor passes |
| `/change-request <desc>` | Fast path for small changes: impact analysis → mini scope contract → change → verify → deliver | Inline approvals |
| `/document <type> <target>` | Produce a how-to, KB article, or understanding document for an existing interface | Fact-checker passes |
| `/repo-profile` | Scan a work repo: conventions into `.conventions.md`, core business entities seeded into `.domain-glossary.md` | — |
| `/verify-code <files>` | Run per-language verification (live DB/host where available, static fallback) | — |
| `/retro` | Capture lessons from a finished task into the framework's knowledge base | User approves framework edits |

## Installation

Option A — install as a plugin (recommended):

```sh
claude plugin marketplace add <this-repo-url-or-path>
claude plugin install software-engineer-stack
```

Option B — clone next to your work repos and add it to a session with `claude --add-dir /path/to/software_engineer_stack`, or symlink `skills/` into your project's `.claude/skills/`.

Then open Claude Code **inside the work repo** you're changing and run the commands above. New here? Read the [narrated walkthrough](docs/walkthrough.md) of a full task first.

## Using with GitHub Copilot

The canonical skills are harness-neutral; a generator produces the Copilot
layer (never edit generated files — edit `skills/` and regenerate):

```sh
# install the adapter into a work repo
python3 scripts/build_copilot.py --target /path/to/your/work-repo
```

This writes `.github/prompts/<stage>.prompt.md` (invoke as `/intake`,
`/implement`, … in Copilot Chat — enable prompt files in VS Code settings and
prefer **agent mode**) and `.github/copilot-instructions.md` (the shared
rules: decision protocol, scope discipline, conventions, verification). Path
references point back at this repo, so keep it checked out at a stable
location. Copilot has no subagents — the review procedures in `agents/` run
inline as separate fresh passes.

A root `AGENTS.md` is also generated for any other AGENTS.md-aware tool
(opencode, Copilot coding agent, etc.): it explains the lifecycle and how to
execute the stage instructions directly.

## Task workspaces

Every engagement (task, change request, doc request) lives in its own workspace directory, `work/<task-id>/`, created by `/intake` (or `scripts/new-task.sh`):

```
work/PROJ-123/
├── STATUS.md          # stage, gate states, next action — the resume point
├── scope-contract.md  # approved at intake; the single source of scope truth
├── research-notes.md
├── tdd.md
├── impl-doc.md
├── evidence/          # captured run outputs, test results, before/after
├── ASSUMPTIONS.md     # proceed-and-log decisions awaiting gate ratification
├── PARKED.md          # out-of-scope findings logged, never acted on
└── deliverables/      # converted docx / pdf / Confluence outputs
```

`STATUS.md` is the resume point: if a session dies mid-stage, rerun the same command and the skill picks up from the recorded state. Add `work/` to the work repo's `.gitignore` if workspaces shouldn't be committed there.

## The four guarantees

- **Accurate** — every factual claim in a generated document must carry a source reference (`file:line`, doc section, or captured run output). Code is verified by running it (`/verify-code`), the `doc-fact-checker` agent re-verifies documents against the code before a stage closes, and `/grill` attacks the design's *completeness* — the edge cases nobody wrote down — before implementation is planned.
- **Fault-tolerant** — stages are idempotent and resumable via `STATUS.md`; implementation happens on a branch with checkpoint commits; every impl doc has a rollback section.
- **Self-improving** — `/retro` appends structured lessons to `knowledge/lessons.md`; every skill loads applicable lessons before starting. Retro can also propose edits to templates/checklists, applied only with your approval. Each work repo additionally accumulates a `.domain-glossary.md` — business terms ("purchase order", "approved") mapped to their system reality (tables, states, code paths, confirmed semantics) — so a term explained once is never re-asked.
- **Scope-disciplined** — `/intake` produces a scope contract you approve; every later skill re-reads it. Anything discovered out of scope goes to `PARKED.md`, never into the change. The `scope-auditor` agent gates `/deliver`.

## When the agent doesn't know

Every skill follows the shared [decision protocol](core/decision-protocol.md).
The short version:

1. **Checkable facts get checked** — if reading code or running a query can
   answer it, that happens; confidence estimates are reserved for genuine
   judgment calls.
2. **Proceed + log** (no interruption) only when the call is ~90%+ confident
   AND cheaply reversible AND inside the scope contract AND touches nothing
   dangerous (data changes, external contracts, prod). The assumption is
   recorded in the workspace's `ASSUMPTIONS.md` with its basis, impact-if-wrong,
   and reversal step.
3. **Stop and ask** for everything else — genuinely unknown, irreversible or
   high blast-radius (regardless of confidence), scope-affecting, or
   user-reserved. Blocking questions ask immediately; the rest batch at stage
   boundaries.
4. **Every approval gate ratifies open assumptions** — you see what was
   assumed before you sign off, and nothing is delivered on an unratified
   guess (the scope auditor enforces it).
5. `/retro` reviews corrected assumptions as calibration feedback, so
   over-confidence turns into lessons.

## Environment configuration for live verification

Connection details are **never stored in this framework**. Verification recipes read them from the environment of the machine you run Claude Code on:

| Variable | Used for | Example |
|---|---|---|
| `SES_DB_CONN` | `sqlplus`/`sql` (SQLcl) connect string for the dev schema | `scott@//devdb:1521/DEVPDB` (password via wallet or prompt) |
| `SES_KSH_HOST` | Optional ssh host for running KSH scripts | `devuser@unixdev01` |
| `SES_PY` | Python interpreter for the work repo | `~/.venvs/proj/bin/python` |

If a variable is unset or the environment is unreachable, `/verify-code` falls back to static checks and says so in the evidence file.

## Repository layout

```
skills/       one directory per lifecycle command (SKILL.md each)
agents/       scope-auditor, code-reviewer, doc-fact-checker (read-only reviewers)
templates/    canonical Markdown templates for every document type
standards/    default coding standards per language (a repo's .conventions.md overrides them)
checklists/   per-stage quality gates
knowledge/    lessons.md (self-improvement memory), decisions.md (framework decision log)
docs/         QA.md (design Q&A + testing guide), walkthrough.md (narrated example task)
scripts/      new-task.sh, md2docx.sh, md2pdf.sh, md2confluence.sh
examples/     sample work repo + a fully worked example task workspace
```

## Document conversion

Deliverables are authored in Markdown and converted on `/deliver`:

```sh
scripts/md2docx.sh work/PROJ-123/tdd.md          # → deliverables/tdd.docx
scripts/md2pdf.sh  work/PROJ-123/tdd.md          # → deliverables/tdd.pdf
scripts/md2confluence.sh work/PROJ-123/tdd.md    # → deliverables/tdd.confluence.txt
```

The scripts require [pandoc](https://pandoc.org) (and a LaTeX engine for PDF); they print install instructions if it's missing.
