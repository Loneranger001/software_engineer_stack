---
name: implement
description: Execute the approved implementation document step by step on a task branch - code, verify each step against the live environment where available, capture evidence, checkpoint-commit, and pass code review. Use after the impl doc is approved.
argument-hint: "[task-id]"
---

# /implement — execute the impl doc, verifiably

> Framework files: `<root>` is what `ses root` prints — run it once. Every
> framework script runs as `ses <command>` (`ses help` lists them). If `ses`
> is not on PATH, stop and ask the user to install the framework (README →
> Install) — never guess its location.

Execute `<ws>/impl-doc.md` exactly: one step at a time, verified and
committed before the next begins.

## 0. Preamble

1. Load applicable lessons:
   `ses lessons implement --lang <languages the impl doc touches>`
   — the language filter pulls in verify-stage lessons for that code too.
2. Locate the workspace and gate:
   `ses status require <ws> impl-plan=approved`
   (`<ws>` = `<workspace-root>/work/<id>`) — non-zero exit = stop.
3. Read the contract and impl-doc handoff summaries
   (`ses handoff show <ws>/<doc>`) — not the whole documents.
   For each step, read only its row in impl-doc §2 and the TDD sections it
   cites. Also read the rules files of
   every repo the impl doc changes (`ses repo-rules <repo>
   <files>`; paths from STATUS.md — see
   `<root>/core/repo-resolution.md`; git operations and test
   runs execute with the step's own repo as their working directory).
   Also read ASSUMPTIONS.md — you are building on its ratified entries.
4. Unknowns follow `<root>/core/decision-protocol.md`. During
   implementation the "no dangerous surface" rule bites hardest: coding
   judgment calls passing §2 → ASSUMPTIONS.md; any uncertainty about a
   data-changing statement, an external contract, or the approved design
   stops and asks — regardless of confidence.
5. `ses status show <ws>` — a recorded `branch.<repo>` means this is a
   RESUME. Run `ses checkpoint resume <ws>`: it finds the last
   `<task-id> step <N>` checkpoint commit per repo (the commits are the step
   record — nothing else stores it), checks each repo is on its recorded
   branch, and lists every uncommitted file — as the next step's own files
   (a half-done step) or UNEXPECTED.
   - Exit 0 (CLEAN) → run `ses checkpoint verify <ws>`, then continue from
     step N+1.
   - Exit 3 (NEEDS DECISION) → stop and show the user its report and the
     uncommitted changes (`git status`, `git diff`, untracked files'
     contents). Ask: keep the half-done work and finish step N+1, or discard
     it and redo the step. Never fold uncommitted work into a commit, stash
     it, or discard it without that answer — it may be the user's own edit.

## 1. Branch setup (first run only)

1. Ensure each repo the impl-doc changes is clean. If one isn't, show the
   user what is uncommitted and ask — never stash, commit, or discard their
   work unasked.
2. In each, create the branch named in the impl-doc from that repo's mainline.
3. Record the branch per repo:
   `ses status field <ws> branch.<repo-name> <branch>`, then
   `ses status set <ws> implement=in-progress`.
4. **Commit-message preflight**, before the first checkpoint commit in each
   repo: inspect its `commit-msg` hook (`git -C <repo> config core.hooksPath`,
   else `.git/hooks/commit-msg`; also a `commit-msg` stage in
   `.pre-commit-config.yaml`) and adopt its exact format. Recent history and
   framework examples are not enough — the hook is what rejects the commit.
   Fit the checkpoint message into that format keeping the
   `<task-id> step <N>` token intact (resume greps for it). On a resume, the
   branch's existing checkpoint commits show the format already in use.
5. Repos in `<repo-set>` that the scope contract does NOT list as changing get
   no branch and no commits — they were analysis scope, not write scope.

## 2. The step loop

For each impl-doc step N, in order:

1. **Code** the step, in the repo the step names, following that repo's
   rules files (`ses repo-rules <repo> <files>` — nested AGENTS.md nearest
   the file wins), then the surrounding code's style, then
   `<root>/standards/`. Touch only the files the step
   names — if the step turns out to need another file, update the impl-doc row
   first (append a note, don't rewrite history) and its `step <N>:` summary
   line.
2. **Verify** using the step's verification column — invoke the /verify-code
   recipes for each changed file (live mode via `$SES_DB_CONN`/`$SES_KSH_HOST`/
   `$SES_PY` when reachable; static fallback otherwise, recorded as such).
   Run each command through `ses capture` and
   write `evidence/step<N>-<desc>.txt` from its summary using
   `<root>/templates/test-evidence.md`; the full output stays
   in `evidence/raw/`.
3. **On failure**: fix and re-verify. If the fix invalidates the design, STOP —
   report to the user, propose a TDD/impl-doc amendment, get approval before
   continuing. Never quietly diverge from the approved documents.
4. **Checkpoint commit**: `git commit` the step **in the step's repo** with
   message `<task-id> step <N>: <desc>` (inside the hook format from §1),
   ending with the evidence hashes as their own paragraph —
   `ses checkpoint trailer <ws> evidence/step<N>-<desc>.txt
   evidence/raw/<its logs>` prints them (`git commit -m "<subject>" -m
   "<trailer lines>"`). `work/` may live outside every repo; these lines put
   proof of the evidence into git.
   Never batch multiple steps into one commit, and never span repos in one
   step — a step belongs to exactly one repo so that its rollback is a single
   revert. The commit IS the resume point; nothing else needs recording.
   Track the loop in the harness's todo/plan tool if it has one — that is
   in-session convenience; a new session resumes from the commits.

### Scope guard (continuous)

Before each commit, check the diff (`ses review-diff <repo> <mainline> HEAD`
lists the changed files) against the scope contract's handoff summary (S#
items, repos allowed to change): every changed file must map to
an in-scope item via the impl-doc, and its repo must be one
the contract lists as changing. A change that turns out to be needed in
another repo stops the loop and goes to the user as a scope amendment — not a
quick fix in a repo nobody approved touching. Bugs or improvements you
notice along the way go to PARKED.md — even one-line "harmless" fixes.

## 3. Test plan execution

After the last step, run the full impl-doc test plan (unit, integration,
regression) through `ses capture`, summary to `evidence/tests-<date>.txt`.
Every acceptance criterion must reach PASS; failures loop back to the step
loop.

## 4. Review gate

1. Run the review procedure in `<root>/agents/code-reviewer.md`
   on the branch of every changed repo (it reads the diff file by file via
   `ses review-diff`; one pass per repo, each
   judged against that repo's own rules files) — as a subagent where the harness
   supports it;
   otherwise execute the procedure yourself as a separate, fresh review pass,
   holding yourself to its report format. Resolve findings
   or record a conscious waiver (with the user for anything non-trivial).
2. Self-check with `<root>/checklists/implement.md`.
3. Record: `ses status set <ws> implement=done --next "Run /deliver."`.

## Fault tolerance

- The branch + checkpoint commits + evidence/ ARE the recovery state, with
  STATUS.md naming the branches; keep them current after every step.
- A crashed session resumes losslessly: `ses checkpoint resume` shows exactly
  what was committed and what was left half-done; worst case, one step's work
  is redone — by the user's choice, never silently.
- Evidence is hashed into each checkpoint commit; `ses checkpoint verify`
  proves the evidence/ files a delivery cites are the ones that were
  recorded. A lost or edited evidence file is a finding, not a formality.
- If the environment becomes unreachable mid-task, continue in static-fallback
  mode, mark affected evidence `mode: static-fallback`, and list the pending
  live verifications as the next action (`ses status next <ws> "..."`).
