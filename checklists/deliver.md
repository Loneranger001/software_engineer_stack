# Deliver checklist

Run before declaring the task delivered.

- [ ] ASSUMPTIONS.md has no open entries — all ratified or corrected (decision-protocol §4); nothing ships on an unratified guess
- [ ] scope-auditor agent ran on the final diff + artifacts and reported PASS (violations resolved or user-waived in writing)
- [ ] Release notes produced from template, including deployment and rollback sections usable stand-alone
- [ ] Evidence bundle complete: every acceptance criterion → evidence file → PASS
- [ ] All task documents are internally consistent (TDD ↔ impl-doc ↔ actual diff; stale sections updated)
- [ ] Requested output formats produced (docx/pdf/Confluence) and files open/render correctly
- [ ] PARKED.md items summarized in release notes as follow-ups
- [ ] Work branch pushed in every changed repo; commits reference the task id
- [ ] Multi-repo changes: release notes state the deploy order across repos and the intermediate state between deployments
- [ ] STATUS.md updated: deliver → done; retro is the recorded next action
- [ ] User prompted to run /retro
