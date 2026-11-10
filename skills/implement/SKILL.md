---
name: implement
description: Execute the approved implementation document step by step on a task branch - code, verify each step against the live environment where available, capture evidence, checkpoint-commit, and pass code review. Use after the impl doc is approved.
argument-hint: "[task-id]"
---

# /implement — execute the impl doc, verifiably

> Framework files: `<root>` is what `ses root` prints — run it once. Every
> framework script runs as `ses <command>` (`ses help` lists them). If `ses`
> is not on PATH, use `python3 <skill-dir>/../../bin/ses` in its place —
> `<skill-dir>` is the folder this SKILL.md was loaded from — here and for
> every `ses` below. If neither runs, stop and ask the user (README →
> Install); never guess another path.

Execute `<ws>/impl-doc.md` exactly: one step at a time, verified and
committed before the next begins.

## 0. Preamble

1. Load applicable lessons once step 2 has located `<ws>`:
   `ses lessons implement --ws <ws>` — the repos and languages come from
   STATUS.md, so verify-stage lessons for that code come in too; add
   `--lang <languages the impl doc touches>` if a language is new to the repos.
2. Locate the workspace and gate:
   `ses status require <ws> impl-plan=approved`
   (`<ws>` = `<workspace-root>/work/<id>`) — non-zero exit = stop.
