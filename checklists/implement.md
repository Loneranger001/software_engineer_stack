# Implement checklist

Run before marking the implement stage done.

- [ ] All impl-doc steps executed in order, each with its verification captured to evidence/
- [ ] Work happened on the task branch with checkpoint commits (one per step or logical unit)
- [ ] /verify-code ran for every changed file, in live mode where the environment was reachable; fallback mode is recorded in the evidence when not
- [ ] All tests in the impl-doc test plan pass; failures are fixed or explicitly accepted by the user
- [ ] Every acceptance criterion has PASS evidence (criterion → evidence file mapping exists)
- [ ] Diff reviewed against the scope contract: every changed file maps to an in-scope item
- [ ] Out-of-scope discoveries went to PARKED.md, not into the diff
- [ ] code-reviewer agent ran on every changed repo's branch (via `ses review-diff`, every review file read) and its findings were resolved or consciously waived
- [ ] New code (new file, object, or unit) follows the repo's rules strictly (its AGENTS.md and linked files per `ses repo-rules` / standards defaults: naming, error handling, logging), whatever the code around it does
- [ ] Changes inside an existing unit follow that unit's own conventions; the rules only fill what it doesn't show
- [ ] Each step's evidence has its Rules check (new vs modified hunks); rule breaches carried by a unit's convention, existing names that break a rule, and the reviewer's PRE-EXISTING list are in PARKED.md
- [ ] No standards finding was waived without the user
- [ ] Commits exist only in repos the scope contract lists as changing; each step's commit is in exactly one repo
- [ ] No secrets, connect strings, or environment-specific paths hardcoded
- [ ] New assumptions made while coding are in ASSUMPTIONS.md (not just in commit messages or memory)
- [ ] `ses status` records `implement=done` and `branch.<repo>` for every changed repo
- [ ] Every checkpoint commit ends with its `Evidence-SHA256` lines (`ses checkpoint trailer`), and `ses checkpoint verify` passes
- [ ] Any resume ran `ses checkpoint resume`; uncommitted work found there was kept or discarded by the user's explicit choice
