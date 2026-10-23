# Functional design checklist

Run before presenting the FDD for approval.

- [ ] Functional level throughout: no code, SQL, pseudocode, DDL, data types, commit points, or error codes; every step passes the litmus test (a business reader follows it; two implementations could both satisfy it)
- [ ] `ses fdd-lint` passes — any `--allow` kinds are the ones recorded in `fdd-lint-allow` for a prescribed format, nothing more
- [ ] `ses prose-lint` passes, and every sentence follows `<root>/standards/writing.md`: facts about the system, never about how the document was made (no research, task, scope contract, or stage names); no coined noun stacks or slashes; one term for one meaning
- [ ] **In short** opens the document: four to eight plain sentences a reader can stop after — no IDs, no table or column names — current with the body
- [ ] Every FR# lands in at least one §5 step and one §14 scenario (no orphans either way)
- [ ] Attached forward mode: every in-scope S# is the source of at least one FR#, every A# appears in §14, and no FR# lacks an S# (nothing designed outside the contract)
- [ ] Change mode: base and head SHAs pinned in the workspace; every changed file in the review-diff plan is reflected in the FDD; new/changed steps marked; departures from the contract/TDD raised as Q#, not smoothed over
- [ ] Forward and change modes: "Before and after this change" (under In short) filled with concrete rows a stakeholder can picture
- [ ] Developer-only detail (component Inputs tables, Appendix A) sits inside `technical:start/end` markers, and the rendered audience view reads cleanly without it
- [ ] Steps are in business words: each names its rule (BR#) and failure path (EX#) in a few words that agree with §6 and §9; table and column names and code values sit in §7
- [ ] Each business rule stated in full once, in §6; multi-condition rules have a decision table
- [ ] Every failure path found in the code (as-built) or required (forward) has an EX# with who is informed and the business recovery
- [ ] Every existing table, column, and code value named was confirmed against the schema; proposed ones are marked `new` and collide with no existing name
- [ ] Actors, triggers, consumers, and interfaces come from the code and the cross-repo search, with "no other consumer" backed by the search that found none
- [ ] Flow diagram is business-level and matches the traced flow (as-built) or the research call graph plus the change (forward)
- [ ] Every statement about existing behaviour has an Appendix A row with a source reference
- [ ] §1 lists every business term relied on: global ones with their `Meaning` line copied verbatim from `<workspace-root>/work/domain-glossary.md` (none re-defined), repo-specific ones defined for their repo
- [ ] No section dropped — "None" stated explicitly where nothing applies
- [ ] Open Q# items answered, or explicitly deferred by the user and recorded in §13
- [ ] doc-fact-checker ran on the FDD and its findings were resolved at the functional level
- [ ] ASSUMPTIONS.md reviewed — open entries presented for ratification (decision-protocol §4)
- [ ] Handoff summary written last and `ses handoff check` passes
- [ ] Stakeholders get the `ses fdd-view` rendering for the recorded audience, never `fdd.md` itself
- [ ] Approval recorded only after the user's explicit approval (`fdd` field when attached, `approval=approved` when standalone), with the date in the FDD header
