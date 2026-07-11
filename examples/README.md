# Examples

Two things live here:

- **sample-repo/** — a miniature work repo in the framework's four languages
  (PL/SQL package, SQL DDL, KSH batch wrapper, Python reconciliation tool).
  Use it to try the framework end-to-end without touching a real repo:
  open Claude Code in `sample-repo/`, then run
  `/intake ../sample-brief.md DEMO-1` and follow the pipeline.
- **sample-brief.md** — a requirement brief for a small enhancement to the
  sample repo, written the way such briefs typically arrive (slightly
  ambiguous on purpose — intake should surface the ambiguities as open
  questions rather than assume).
- **sample-task/** — a snapshot of a task workspace mid-pipeline (intake and
  research done, tech-design next), showing what the artifacts look like
  filled in: STATUS.md, an approved scope contract, and PARKED.md with a
  real-shaped entry.

The sample repo has no live database; verification there exercises the
static-fallback path (and `ksh -n`/`py_compile` where those tools exist).
