# Grill checklist

Run before marking the grill stage done.

- [ ] Every category (data, lifecycle, interface, temporal, environment, security/ops, deploy/rollback) has ≥1 concrete scenario using the task's real objects — or an explicit n/a with reason
- [ ] Every `covered` verdict cites where the design handles it (TDD § / file:line) — no bare assertions
- [ ] Every `gap-fixed` scenario had one defensible behaviour, traces to an S#/A#, and passes decision-protocol §2 — a choice between behaviours went to the user instead
- [ ] Every `gap-fixed` scenario was actually edited into the TDD (design section, plus a §7 `G#` row when testable), not just logged
- [ ] Every `out-of-scope` verdict cites the contract exclusion it relies on
- [ ] Zero `ask-user` items remain unanswered — each is answered (landed in the TDD) or explicitly deferred by the user (verbatim, in TDD §11 Risks, the grill log, and PARKED.md)
- [ ] Answers that changed an approved FDD's business rules or exceptions went through an FDD amendment and re-approval first
- [ ] Terminology challenges resolved by the user, never by assumption; load-bearing resolutions recorded in the TDD
- [ ] Checkable scenarios were checked against code/dev DB, not reasoned about (decision-protocol §1)
- [ ] TDD handoff summary names every `G#` row; `ses handoff check` passes
- [ ] Every TDD edit was fact-checked (doc-fact-checker scoped to the edited sections) and its findings resolved
- [ ] An approved TDD the grill edited was re-approved once, from a single change list, and the re-approval recorded in the TDD header and STATUS (no edits → none needed)
- [ ] STATUS.md updated: grill → done (or waived, with who/when), next action /impl-plan
