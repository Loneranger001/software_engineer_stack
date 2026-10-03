# Tech design checklist

Run before presenting the TDD for approval.

- [ ] Traceability table maps EVERY in-scope item to a design section (no orphans either way)
- [ ] Nothing in the design implements an out-of-scope/non-goal item
- [ ] Every claim about existing behaviour carries a source reference (file:line, query, doc)
- [ ] Interface impact analysis is backed by the research call graph — "no callers affected" is proven, not assumed
- [ ] Data model changes include migration/backfill AND rollback for each object
- [ ] Design follows the conventions of the repo each component lands in (or standards/ defaults where that repo is silent)
- [ ] Interface impact names the repo of every affected caller; "no callers affected" cites the search across every analyzed repo
- [ ] As-is and to-be flow diagrams present and consistent with the research call graph
- [ ] Verification-approach table covers every acceptance criterion (an untestable criterion blocks approval); operational impact stated line by line, "none" explicit
- [ ] Non-functional section addresses performance, security, operability — or states why not applicable
- [ ] At least one alternative was considered and its rejection justified
- [ ] Platform grounding: every integration mechanism in the to-be design is already used by the interface (research evidence) or is `in-use`/`available` in the platform inventory; anything else appears only in §10 marked REQUIRES NEW PLATFORM CAPABILITY, and the user decided it
- [ ] If the task is a work package of an approved architecture: the design conforms to its systems, mechanisms and data ownership, deviations went back for re-approval, and its §13 items for this package are answered
- [ ] doc-fact-checker agent ran on the TDD and its findings were resolved
- [ ] Open questions from research are resolved or explicitly carried as risks
- [ ] ASSUMPTIONS.md reviewed — open entries presented for ratification; design-shaping ones promoted into the TDD (decision-protocol §4)
- [ ] STATUS.md updated: tech-design → awaiting approval
