# Estate profile checklist

Run before reporting the platform capability inventory as complete.

- [ ] Repo set enumerated with list-repos.sh, shown to the user, and confirmed — any excluded repo recorded with the user's reason
- [ ] scan-integrations.sh (or the equivalent hand-run greps) covered EVERY repo in the confirmed set, and the commands/patterns are recorded in the file
- [ ] Every `in-use` row cites at least one `<repo>:<file>:<line>`
- [ ] Every row with a status other than `in-use` cites a person and a date — no status was upgraded from scan evidence alone
- [ ] Every `absent` row records the search that found nothing AND the user's confirmation that the estate lacks it
- [ ] §8 negative list is filled — the user was asked directly what is forbidden or effectively impossible
- [ ] §7 procurement path has an approver and a lead time for each new-capability type, so "cannot" can be restated as a costed trade-off
- [ ] §3 reference patterns each point at a real, current working example
- [ ] §2 "can we change it?" answered per system — inferred entries left blank rather than guessed
- [ ] No credentials, connect strings, or secret values anywhere in the file (secret STORES named, secrets not)
- [ ] Sections not confirmed by the user remain visible placeholders — nothing in §5–§8 filled by inference
- [ ] Unanswered questions are in §9 with what they block, and the user was told those capabilities count as unavailable until answered
- [ ] Pre-existing file was MERGED, not overwritten — every user hand-edit and confirmed status survived
- [ ] File written to the absolute `<estate-root>` path, and that path was reported to the user
- [ ] Header records profile date + repos scanned; refresh guidance stated
- [ ] STATUS.md updated with `platform-capabilities:` if a task workspace exists
- [ ] Applicable lessons from knowledge/lessons.md were loaded and considered
