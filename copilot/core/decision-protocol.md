# Decision protocol — what to do when you don't know

The shared policy for every stack skill. When work hits something unknown,
there are exactly three outcomes: **check it**, **proceed and log**, or
**stop and ask**. Which one applies is decided by this protocol, not by
in-the-moment optimism.

## 1. Checkable facts are checked, never estimated

If the unknown can be resolved by reading code, running a query against a
reachable environment, grepping the repo, or consulting the task workspace
documents — resolving it that way is MANDATORY before any confidence judgment.

Confidence applies only to genuine judgment calls (design choices, intent
interpretation, behaviour of unreachable systems). "I'm 95% sure that column
is NOT NULL" is not a confidence statement; it's an unread data dictionary.

## 2. Proceed + log — the narrow path

Continue WITHOUT interrupting the user only when **all four** hold:

1. **Confidence ≥ ~90%** — you would bet the rework on it. The basis is
   evidence you can cite (repo conventions, the brief's wording, platform
   behaviour you verified), not plausibility.
2. **Cheaply reversible** — a later gate can undo the decision without
   cascading rework (e.g. a naming choice, an internal structure choice,
   ordering of independent steps).
3. **Inside the scope contract** — the decision changes HOW an in-scope item
   is met, never WHAT is in scope.
4. **No dangerous surface** — it does not involve data-changing or
   irreversible operations, external interface contracts, or anything
   prod-adjacent.

Then record it in the workspace `ASSUMPTIONS.md` **at the moment you decide**,
one row per assumption:

```
| # | Date | Stage | Assumption | Basis (why ~90%) | Impact if wrong | Reversal step | Status |
```

`Status` is `open` until a gate ratifies it (§4).

## 3. Stop and ask — everything else

Stop and ask the user when **any** holds, regardless of confidence:

- **Genuinely unknown** — below the confidence bar, or two readings of the
  brief/design are both defensible.
- **Irreversible or high blast radius** — data deletes/updates beyond the
  task's own scratch data, interface contracts external callers depend on,
  schema drops, anything touching prod or shared environments. A
  95%-confident guess about a DELETE predicate still stops.
- **Scope-affecting** — would add, remove, or alter an in-scope item or
  exclusion. This is never assumable; it requires a scope-contract version
  bump with explicit approval.
- **User-reserved** — the user said "check with me about X".

Asking discipline: **blocking** questions (work cannot continue on any front)
ask immediately. **Non-blocking** questions accumulate and are asked as one
batch at the stage boundary — never one-at-a-time interruptions. Every asked
question and its answer is recorded where it lands (scope contract Q-table,
research open questions, or ASSUMPTIONS.md as a `resolved-by-user` row).

## 4. Gate ratification

Every approval gate — intake, tech-design, impl-plan, deliver, and the
change-request mini-contract — MUST present all `open` ASSUMPTIONS.md entries
alongside the artifact being approved:

- **Ratified** → status `ratified (gate, date)`. Assumptions that shape scope
  or design are promoted into the scope contract or TDD so the documents
  stand alone.
- **Corrected** → execute the recorded reversal step; rework is bounded by
  design because §2.2 only admitted cheaply-reversible decisions.

Delivery with an `open` assumption is a scope-audit finding: nothing ships
on an unratified guess.

## 5. Calibration feedback

/retro reviews ASSUMPTIONS.md: corrected entries mean over-confidence —
capture a lesson (`stage:any`) naming the class of decision that should have
been asked; a task with many trivially-ratified entries may mean
under-confidence — consider whether the checklist can pre-answer that class.
