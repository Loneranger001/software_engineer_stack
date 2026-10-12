---
name: implement
description: Execute the approved implementation document step by step on a task branch - code, verify each step against the live environment where available, capture evidence, checkpoint-commit, and pass code review. Use after the impl doc is approved.
argument-hint: "[task-id]"
---

# /implement — execute the impl doc, verifiably

> Path note: `${CLAUDE_PLUGIN_ROOT}` is this framework's root — the ancestor
> directory of this file containing `plugin.json`/`skills/`. Claude Code resolves
> it automatically; other harnesses resolve it from this file's location.

> Script shorthand: a bare `status.py`, `handoff.py`, `checkpoint.py`, or
> `xsearch.py` below means `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/<name>`; a
> bare `<name>.sh` means `${CLAUDE_PLUGIN_ROOT}/scripts/<name>.sh`. Run them
> by that full path — the scripts are not on PATH.

Execute `<ws>/impl-doc.md` exactly: one step at a time, verified and
committed before the next begins.

## 0. Preamble

1. Load applicable lessons:
   `${CLAUDE_PLUGIN_ROOT}/scripts/lessons.sh implement --lang <languages the impl doc touches>`
   — the language filter pulls in verify-stage lessons for that code too.
2. Locate the workspace and gate:
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/status.py require <ws> impl-plan=approved`
   (`<ws>` = `<workspace-root>/work/<id>`) — non-zero exit = stop.
3. Read the contract and impl-doc handoff summaries
   (`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/handoff.py show <ws>/<doc>`) — not the whole documents.
   For each step, read only its row in impl-doc §2 and the TDD sections it
   cites. Also read the rules files of
   every repo the impl doc changes (`${CLAUDE_PLUGIN_ROOT}/scripts/repo-rules.sh <repo>
   <files>`; paths from STATUS.md — see
   `${CLAUDE_PLUGIN_ROOT}/core/repo-resolution.md`; git operations and test
   runs execute with the step's own repo as their working directory).
   Also read ASSUMPTIONS.md — you are building on its ratified entries.
4. Unknowns follow `${CLAUDE_PLUGIN_ROOT}/core/decision-protocol.md`. During
   implementation the "no dangerous surface" rule bites hardest: coding
   judgment calls passing §2 → ASSUMPTIONS.md; any uncertainty about a
   data-changing statement, an external contract, or the approved design
   stops and asks — regardless of confidence.
5. `status.py show <ws>` — a recorded `branch.<repo>` or `current-step` means
   this is a RESUME. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/checkpoint.py resume <ws>`: it
   finds the last `<task-id> step <N>` checkpoint commit per repo, compares it
   with `current-step`, checks each repo is on its recorded branch, and lists
   every uncommitted file — as the next step's own files (a half-done step)
   or UNEXPECTED.
   - Exit 0 (CLEAN) → run `checkpoint.py verify <ws>`, then continue from
     step N+1.
   - Exit 3 (NEEDS DECISION) → stop and show the user its report and the
     uncommitted changes (`git status`, `git diff`, untracked files'
     contents). Ask: keep the half-done work and finish step N+1, or discard
     it and redo the step. Never fold uncommitted work into a commit, stash
     it, or discard it without that answer — it may be the user's own edit.
   - Any other exit (1 = a git or STATUS error, e.g. a recorded branch that
     no longer exists) → stop and show the user the error; resume only once
     it is fixed.
   - The commit log is the truth: if it disagrees with `current-step`, trust
     the commits and re-record the field.

## 1. Branch setup (first run only)

1. Ensure each repo the impl-doc changes is clean. If one isn't, show the
   user what is uncommitted and ask — never stash, commit, or discard their
   work unasked.
2. In each, create the branch named in the impl-doc from that repo's mainline.
3. Record the branch per repo:
   `status.py field <ws> branch.<repo-name> <branch> --log "branch created in <repo-name>"`,
   then `status.py set <ws> implement=in-progress`.
4. **Commit-message preflight**, before the first checkpoint commit in each
   repo: inspect its `commit-msg` hook (`git -C <repo> config core.hooksPath`,
   else `.git/hooks/commit-msg`; also a `commit-msg` stage in
   `.pre-commit-config.yaml`) and adopt its exact format. Recent history and
   framework examples are not enough — the hook is what rejects the commit.
   Fit the checkpoint message into that format keeping the
   `<task-id> step <N>` token intact (resume greps for it), and record it:
   `status.py field <ws> commit-format.<repo-name> "<format>"`.
5. Repos in `<repo-set>` that the scope contract does NOT list as changing get
   no branch and no commits — they were analysis scope, not write scope.

## 2. The step loop

For each impl-doc step N, in order:

