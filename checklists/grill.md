# Grill checklist

Run before marking the grill stage done.

- [ ] Every category (data, lifecycle, interface, temporal, environment, security/ops, deploy/rollback) has ≥1 concrete scenario using the task's real objects — or an explicit n/a with reason
- [ ] Every `covered` verdict cites where the design handles it (TDD § / `<repo>:<path>:<line>`) — no bare assertions
- [ ] Every `gap-fixed` scenario had one defensible behaviour, traces to an S#/A# (change request: a mini-contract Change bullet), and passes decision-protocol §2 — a choice between behaviours went to the user instead
- [ ] Every `gap-fixed` scenario was actually edited into the TDD (design section, plus a §7 `G#` row when testable) or, for a change request, into analysis.md (plus an acceptance criterion A# tagged `(grill #n)`), not just logged
- [ ] Every `out-of-scope` verdict cites the contract exclusion it relies on
- [ ] Zero `ask-user` items remain unanswered — each is answered (landed in the TDD or analysis.md) or explicitly deferred by the user (verbatim in the grill log and PARKED.md; a plain-words risk row in TDD §11, or the mini contract's Risks)
- [ ] Answers that changed an approved FDD's business rules or exceptions went through an FDD amendment and re-approval first
- [ ] Terminology challenges resolved by the user, never by assumption; load-bearing resolutions recorded in the TDD
- [ ] Checkable scenarios were checked against code/dev DB, not reasoned about (decision-protocol §1)
- [ ] Full pipeline: TDD handoff summary names every `G#` row; `ses handoff check` and `ses prose-lint` pass on tdd.md
- [ ] Every TDD edit was fact-checked (doc-fact-checker scoped to the edited sections), its report kept, its findings resolved, and `ses review require <ws> doc-fact-checker tdd-grill` passes
- [ ] An approved TDD the grill edited was re-approved once, from a single change list, and the re-approval recorded in the TDD header and STATUS (no edits → none needed)
- [ ] Full pipeline: STATUS.md updated — grill → done (or waived, with who/when), next action /impl-plan, or TDD approval first when it was grilled unapproved. Change request: the grill log's Close line written; an already-approved mini contract the grill changed was re-approved