3. Read the contract's handoff summary
   (`ses handoff show <ws>/scope-contract.md`) and impl-doc.md whole — it is
   terse and has no summary. For each step, open only the TDD sections its
   row cites. Also read the rules files of
   every repo the impl doc changes (`ses repo-rules <repo>
   <files>`; paths from STATUS.md — see
   `<root>/core/repo-resolution.md`; git operations and test
   runs execute with the step's own repo as their working directory).
   Also read ASSUMPTIONS.md — you are building on its ratified entries.
4. **Rules checklist**: from those rules files write
   `<ws>/rules-checklist.md`, rebuilt at every session start — one line per
   checkable rule that applies to the languages and object kinds the impl
   doc touches: `R<n> | <repo> | <rule, in the file's own words> |
   <file>:<line>` (naming per object type, error handling, logging,
   transaction control, formatting). Leave out what no diff can be checked
   against ("write clean code"). It is the worksheet for each step's rules
   check, not a substitute: the rules files stay the authority, and the
   code reviewer judges against them.
5. Unknowns follow `<root>/core/decision-protocol.md`. During
   implementation the "no dangerous surface" rule bites hardest: coding
   judgment calls passing §2 → ASSUMPTIONS.md; any uncertainty about a
   data-changing statement, an external contract, or the approved design
   stops and asks — regardless of confidence.
6. `ses status show <ws>` — a recorded `branch.<repo>` means this is a
   RESUME. Run `ses checkpoint resume <ws>`: it finds the last
   `<task-id> step <N>` checkpoint commit per repo (the commits are the step
   record — nothing else stores it), checks each task worktree is on its
   recorded branch, and lists every uncommitted file — as the next step's
   own files (a half-done step) or UNEXPECTED. A recorded `branch.<repo>`
   with no `worktree.<repo>` (a workspace from before worktrees) gets one
   first: `ses worktree add <ws> <repo-name> <branch>` checks the existing
   branch out as it is.
   - Exit 0 (CLEAN) → run `ses checkpoint verify <ws>`, then continue from
     step N+1.
   - Exit 3 (NEEDS DECISION) → stop and show the user its report and the
     uncommitted changes (`git status`, `git diff`, untracked files'
     contents). Ask: keep the half-done work and finish step N+1, or discard
     it and redo the step. Never fold uncommitted work into a commit, stash
     it, or discard it without that answer — it may be the user's own edit.

## 1. Branch setup (first run only)

1. Confirm each impl-doc §1 precondition (check it, or ask the user), and
   probe the dev environment once (`$SES_DB_CONN`, `$SES_KSH_HOST`, `$SES_PY`
   — whichever the steps need): tell the user which steps will run in
   static-fallback mode before step 1, not after it.
2. For each repo the impl doc changes, check the task branch out in its own
   worktree: `ses worktree add <ws> <repo-name> <branch>` — `--base`
   defaults to the recorded `mainline.<repo>`; pass `--base <mainline>` only
   when none is recorded (ask the user which branch the repo releases
   from, and record it as `mainline.<repo>`). It fetches and cuts the branch from `origin/<mainline>` — never
   from whatever the repo has checked out, which may be another task's
   branch — and records `branch.<repo>`, `base.<repo>` and `worktree.<repo>`.
   The repo's own checkout is never switched, so the user's uncommitted
   work there stays theirs. Exit 3 (the branch is checked out elsewhere) →
   show the user its message and let them free it.
3. `ses status set <ws> implement=in-progress`. From here `<wt>` is
   `ses status get <ws> worktree.<repo-name>`: every edit, diff, stage,
   commit, verify recipe and test run for that repo happens in `<wt>`. Every
   later `<mainline>` — the scope guard, the review gate, /deliver, /retro —
   is `ses status get <ws> base.<repo-name>`, never a guess.
4. **Commit subjects come from the hook.** Every checkpoint subject is
   printed by `ses checkpoint subject <ws> <repo-name> <N> "<desc>"` (`tests`
   instead of `<N>` for the test-plan commit). It runs the repo's own
   `commit-msg` hook (core.hooksPath honoured) against the forms
   `ses checkpoint resume` can read — `<task-id> step <N>: …`,
   `<task-id>: step <N>: …`, `<task-id>: <task-id> step <N>: …` — and prints
   the first one the hook accepts. Exit 3 = the hook rejects all three: show
   the user its message and ask how checkpoint commits may be written. A
   `commit-msg` stage in `.pre-commit-config.yaml` that is not installed as a
   hook is only warned about: check the subject against it by hand.
5. Repos in `<repo-set>` that the scope contract does NOT list as changing get
   no branch, no worktree and no commits — they were analysis scope, not
   write scope. `ses checkpoint verify` fails on a task commit in any of them.

## 2. The step loop

For each impl-doc step N, in order:

1. **Code** the step, in the worktree of the repo the step names, following that repo's
   rules (`ses repo-rules <repo> <files>`, its rules-checklist.md lines)
   as `<root>/core/repo-resolution.md` splits them: **a new file** follows
   the rules strictly, whatever existing files do; **any change to an
   existing file** — a new procedure, function, class or method included —
   follows that file's own conventions, the rules filling only what it
   doesn't show. Existing identifiers you call keep their names. Touch only the files the step
   names — if the step turns out to need another file, update the impl-doc row
   first (append a note, don't rewrite history).
2. **Rules check**, before verifying: read the step's diff
   (`git -C <wt> diff HEAD -- <files>`; a new file whole). A new file:
   against rules-checklist.md. An existing file: against its own
   conventions, and rules-checklist.md for what it doesn't show. Check
   every new or renamed identifier against the naming standard that governs
   it and every added or changed line against the rest, and fix each
   violation now. A rule breach the file's convention carries into your
   change, or an existing identifier that breaks a rule, stays as it is:
   one PARKED.md line (file or name, rule). The result goes into the Rules check section of the step's
   evidence file (written in 3).
3. **Verify** using the step's Verify column — invoke the /verify-code
   recipes for each changed file (live mode via `$SES_DB_CONN`/`$SES_KSH_HOST`/
   `$SES_PY` when reachable; static fallback otherwise, recorded as such).
   Run each command through `ses capture`, with log names starting
   `step<N>-`, and write `evidence/step<N>-<desc>.txt` from its summary using
   `<root>/templates/test-evidence.md`; the full output stays
   in `evidence/raw/`.
4. **On failure**: fix, rules-check the lines the fix changed, and
   re-verify. If the fix invalidates the design, STOP —
   report to the user, propose a TDD/impl-doc amendment, get approval before
   continuing. Never quietly diverge from the approved documents.
5. **Checkpoint commit**: stage the step's own files by name
   (`git -C <wt> add <files>` — never `git add -A` or `git add .`, which
   would sweep in `work/` when it sits inside the repo), then `git commit`
   the step **in the step's worktree** with the subject
   `ses checkpoint subject <ws> <repo-name> <N> "<desc>"` prints (§1 step 4), ending with the evidence hashes as
   their own paragraph — `ses checkpoint trailer <ws>
   evidence/step<N>-<desc>.txt evidence/raw/<its logs>` prints them
   (`git commit -m "<subject>" -m "<trailer lines>"`) and refuses while any
   workspace file is staged. The workspace itself never goes into git; these
   lines put proof of the evidence there instead.
   Never batch multiple steps into one commit, and never span repos in one
   step — a step belongs to exactly one repo so that its rollback is a single
   revert. The commit IS the resume point; nothing else needs recording.
   Track the loop in the harness's todo/plan tool if it has one — that is
   in-session convenience; a new session resumes from the commits.

### Scope guard (continuous)

Before each commit, after staging the step's files by name, check what the
commit will add (`git -C <wt> diff --cached --name-only`) and what the
branch already holds (`ses review-diff <wt> <mainline> HEAD`, `<mainline>`
from `base.<repo>` — committed
work only, so it cannot see the step being committed) against the scope
contract's handoff summary (S# items, repos allowed to change): every file
must map to an in-scope item via the impl-doc, and its repo must be one the
contract lists as changing. A change that turns out to be needed in
another repo stops the loop and goes to the user as a scope amendment — not a
quick fix in a repo nobody approved touching. Bugs or improvements you
notice along the way go to PARKED.md — even one-line "harmless" fixes.

## 3. Test plan execution

After the last step, run the full impl-doc test plan (unit, integration,
regression) through `ses capture` with log names starting `tests-<date>-`
— never a step's log name, whose hash is already committed — summary to
`evidence/tests-<date>.txt`, with one row per T# in its Result table
(`<root>/templates/test-evidence.md`): PASS, FAIL, PARTIAL or NOT-RUN, the
mode it ran in, and where its expected value came from (`Expected from`).
Derive each expectation from the scenario, the spec or a fixture — never by
re-running the code under test or a copy of its query; a PASS without an
independent expectation is NO-ORACLE. Every TDD §7 row (A#, TS#, G#) must reach PASS through
its T#: `ses coverage <ws>` walks row → T# → recorded result and is the
judge — a T# that could not run is NOT-RUN, never left out.

- A failure loops back: fix it in the step whose files it touches,
  re-verify (log names starting `step<N>-fix-`), and commit it as
  `step <N>: fix <what>` (subject from `ses checkpoint subject`) with its own evidence and trailer. Then
  re-run the affected T#s under a new `tests-<date>-` name and record that
  re-run in its own `tests:` commit, as below — the latest result per T# wins.
- Once all pass, record the test-plan evidence like a step: an empty commit
  on `<work-repo>`'s task branch (else the first changed repo's),
  `git commit --allow-empty -m "<subject>" -m "<trailer>"`, the subject from
  `ses checkpoint subject <ws> <repo-name> tests "test plan <date>"` and the trailer from `ses checkpoint trailer <ws>
  evidence/tests-<date>.txt <its raw logs>` — then run `ses coverage <ws>`
  (a result counts only once its evidence hash is committed).

## 4. Review gate

1. Run the review procedure in `<root>/com.github.copilot/agents/code-reviewer.agent.md`
   on the branch of every changed repo (it reads the diff file by file via
   `ses review-diff`; one pass per repo, each
   judged against that repo's own rules files) — delegated per `<root>/core/reviewers.md`.
   Keep each pass's report:
   `ses review record <ws> code-reviewer <repo-name> --mode <mode> <report>`.
   Resolve findings — each fix committed as step `<N>`'s `fix <what>` (subject from `ses checkpoint subject`)
   for the step whose files it touches, re-verified with its own evidence
   and trailer, as in §3 —
   or record a conscious waiver (with the user for anything non-trivial).
   A standards finding (a repo rule in a new file, the file's convention in
   an existing one) is fixed, or waived by the user only; the reviewer's
   PRE-EXISTING list goes to PARKED.md. Review again after the fixes;
   `ses review require <ws> code-reviewer <repo-name>` must pass for every
   changed repo (a user waiver of a finding is recorded in the next report,
   not by skipping the gate). Tell the user how each review ran — a
   self-pass by name.
2. Self-check with `<root>/checklists/implement.md`.
3. Record: `ses status set <ws> implement=done --next "Run /deliver."`. If
   `ses coverage <ws>` exits 3 (a row NOT-RUN, PARTIAL — static fallback —
   or without a result, typically for want of a live environment), tell the
   user each row it lists and keep them in the next action:
   `--next "Run /deliver. Not verified yet: <IDs from ses coverage>"`.
   /deliver will not ship them until each is run or waived by the user.

## Fault tolerance

- The branch + checkpoint commits + evidence/ ARE the recovery state, with
  STATUS.md naming the branches and their worktrees; keep them current after
  every step. A lost worktree is recreated from its branch with
  `ses worktree add <ws> <repo-name> <branch>`.
- A crashed session resumes losslessly: `ses checkpoint resume` shows exactly
  what was committed and what was left half-done; worst case, one step's work
  is redone — by the user's choice, never silently.
- Evidence is hashed into each checkpoint commit; `ses checkpoint verify`
  proves the evidence/ files a delivery cites are the ones that were
  recorded. A lost or edited evidence file is a finding, not a formality.
- If the environment becomes unreachable mid-task, continue in static-fallback
  mode, mark affected evidence `mode: static-fallback`, and list the pending
  live verifications as the next action (`ses status next <ws> "..."`).
