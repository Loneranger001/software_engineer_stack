# Change request checklist

Run before delivering a fast-path change.

- [ ] Impact analysis found ALL callers/dependents of the changed interface (commands/queries used are recorded and reproducible)
- [ ] Mini scope contract (in/out/acceptance) was approved by the user before any code change
- [ ] Change is as small as the request allows — no opportunistic refactoring (that goes to PARKED.md)
- [ ] /verify-code ran on every changed file; live verification where reachable
- [ ] Regression check covers the impacted callers found in the analysis, not just the changed object
- [ ] Every acceptance criterion has PASS evidence in evidence/
- [ ] Diff maps 1:1 to the mini contract; scope-auditor pass on anything larger than a single-file change
- [ ] Conventions respected (.conventions.md / standards defaults)
- [ ] Rollback note written (even for small changes: exact revert/redeploy step)
- [ ] ASSUMPTIONS.md has no open entries — ratified at the mini-contract gate or resolved since (decision-protocol §4)
- [ ] STATUS.md updated through analyze → mini-contract → change → verify → deliver
