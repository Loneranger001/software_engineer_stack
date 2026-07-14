# Grill checklist

Run before marking the grill stage done.

- [ ] Every category (data, lifecycle, interface, temporal, environment, security/ops) has ≥1 concrete scenario using the task's real objects — or an explicit n/a with reason
- [ ] Every `covered` verdict cites where the design handles it (TDD § / file:line) — no bare assertions
- [ ] Every `gap-fixed` scenario was actually edited into the TDD (design section AND a §7 verification row), not just logged
- [ ] Zero `ask-user` items remain unanswered — each is answered (landed in the TDD) or explicitly deferred by the user (verbatim, in TDD §11 Risks and the grill log)
- [ ] Terminology challenges resolved by the user, never by assumption; load-bearing resolutions recorded in the TDD
- [ ] Checkable scenarios were checked against code/dev DB, not reasoned about (decision-protocol §1)
- [ ] If an approved TDD materially changed, the changed sections were re-presented and re-approved
- [ ] STATUS.md updated: grill → done (or waived, with who/when), next action /impl-plan
