# Implement checklist

Run before marking the implement stage done.

- [ ] All impl-doc steps executed in order, each with its verification captured to evidence/
- [ ] Work happened on the task branch with checkpoint commits (one per step or logical unit)
- [ ] /verify-code ran for every changed file, in live mode where the environment was reachable; fallback mode is recorded in the evidence when not
- [ ] All tests in the impl-doc test plan pass; failures are fixed or explicitly accepted by the user
- [ ] Every acceptance criterion has PASS evidence (criterion → evidence file mapping exists)
- [ ] Diff reviewed against the scope contract: every changed file maps to an in-scope item
- [ ] Out-of-scope discoveries went to PARKED.md, not into the diff
- [ ] code-reviewer agent ran on the full diff and its findings were resolved or consciously waived
- [ ] Code follows .conventions.md / standards defaults (naming, error handling, logging)
- [ ] No secrets, connect strings, or environment-specific paths hardcoded
- [ ] STATUS.md updated: implement → done, with branch and last commit recorded
