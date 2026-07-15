---
name: implement
description: Execute the approved implementation document step by step on a task branch - code, verify each step against the live environment where available, capture evidence, checkpoint-commit, and pass code review. Use after the impl doc is approved.
argument-hint: "[task-id]"
---

# /implement — execute the impl doc, verifiably

> Path note: `${CLAUDE_PLUGIN_ROOT}` is this framework's root — the ancestor
> directory of this file containing `plugin.json`/`skills/`. Claude Code resolves
> it automatically; other harnesses resolve it from this file's location.

Execute `work/<id>/impl-doc.md` exactly: one step at a time, verified and
committed before the next begins.

## 0. Preamble

1. Load lessons tagged `stage:implement` and the languages involved from
   `${CLAUDE_PLUGIN_ROOT}/knowledge/lessons.md`.
2. Locate the workspace; verify `impl-plan: approved`.
3. Read scope-contract.md, tdd.md, impl-doc.md, and `.conventions.md`.
   Also read ASSUMPTIONS.md — you are building on its ratified entries.
4. Unknowns follow `${CLAUDE_PLUGIN_ROOT}/core/decision-protocol.md`. During
   implementation the "no dangerous surface" rule bites hardest: coding
   judgment calls passing §2 → ASSUMPTIONS.md; any uncertainty about a
   data-changing statement, an external contract, or the approved design
   stops and asks — regardless of confidence.
5. Check STATUS.md for a recorded branch/step — if present, this is a RESUME:
   `git log` the branch, find the last completed step (checkpoint commits are
   named `<task-id> step <N>: <desc>`), verify its evidence exists, continue
   from step N+1.

## 1. Branch setup (first run only)

1. Ensure the work repo is clean; stash/ask if not.
2. Create the branch named in the impl-doc from the repo's mainline.
3. Record the branch in STATUS.md.

## 2. The step loop

For each impl-doc step N, in order:

1. **Code** the step. Match the surrounding code's conventions (`.conventions.md`
   overrides `${CLAUDE_PLUGIN_ROOT}/standards/`). Touch only the files the step
   names — if the step turns out to need another file, update the impl-doc row
   first (append a note, don't rewrite history).
2. **Verify** using the step's verification column — invoke the /verify-code
   recipes for each changed file (live mode via `$SES_DB_CONN`/`$SES_KSH_HOST`/
   `$SES_PY` when reachable; static fallback otherwise, recorded as such).
   Capture output to `evidence/step<N>-<desc>.txt` using
   `${CLAUDE_PLUGIN_ROOT}/templates/test-evidence.md`.
3. **On failure**: fix and re-verify. If the fix invalidates the design, STOP —
   report to the user, propose a TDD/impl-doc amendment, get approval before
   continuing. Never quietly diverge from the approved documents.
4. **Checkpoint commit**: `git commit` the step with message
   `<task-id> step <N>: <desc>`. Never batch multiple steps into one commit.
5. Update STATUS.md (current step, last evidence file) after every step —
   this is the resume point.

### Scope guard (continuous)

Before each commit, check the diff against the scope contract: every changed
file must map to an in-scope item via the impl-doc. Bugs or improvements you
notice along the way go to PARKED.md — even one-line "harmless" fixes.

## 3. Test plan execution

After the last step, run the full impl-doc test plan (unit, integration,
regression). Capture results to `evidence/tests-<date>.txt`. Every acceptance
criterion must reach PASS; failures loop back to the step loop.

## 4. Review gate

1. Run the review procedure in `${CLAUDE_PLUGIN_ROOT}/agents/code-reviewer.md`
   on the full branch diff — as a subagent where the harness supports it;
   otherwise execute the procedure yourself as a separate, fresh review pass,
   holding yourself to its report format. Resolve findings
   or record a conscious waiver (with the user for anything non-trivial).
2. Self-check with `${CLAUDE_PLUGIN_ROOT}/checklists/implement.md`.
3. Update STATUS.md: `implement: done` (branch + final commit recorded), next
   action `/deliver`.

## Fault tolerance

- The branch + checkpoint commits + STATUS.md + evidence/ ARE the recovery
  state; keep all four current after every step.
- A crashed session resumes losslessly: worst case, one step's work is redone.
- If the environment becomes unreachable mid-task, continue in static-fallback
  mode, mark affected evidence `mode: static-fallback`, and list the pending
  live verifications in STATUS.md under next action.
