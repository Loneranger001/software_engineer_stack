# Implement checklist

Run before marking the implement stage done.

- [ ] All impl-doc steps executed in order, each with its verification captured to evidence/
- [ ] Work happened on the task branch with checkpoint commits (one per step or logical unit)
- [ ] /verify-code ran for every changed file, in live mode where the environment was reachable; fallback mode is recorded in the evidence when not
- [ ] All tests in the impl-doc test plan pass; failures are fixed or explicitly accepted by the user
- [ ] Every acceptance criterion has PASS evidence (criterion → evidence file mapping exists)
- [ ] Diff reviewed against the scope contract: every changed file maps to an in-scope item
- [ ] Out-of-scope discoveries went to PARKED.md, not into the diff
- [ ] code-reviewer agent ran on every changed repo's branch (via review-diff.sh, every review file read) and its findings were resolved or consciously waived
- [ ] Code follows the conventions of the repo it lives in (its rules files per repo-rules.sh / standards defaults: naming, error handling, logging)
- [ ] Commits exist only in repos the scope contract lists as changing; each step's commit is in exactly one repo
- [ ] No secrets, connect strings, or environment-specific paths hardcoded
- [ ] New assumptions made while coding are in ASSUMPTIONS.md (not just in commit messages or memory)
- [ ] status.py records `implement=done`, `branch.<repo>` and `final-commit.<repo>` for every changed repo
- [ ] Every checkpoint commit ends with its `Evidence-SHA256` lines (`scripts/checkpoint.py trailer`), and `scripts/checkpoint.py verify` passes
- [ ] Any resume ran `scripts/checkpoint.py resume`; uncommitted work found there was kept or discarded by the user's explicit choice
