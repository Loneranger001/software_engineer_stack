# Implement checklist

Run before marking the implement stage done.

- [ ] All impl-doc steps executed in order, each with its verification captured to evidence/
- [ ] Work happened on the task branch in its own worktree (`ses worktree add`, cut from `origin/<mainline>`; the repo's own checkout untouched), with one checkpoint commit per step (never batched), plus any `step <N>: fix` commits and one `tests:` commit for the test-plan evidence
- [ ] /verify-code ran for every changed file, in live mode where the environment was reachable; fallback mode is recorded in the evidence when not
- [ ] All tests in the impl-doc test plan pass; failures are fixed or explicitly accepted by the user
- [ ] `ses coverage` run after the `tests:` commit: every TDD §7 row (A#, TS#, G#) has a recorded PASS through its T#, or each row it lists (NOT-RUN, PARTIAL, …) is told to the user and kept in the next action for /deliver
- [ ] Diff reviewed against the scope contract: every changed file maps to an in-scope item
- [ ] Out-of-scope discoveries went to PARKED.md, not into the diff
- [ ] code-reviewer agent ran on every changed repo's branch (via `ses review-diff`, every review file read) and its findings were resolved or consciously waived
- [ ] New files follow the repo's rules strictly (its AGENTS.md and linked files per `ses repo-rules` / standards defaults: naming, error handling, logging), whatever existing files do
- [ ] Changes to existing files — new procedures, functions, classes or methods included — follow that file's own conventions; the rules only fill what it doesn't show
- [ ] Each step's evidence has its Rules check (new vs existing files); rule breaches carried by a file's convention, existing names that break a rule, and the reviewer's PRE-EXISTING list are in PARKED.md
- [ ] No standards finding was waived without the user
- [ ] Commits exist only in repos the scope contract lists as changing; each step's commit is in exactly one repo
- [ ] No secrets, connect strings, or environment-specific paths hardcoded
- [ ] New assumptions made while coding are in ASSUMPTIONS.md (not just in commit messages or memory)
- [ ] `ses status` records `branch.<repo>`, `base.<repo>` and `worktree.<repo>` for every changed repo (`implement=done` is set right after this checklist)
- [ ] Every checkpoint commit ends with its `Evidence-SHA256` lines (`ses checkpoint trailer`), and `ses checkpoint verify` passes
- [ ] Any resume ran `ses checkpoint resume`; uncommitted work found there was kept or discarded by the user's explicit choice
