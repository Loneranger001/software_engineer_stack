# Walkthrough — a task from brief to delivery

A narrated example of driving the framework, using the bundled sample repo
(`examples/sample-repo`, a nightly balance extract) and its brief
(`examples/sample-brief.md`: "add currency support"). Your real usage is the
same with your own repo and brief.

**The commands in order:**

```
/repo-profile                      (once per repo)
/intake <brief> <task-id>          → gate: you approve the scope contract
/research
/tech-design                       → gate: you approve the TDD
/grill                             → gate: zero open questions
/impl-plan                         → gate: you approve the impl doc
/implement
/deliver                           → gate: scope audit passes
/retro
```

You drive every transition — nothing auto-advances. Everything between
commands is saved to `work/<task-id>/`, so "the same session" is convenient
but NOT required: close the laptop after `/tech-design`, come back in three
days, run `/grill`, and it picks up from `STATUS.md` exactly where you left off.

---

## 0. Once per repo: profile it

```
you>  /repo-profile
```

The agent samples the repo and writes `.conventions.md` — naming patterns,
error-handling style, test tooling, deployment layout, each convention with a
real `file:line` example. Every later stage follows this file over the
framework's own defaults. Takes a few minutes; you only redo it when the repo
drifts.

## 1. /intake — the brief becomes an approved scope contract

```
you>  /intake ../sample-brief.md DEMO-1
```

The agent creates `work/DEMO-1/` (STATUS.md, ASSUMPTIONS.md, PARKED.md,
evidence/), stores the brief, reads it fully, and classifies every statement:
in-scope item, exclusion, constraint, or open question. Business terms the
brief leans on ("balance", "extract") are looked up in `.domain-glossary.md`
first — known terms link their entry; unknown ones become research targets. Then it asks you the
open questions in ONE batch — the sample brief is ambiguous on purpose, so
expect something like:

```
claude>  Q1: Where does an account's currency come from — is there a
         customers.currency_code, or does it need deriving?
         Q2: "Backward-compatible if possible" — is appending a 4th
         pipe-delimited field acceptable to the datamart loader?
         Q3: Should accounts with no currency fail the run or default to EUR?
```

You answer; it drafts the scope contract (in-scope table S1..Sn, exclusions
N1..Nn, acceptance criteria A1..An each with "how verified") and presents it:

```
claude>  Approve this scope contract? Work will be limited to exactly this.
you>     approve
```

**Gate 1 passed.** STATUS.md: `intake: approved`, next action `/research`.

## 2. /research — the codebase gets read, not skimmed

```
you>  /research
```

No questions for you unless it hits a blocker. The agent reads the affected
objects (package spec AND body, the ksh job, the Python tool), builds the
caller graph both directions with recorded grep commands, captures data-model
facts (running queries against dev if `SES_DB_CONN` is set), and writes
`research-notes.md` where every finding has a `file:line` or query source.
Side discoveries land in PARKED.md, not in your lap.

## 3. /tech-design — the TDD, traceable and fact-checked

```
you>  /tech-design
```

The agent designs against the research: traceability table first (every scope
item → a design section), as-is and to-be mermaid flows drawn from the call
graph, data model changes with migration + rollback, verification approach
(every acceptance criterion → a test type), operational impact. The
doc-fact-checker pass runs before you ever see it. Then:

```
claude>  TDD ready: [summary, key decisions, 2 open assumptions to ratify]
         Approve?
you>     change §4.2 to keep the old file name; otherwise fine
claude>  [updates, re-presents]
you>     approve
```

**Gate 2 passed.**

## 4. /grill — the design gets interrogated

```
you>  /grill
```

Phase 1 runs without you: the agent stress-tests the TDD with concrete
scenarios per category (data, lifecycle, interface, temporal, environment,
security/ops) — fixing what the evidence can answer, logging everything to
`grill-log.md`. Phase 2 is your interview; expect several short rounds:

```
claude>  Lifecycle: the extract reruns for a date that already has GBP rows —
         replace, reject, or merge? Design currently replaces silently (§4.1).
you>     replace is correct, that's the restart behaviour
claude>  Temporal: a backdated transaction arrives after the snapshot was
         extracted — is regeneration for past dates ever expected?
you>     yes, ops reruns up to 7 days back
claude>  Then §4.1's delete+insert covers it, but the extract FILE for the old
         date gets overwritten — is the datamart tolerant of re-delivery?
you>     good catch — ask the datamart team; defer as a risk for now
```

Answers land in the TDD immediately; deferrals go to §11 Risks verbatim.
Resolved terminology also lands in `.domain-glossary.md` as `user-confirmed`,
so the next task never re-asks it. **Gate 3 passed** when nothing is left open.

## 5. /impl-plan — the executable recipe

```
you>  /impl-plan
```

Ordered commit-sized steps, each with its own verification and rollback; test
plan mapped to every acceptance criterion; deployment and whole-change
rollback. You approve it (**Gate 4**) — this is the last cheap place to
change your mind.

## 6. /implement — code, one verified step at a time

```
you>  /implement
```

Branch created, then per step: code → `/verify-code` (live against dev if
`SES_DB_CONN`/`SES_KSH_HOST`/`SES_PY` are set, static fallback otherwise) →
evidence file → checkpoint commit. If a step invalidates the design, it stops
and asks rather than quietly diverging. After the last step: full test plan,
then the code-reviewer pass; SEV-1/2 findings get fixed before the stage
closes. If your session dies at step 3 of 6, rerun `/implement` — it resumes
at step 4.

## 7. /deliver — audited handover

```
you>  /deliver
```

Open assumptions ratified, scope-auditor pass (diff ↔ contract, both
directions), release notes with stand-alone deploy/rollback, your chosen
formats generated (`deliverables/tdd.docx`, …), branch pushed. **Gate 5
passed** — the task is delivered.

## 8. /retro — two minutes that improve the next task

```
you>  /retro
```

It asks you 2–3 pointed questions, distills actionable lessons into
`knowledge/lessons.md` (which every future run loads), and proposes concrete
template/checklist edits for your approval.

---

## The fast path: a small change request

No intake/TDD ceremony — one command:

```
you>  /change-request "reconcile.py should exit 3 (not 2) when the datamart
      file is missing, so ops can distinguish it from a bad-format file" CR-7
```

Flow: impact analysis (who reads that exit code? the recorded grep finds the
ksh wrapper and a cron alert) → mini scope contract you approve → surgical
change → verify + regression on the impacted callers → short release note.
If the analysis reveals it's NOT small, it says so and recommends `/intake`.

## Documentation tasks

```
you>  /document understanding-doc "the nightly balance extract"
you>  /document howto "rerun the extract for a past date"
you>  /document kb-article "extract fails with exit 3"
```

Analyze → draft from the matching template → fact-check pass → your formats.

## Things worth knowing

- **You can stack sessions however you like** — one sitting or eight; the
  workspace is the memory, not the chat.
- **Interruptions are safe everywhere**: every skill writes its progress as
  it goes and resumes from STATUS.md.
- **Saying no at a gate is normal** — gates exist so corrections happen where
  they're cheap. Rejecting a TDD costs minutes; rejecting a diff costs hours.
- **Check ASSUMPTIONS.md when a gate presents it** — that's where the agent
  shows you what it decided on its own authority.
- **In Copilot** the flow is identical; the commands come from
  `.github/prompts/` and the three reviewers run as native custom agents from
  `.github/agents/` (generate both once with
  `python3 scripts/build_copilot.py --target <your-repo>`).
