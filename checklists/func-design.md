# Functional design checklist

Run before presenting the FDD for approval.

- [ ] Functional level throughout: no code, SQL, pseudocode, DDL, data types, commit points, or error codes; every step passes the litmus test (a business reader follows it; two implementations could both satisfy it)
- [ ] `ses fdd-lint` passes — any `--allow` kinds are the ones recorded in `fdd-lint-allow` for a prescribed format, nothing more
- [ ] Every FR# lands in at least one §4 step and one §13 scenario (no orphans either way)
- [ ] Attached forward mode: every in-scope S# is the source of at least one FR#, every A# appears in §13, and no FR# lacks an S# (nothing designed outside the contract)
- [ ] Change mode: base and head SHAs pinned in the workspace; every changed file in the review-diff plan is reflected in the FDD; new/changed steps marked; departures from the contract/TDD raised as Q#, not smoothed over
- [ ] §1.1 gives the business reason for the change (as-built: what the function is for); forward and change modes: §1.2 has one block per change a stakeholder would notice, in run order — today, after this change, why, who notices, where it happens — concrete enough to picture
- [ ] Every reason in §1 has a source — the brief, the contract's objective, a recorded decision, the ticket or commit message of the change, or the user; a reason no source gives is a Q#, not invented
- [ ] §3 tells the run start to finish in time order — every trigger, schedule, component run, file, and report a person sees — each row with when, who or what, and the §4 subsection; its diagram shows the same events in lanes, nodes labelled E#
- [ ] §4 takes components in the order they first run in §3, each with "Starts when" and "Hands over to"; each new or changed step names its C#; `ses fdd-lint` reports no SEQUENCE finding
- [ ] Developer-only detail (component Inputs tables, Appendix A) sits inside `technical:start/end` markers, and the text outside them reads cleanly without it
- [ ] Each business rule stated in full once in §5 and each failure path once in §8; a step names them in a few words with the ID — never the ID alone — and the words agree; multi-condition rules have a decision table
- [ ] Every failure path found in the code (as-built) or required (forward) has an EX# with who is informed and the business recovery
- [ ] Every existing table, column, and code value named was confirmed against the schema; proposed ones are marked `new` and collide with no existing name
- [ ] Actors, triggers, consumers, and interfaces come from the code and the cross-repo search, with "no other consumer" backed by the search that found none
- [ ] The §3 sequence and its diagram are business-level and match the traced flow and schedules (as-built, change) or the research call graph plus the change (forward)
- [ ] Every statement about existing behaviour has an Appendix A row with a source reference
- [ ] §1.4 lists every business term relied on: global ones with their `Meaning` line copied verbatim from `<workspace-root>/work/domain-glossary.md` (none re-defined), repo-specific ones defined for their repo
- [ ] No section dropped — "None" stated explicitly where nothing applies
- [ ] Open Q# items answered, or explicitly deferred by the user and recorded in §12; §1.3 names the ones the reader must decide
- [ ] doc-fact-checker ran on the whole FDD once, each report is kept the moment it returned (`ses review record --doc`), every later check re-checked only what `ses review changed` listed — once per gate, with revisions batched into one re-check before approval was recorded — its findings were resolved at the functional level, and `ses review require <ws> doc-fact-checker fdd` passes after the last revision; a self-pass is named to the user
- [ ] ASSUMPTIONS.md reviewed — open entries presented for ratification (decision-protocol §4)
- [ ] Handoff summary written last, as Appendix B at the end of the document, and `ses handoff check` passes
- [ ] Written to `<root>/standards/writing.md` throughout: §1 says why, what changes, and what to decide; plain words and short sentences; about the system, never about how the document was made; no coined noun stacks or slashes; IDs in brackets or columns, never in place of the words
- [ ] `ses prose-lint` passes on fdd.md — each finding fixed by rewriting the sentence, not by dodging the pattern
- [ ] fdd.md is the only version presented and delivered — converted as written; a `ses fdd-view` view only when the user asked for one (recorded in `fdd-views`)
- [ ] Approval recorded only after the user's explicit approval (`fdd` field when attached, `approval=approved` when standalone), with the date in the FDD header