1. **Code** the step, in the repo the step names, following that repo's
   rules files (`repo-rules.sh <repo> <files>` — nested AGENTS.md nearest
   the file wins), then the surrounding code's style, then
   `${CLAUDE_PLUGIN_ROOT}/standards/`. Touch only the files the step
   names — if the step turns out to need another file, update the impl-doc row
   first (append a note, don't rewrite history) and its `step <N>:` summary
   line.
2. **Verify** using the step's verification column — for each changed file,
   the recipe for its language in
   `${CLAUDE_PLUGIN_ROOT}/skills/verify-code/SKILL.md` (read only its
   "Lessons and output capture", "Environment resolution", and that
   language's sections; live mode via the task's recorded `db-connection`
   (MCP or CLI) / `$SES_KSH_HOST` / `$SES_PY` when reachable; static
   fallback otherwise, recorded as such).
   Run each shell command through `${CLAUDE_PLUGIN_ROOT}/scripts/capture.sh`
   (MCP database calls: verify-code's MCP-mode capture) and write `evidence/step<N>-<desc>.txt` from its summary using
   `${CLAUDE_PLUGIN_ROOT}/templates/test-evidence.md`; the full output stays
   in `evidence/raw/`.
3. **On failure**: fix and re-verify, at most 3 attempts per step. STOP
   when it still fails after the third, when the fix needs a file outside
   the step's row, or when it invalidates the design:
   `status.py next <ws> "step <N> blocked: <reason>"`, show the user the
   evidence, propose the TDD/impl-doc amendment, and get approval before
   continuing. Never quietly diverge from the approved documents.
4. **Checkpoint commit**: `git commit` the step **in the step's repo** with
   message `<task-id> step <N>: <desc>` (inside the hook format from §1),
   ending with the evidence hashes as their own paragraph —
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/checkpoint.py trailer <ws> evidence/step<N>-<desc>.txt
   evidence/raw/<its logs>` prints them (`git commit -m "<subject>" -m
   "<trailer lines>"`). `work/` may live outside every repo; these lines put
   proof of the evidence into git.
   Never batch multiple steps into one commit, and never span repos in one
   step — a step belongs to exactly one repo so that its rollback is a single
   revert.
5. Record after every step — this is the resume point:
   `status.py field <ws> current-step <N> --log "step <N> committed <sha>; evidence/step<N>-<desc>.txt"`.

### Scope guard (continuous)

Before each commit, check the diff (`review-diff.sh <repo> <mainline> HEAD`
lists the changed files) against the scope contract's handoff summary (S#
items, repos allowed to change): every changed file must map to
an in-scope item via the impl-doc, and its repo must be one
the contract lists as changing. A change that turns out to be needed in
another repo stops the loop and goes to the user as a scope amendment — not a
quick fix in a repo nobody approved touching. Bugs or improvements you
notice along the way go to PARKED.md — even one-line "harmless" fixes.

## 3. Test plan execution

After the last step, run the full impl-doc test plan (unit, integration,
regression) through `capture.sh`, summary to `evidence/tests-<date>.txt`.
Every acceptance criterion must reach PASS. A failure is fixed as a NEW
step, never by reopening a committed one:
1. Append step N+1 to impl-doc §2 — an integer number (`checkpoint.py`
   parses only integers), its repo, files, verification, and rollback —
   with an amendment note naming the failing test, and add its `step <N+1>:`
   line to the handoff summary. If the fix changes the approved design, stop
   for approval first (§2 step 3).
2. Run it through §2 like any other step (code, verify, checkpoint commit,
   `current-step`), then re-run the full test plan. The 3-attempt cap of §2
   step 3 applies to the test plan too.

## 4. Review gate

1. Run the review procedure in `${CLAUDE_PLUGIN_ROOT}/agents/code-reviewer.md`
   on the branch of every changed repo (it reads the diff file by file via
   `review-diff.sh`; one pass per repo, each
   judged against that repo's own rules files) — as a subagent where the harness
   supports it;
   otherwise execute the procedure yourself as a separate, fresh review pass,
   holding yourself to its report format. Resolve findings
   or record a conscious waiver (with the user for anything non-trivial).
2. Self-check with `${CLAUDE_PLUGIN_ROOT}/checklists/implement.md`.
3. Record the final commit per changed repo
   (`status.py field <ws> final-commit.<repo-name> <sha>`), then
   `status.py set <ws> implement=done --next "Run /deliver."`.

## Fault tolerance

- The branch + checkpoint commits + STATUS.md + evidence/ ARE the recovery
  state; keep all four current after every step.
- A crashed session resumes losslessly: `checkpoint.py resume` shows exactly
  what was committed and what was left half-done; worst case, one step's work
  is redone — by the user's choice, never silently.
- Evidence is hashed into each checkpoint commit; `checkpoint.py verify`
  proves the evidence/ files a delivery cites are the ones that were
  recorded. A lost or edited evidence file is a finding, not a formality.
- If the environment becomes unreachable mid-task, continue in static-fallback
  mode, mark affected evidence `mode: static-fallback`, and list the pending
  live verifications as the next action (`status.py next <ws> "..."`).
