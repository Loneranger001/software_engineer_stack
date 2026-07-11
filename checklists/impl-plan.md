# Implementation plan checklist

Run before presenting the implementation document for approval.

- [ ] Every design section of the approved TDD is covered by at least one implementation step
- [ ] Steps are ordered so the system stays consistent between steps (no step leaves a broken intermediate state without saying so)
- [ ] Each step is commit-sized and has its OWN verification and rollback note
- [ ] Test plan covers every acceptance criterion in the scope contract (map T# → A#)
- [ ] Test plan includes regression checks for existing behaviour touched by the change
- [ ] Deployment steps are executable by someone other than the author (exact commands, environments)
- [ ] Whole-change rollback plan exists and does not depend on memory ("redeploy previous" names the previous version)
- [ ] Evidence capture points are defined (which files land in evidence/)
- [ ] No step implements anything outside the scope contract
- [ ] STATUS.md updated: impl-plan → awaiting approval
