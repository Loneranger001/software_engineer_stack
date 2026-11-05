# Deliver checklist

Run before declaring the task delivered.

- [ ] ASSUMPTIONS.md has no open entries — all ratified, corrected, or resolved-by-user (decision-protocol §4); nothing ships on an unratified guess
- [ ] scope-auditor ran on the final diff + artifacts, its report is kept, and `ses review require <ws> scope-auditor delivery` passes (violations resolved or user-waived in writing); how it ran was told to the user
- [ ] Release notes produced from template, including deployment and rollback sections usable stand-alone
- [ ] `ses prose-lint` passes on the release notes — written to `<root>/standards/writing.md`, about the system rather than the task
- [ ] `ses prose-lint` passes on fdd.md and tdd.md after the consistency sweep; an FDD goes out as its `ses fdd-view` rendering, never fdd.md itself
- [ ] `ses coverage` exits 0: every TDD §7 row (A#, TS#, G#) → T# → recorded PASS, or waived by the user row by row (`waiver.<ID>`) — waived rows named in the release notes as not verified
- [ ] All task documents are internally consistent (TDD ↔ impl-doc ↔ actual diff; stale sections updated)
- [ ] Requested output formats produced (docx/pdf/Confluence) and files open/render correctly
- [ ] PARKED.md items summarized in release notes as follow-ups
- [ ] `ses checkpoint verify --delivery` passes (no empty branch, no task commit without evidence lines, no task commit in a repo outside the changed ones)
- [ ] Work branch pushed in every changed repo; commits reference the task id; task worktrees removed (`ses worktree remove`)
- [ ] Multi-repo changes: release notes state the deploy order across repos and the intermediate state between deployments
- [ ] Ready to record `deliver=done` with /retro as the next action (§4 step 3, right after this checklist)
- [ ] User prompted to run /retro
