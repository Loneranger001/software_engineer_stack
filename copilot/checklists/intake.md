# Intake checklist

Run before presenting the scope contract for approval.

- [ ] The full brief was read (all pages/sections; converted from docx/pdf if needed)
- [ ] Every requirement in the brief appears as an in-scope item, an exclusion, or an open question — nothing silently dropped
- [ ] Every in-scope item is concrete and checkable (a reviewer could say yes/no to "is this done?")
- [ ] Every in-scope item has at least one acceptance criterion, and every criterion says HOW it will be verified
- [ ] Out-of-scope section lists adjacent work a reader would otherwise assume included
- [ ] Ambiguities are recorded as open questions, not resolved by silent assumption
- [ ] Affected interfaces/objects listed reflect the brief plus a first scan of EVERY repo in the analysis scope, each row naming its repo
- [ ] Contract's Repos section is filled: which repos are analyzed, which may change, and any repo excluded with the user's reason
- [ ] Applicable lessons were loaded (`scripts/lessons.sh intake --repo … --lang …`) and considered
- [ ] ASSUMPTIONS.md reviewed — every open entry presented for ratification at this gate (decision-protocol §4)
- [ ] `intake=approved` is set (status.py) only after the user's explicit approval — not before
- [ ] Handoff summary written last and `scripts/handoff.py check` passes (every ID in the body is in the summary; contract version current)
