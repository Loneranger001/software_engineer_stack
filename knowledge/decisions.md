# Framework decision log

> Why the framework is the way it is. /retro appends here when a user-approved
> framework edit is applied. Newest first within each section is fine; keep
> entries short — decision, reason, date, motivating task.

## Founding decisions (2026-07-11)

- **Claude Code skill framework** over process-docs-only or a script toolkit:
  the user drives every stage from Claude Code sessions inside work repos, so
  skills give executable process with judgment, while templates/checklists
  keep it auditable.
- **Markdown canonical, convert at delivery** (pandoc → docx/pdf/Confluence):
  documents stay diffable and version-controlled; enterprise formats are a
  rendering concern.
- **Scope contract as a first-class artifact** with user approval at intake,
  re-read by every stage, PARKED.md for out-of-scope findings, and a blocking
  scope-auditor at delivery: "sticks to the defined scope" was a core
  requirement, and prompts alone don't hold scope under pressure — gates do.
- **STATUS.md per task workspace as the resume point** rather than relying on
  session memory: sessions die; the workspace must carry the whole state
  (fault tolerance requirement).
- **Verification is live-first with recorded static fallback** because dev DB
  and Unix hosts are available in the user's environment; evidence files are
  mandatory either way so "tested" is never an unbacked claim.
- **Repo conventions beat framework standards** (`.conventions.md` from
  /repo-profile overrides `standards/`): the user works in existing repos with
  established conventions; the framework must adapt to them, not the reverse.
- **Lessons are append-only one-liners with stage/lang/repo tags**: cheap to
  write at retro time, cheap to filter at skill start; curation is a separate
  user-approved pass so memory can't silently rot or bloat.

## Applied changes

<!-- /retro appends (see skills/retro/SKILL.md §3; checked by scripts/check_knowledge.py):
     - [YYYY-MM-DD] <change> in `<repo-root path>` — motivated by <lesson/task>
     - [YYYY-MM-DD] [pending-upstream] <change> — <where the patch is> -->
- [2026-10-11] Skills load lessons through `scripts/lessons.sh` (stage/lang/repo filter) instead of reading `knowledge/lessons.md` whole, and verification output goes through `scripts/capture.sh` (full log to `evidence/raw/`, bounded summary to context and `templates/test-evidence.md`) — motivated by the token-usage review: both grew without bound per task.
- [2026-10-11] Split repo resolution into a rules card every stage loads (`core/repo-resolution.md`, 380 words, was 1,144) and an on-demand `core/repo-resolution-rationale.md` holding the original reasoning verbatim — every rule kept, ~760 fewer words per stage call; motivated by the token-usage review.
- [2026-10-11] Removed the externally sourced `jira-ops` and `confluence-ops` skills (Copilot-specific tooling, outside the lifecycle's decision protocol); `scripts/build_copilot.py` now prunes generated prompts/skills/agents whose canonical source is gone — motivated by user review of the stack.
- [2026-10-11] Gate checks and stage transitions go through `scripts/status.py` (deterministic `require`, atomic `set`) in every lifecycle skill; `scripts/check_knowledge.py` and `scripts/build_copilot.py --check` run in CI and pre-commit; `skills/retro/SKILL.md` now edits only the canonical repo and records file paths — motivated by the two 2026-08-12 entries below having been recorded as applied while neither edit existed in any skill.
- [2026-08-12] Added a mandatory cross-repository, refreshed-main research preflight and a missing-conventions profiling requirement in `skills/research/SKILL.md` — motivated by MFCS-4684 missing RAIL_PRICE dependencies until /grill. (Re-applied 2026-10-11: the original edit was made in an install copy and lost on rebuild.)
- [2026-08-12] Added a `commit-msg` hook preflight to `skills/implement/SKILL.md` — motivated by MFCS-4684's initial commit-message rejection. (Re-applied 2026-10-11, same cause.)
