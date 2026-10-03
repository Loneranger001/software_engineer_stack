# Architecture checklist

Run before presenting the architecture for approval.

- [ ] Platform inventory was read — or the document header records the user's decision to proceed UNGROUNDED, with who and when
- [ ] Every §5 mechanism cites a platform inventory row with status `in-use` or `available` — none `deprecated`, `requires-approval`, `forbidden`, `absent`, or unlisted
- [ ] Every mechanism outside the usable set appears ONLY in §9, marked REQUIRES NEW PLATFORM CAPABILITY, with the approval path and lead time
- [ ] Where no usable mechanism fitted a row, the user was asked and the choice is recorded in §8 — no mechanism was chosen silently
- [ ] Reference patterns from the platform inventory were preferred where they fit, and are cited
- [ ] Every edge in the §2 diagram is a §5 row, and every §5 row is an edge; §4 flow steps each name their integration
- [ ] No §5 row has a blank "Failure & recovery posture"
- [ ] Altitude held: no table/column names, DDL, signatures, class names, pseudocode, or file layouts (existing interfaces only NAMED, as citations)
- [ ] Every claim in §3–§7 is tagged VERIFIED / PROPOSED / EXTERNAL; VERIFIED claims carry a source; PROPOSED claims are not worded as existing behaviour
- [ ] Unconfirmed EXTERNAL claims are in §12 with the team that can answer
- [ ] §6 names exactly one authoritative system per boundary-crossing entity — or the conflict is raised as a finding
- [ ] §10 states every house NFR line, with "n/a" justified rather than implied
- [ ] §13 lists the detail deliberately left to design; §14 covers every §5 row with a work package or marks it out of scope
- [ ] Stress pass: every §5 row has at least one scenario per category (or n/a with reason); no `open` verdict left without an answer, deferral, or acked risk
- [ ] Platform facts learned from the user were offered back to the platform inventory (with who/date), not left only in this document
- [ ] doc-fact-checker ran in architecture mode and its findings were resolved
- [ ] Business terms checked against the domain glossary; mismatches raised as open questions
- [ ] ASSUMPTIONS.md reviewed — open entries presented for ratification (decision-protocol §4)
- [ ] Applicable lessons from knowledge/lessons.md were loaded and considered
- [ ] STATUS.md updated: approve → awaiting approval
