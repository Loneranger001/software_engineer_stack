# Deliver checklist

Run before declaring the task delivered.

- [ ] ASSUMPTIONS.md has no open entries — all ratified, corrected, or resolved-by-user (decision-protocol §4); nothing ships on an unratified guess
- [ ] scope-auditor agent ran on the final diff + artifacts and reported PASS (violations resolved or user-waived in writing)
- [ ] Release notes produced from template, including deployment and rollback sections usable stand-alone
- [ ] `ses prose-lint` passes on the release notes — written to `<root>/standards/writing.md`, about the system rather than the task
- [ ] `ses prose-lint` passes on fdd.md and tdd.md after the consistency sweep; an FDD goes out as its `ses fdd-view` rendering, never fdd.md itself
- [ ] Evidence bundle complete: every TDD §7 row (A#, TS#, G#) → T# → evidence file → PASS
- [ ] All task documents are internally consistent (TDD ↔ impl-doc ↔ actual diff; stale sections updated)
- [ ] Requested output formats produced (docx/pdf/Confluence) and files open/render correctly
- [ ] PARKED.md items summarized in release notes as follow-ups
- [ ] Work branch pushed in every changed repo; commits reference the task id
- [ ] Multi-repo changes: release notes state the deploy order across repos and the intermediate state between deployments
- [ ] Ready to record `deliver=done` with /retro as the next action (§4 step 3, right after this checklist)
- [ ] User prompted to run /retro
