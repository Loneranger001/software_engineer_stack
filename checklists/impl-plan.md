# Implementation plan checklist

Run before presenting the implementation document for approval.

- [ ] Every design section of the approved TDD is covered by at least one implementation step
- [ ] Steps are ordered so the system stays consistent between steps (no step leaves a broken intermediate state without saying so)
- [ ] Each step is commit-sized and has its exact files, its TDD §, and its OWN verification and rollback
- [ ] Test plan covers every TDD §7 row — acceptance criteria (A#), FDD test scenarios (TS#), grill scenarios (G#) — each mapped to a T#
- [ ] Test plan includes regression checks for existing behaviour touched by the change
- [ ] Deployment steps are executable by someone other than the author (exact commands, environments)
- [ ] Whole-change rollback plan exists and does not depend on memory ("redeploy previous" names the previous version), with its "Rehearsed on dev" line for steps with DDL or data changes
- [ ] §1 states the shared test data — which repo's seed or fixture sets up what, and the order the repos' tests run in — or that each repo's tests stand alone
- [ ] No step implements anything outside the scope contract
- [ ] ASSUMPTIONS.md reviewed — every open entry presented for ratification at this gate (decision-protocol §4)
- [ ] `impl-plan=approved` is set (`ses status`) only after the user's explicit approval
- [ ] Terse and agent-only: tables and fragments, no prose, no design restated from the TDD, no handoff summary; preconditions list only task-specific ones
- [ ] `ses handoff check <ws>` passes — the contract and TDD the plan rests on are current
- [ ] `ses impl-check <ws>` passes — every file the test plan, deployment or rollback names is in a step's Files or already in a repo; every step has its own Verify and Rollback; every row is planned
