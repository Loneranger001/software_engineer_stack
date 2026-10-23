# Tech design checklist

Run before presenting the TDD for approval.

- [ ] Traceability table maps EVERY in-scope item to a design section (no orphans either way)
- [ ] Nothing in the design implements an out-of-scope/non-goal item
- [ ] If an approved FDD exists: every FR# is traced, and no section contradicts its business rules (BR#) or exceptions (EX#) — a needed departure was re-approved as an FDD amendment
- [ ] Every claim about existing behaviour carries a source reference (file:line, query, doc) — never research-notes.md or another workspace file
- [ ] §1 Overview lists every business term relied on: global ones with their `Meaning` line copied verbatim from `<workspace-root>/work/domain-glossary.md` (none re-defined), repo-specific ones defined for their repo
- [ ] Interface impact analysis is backed by the research call graph — "no callers affected" is proven, not assumed
- [ ] Data model changes include migration/backfill AND rollback for each object
- [ ] Design follows the conventions of the repo each component lands in (or standards/ defaults where that repo is silent)
- [ ] Interface impact names the repo of every affected caller; "no callers affected" cites the search across every analyzed repo
- [ ] As-is and to-be flow diagrams present and consistent with the research call graph
- [ ] Verification-approach table covers every acceptance criterion (an untestable criterion blocks approval); operational impact stated line by line, "none" explicit
- [ ] Non-functional section addresses performance, security, operability — or states why not applicable
- [ ] At least one alternative was considered and its rejection justified
- [ ] doc-fact-checker agent ran on the TDD and its findings were resolved
- [ ] Open questions from research are resolved or explicitly carried as risks
- [ ] ASSUMPTIONS.md reviewed — open entries presented for ratification; design-shaping ones promoted into the TDD (decision-protocol §4)
- [ ] `tech-design=approved` is set (`ses status`) only after the user's explicit approval
- [ ] Handoff summary written last and `ses handoff check` passes (every ID in the body is in the summary; contract version current)
- [ ] Review version (tdd.review.md) written from the fact-checked tdd.md: In short first, two pages (four at most), plain words per `<root>/standards/writing.md`; `ses review-version check` and `ses prose-lint` pass; the doc-fact-checker found it agrees with tdd.md
- [ ] The user approved the review version; approval and date recorded in both headers
