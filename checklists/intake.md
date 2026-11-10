# Intake checklist

Run before presenting the scope contract for approval.

- [ ] The full brief was read (all pages/sections; converted from docx/pdf if needed)
- [ ] Every requirement in the brief appears as an in-scope item, an exclusion, or an open question — nothing silently dropped
- [ ] Every in-scope item is concrete and checkable (a reviewer could say yes/no to "is this done?")
- [ ] Every in-scope item has at least one acceptance criterion, and every criterion says HOW it will be verified
- [ ] Out-of-scope section lists adjacent work a reader would otherwise assume included
- [ ] Ambiguities are recorded as open questions, not resolved by silent assumption
- [ ] Every business term the brief leans on is in the Business terms table — linked to its glossary entry or marked `research target` — and on the summary's `- Terms:` line; a term used differently from its glossary entry is a Q#
- [ ] Affected interfaces/objects listed reflect the brief plus a first scan of EVERY repo in the analysis scope, each row naming its repo
- [ ] Contract's Repos section is filled: which repos are analyzed, which may change, each one's mainline, and any repo excluded with the user's reason
- [ ] Every repo's mainline is recorded (`mainline.<repo>`) and confirmed by the user — never one name assumed for all; the first scan used `ses search --ref mainline`
- [ ] Applicable lessons were loaded (`ses lessons intake --ws <ws>` once the workspace exists) and considered
- [ ] ASSUMPTIONS.md reviewed — every open entry presented for ratification at this gate (decision-protocol §4)
- [ ] `intake=approved` is set (`ses status`) only after the user's explicit approval — not before
- [ ] Handoff summary written last and `ses handoff check` passes (every ID in the body is in the summary; contract version current)
