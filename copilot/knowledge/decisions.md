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

<!-- /retro appends: - [date] <change> — motivated by <lesson/task> -->
