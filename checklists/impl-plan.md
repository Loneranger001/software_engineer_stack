# Implementation plan checklist

Run before presenting the implementation document for approval.

- [ ] Every design section of the approved TDD is covered by at least one implementation step
- [ ] Steps are ordered so the system stays consistent between steps (no step leaves a broken intermediate state without saying so)
- [ ] Each step is commit-sized and has its OWN verification and rollback note
- [ ] Test plan covers every acceptance criterion in the scope contract and every TDD §7 G# row from /grill (map T# → A# / G#)
- [ ] Test plan includes regression checks for existing behaviour touched by the change
- [ ] Deployment steps are executable by someone other than the author (exact commands, environments)
- [ ] Whole-change rollback plan exists and does not depend on memory ("redeploy previous" names the previous version)
- [ ] Evidence capture points are defined (which files land in evidence/)
- [ ] No step implements anything outside the scope contract
- [ ] ASSUMPTIONS.md reviewed — every open entry presented for ratification at this gate (decision-protocol §4)
- [ ] `impl-plan=approved` is set (`ses status`) only after the user's explicit approval
- [ ] Handoff summary written last and `ses handoff check` passes (every ID in the body is in the summary; contract version current)
