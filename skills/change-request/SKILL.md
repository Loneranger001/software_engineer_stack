---
name: change-request
description: Fast path for a small change to an existing interface - impact analysis, mini scope contract, surgical change, verification, delivery. Use for small CRs where the full lifecycle would be overkill; escalates to the full pipeline if impact analysis shows the change is not small.
argument-hint: <change description or CR reference> [task-id]
---

# /change-request — small change, full discipline

> Framework files: `<root>` is what `ses root` prints — run it once. Every
> framework script runs as `ses <command>` (`ses help` lists them). If `ses`
> is not on PATH, stop and ask the user to install the framework (README →
> Install) — never guess its location.

The compressed pipeline: `analyze → mini-contract → change → verify → deliver`.
Small change does NOT mean lowered standards — it means fewer documents, same
verification, same scope discipline.

## 0. Preamble

1. Load applicable lessons: `ses lessons change-request` — it prints only
   the matching entries; don't read the lesson files whole.
2. Resolve `<work-repo>`, `<workspace-root>`, and the `<repo-set>` per
   `<root>/core/repo-resolution.md` (cwd is not assumed to be
   the repo; sibling repos are in analysis scope by default), then create the
   workspace:
   `ses new-task <task-id> auto change-request <work-repo> <repo-set>`
   (or resume from an existing workspace, taking all of them from
   `ses status show <ws>`, where `<ws>` =
   `<workspace-root>/work/<id>`).
3. Store the CR text as `<ws>/brief.md`.
4. Unknowns follow `<root>/core/decision-protocol.md`:
   proceed-and-log only for high-confidence, reversible, in-scope calls
   (→ ASSUMPTIONS.md); interface-contract and data questions always ask.

## 1. Impact analysis

1. Read the target interface fully (spec and body / whole script, not just the
   lines to change).
2. Find ALL callers and dependents **in every repo of `<repo-set>`** (from
   STATUS.md, else enumerate with
   `ses list-repos <repos-folder>` and record the
   list): search object/proc/script names, imports, scheduler references,
   config and deployment manifests with
   `ses search --ws <ws> -- <patterns>` — counts first in every
   repo, then open only the hits that matter. Paste its per-repo rows
   (command, sha, result) into analysis.md, including repos that returned
   nothing — "no other repo uses this" is
   a claim, and on the fast path it is the claim most likely to be wrong,
   because the change looks small precisely when nobody has looked outside the
   obvious repo. Cite findings as `<repo>:<path>:<line>`.
3. Read the rules files `ses repo-rules <work-repo> <files>`
   lists, and follow them; none listed → framework `standards/` plus the
   surrounding code's style.
4. Write `<ws>/analysis.md`: current behaviour (source-referenced),
   callers found, blast radius, and the proposed change sketch. Then
   `ses status set <ws> analyze=done`.

**Escalation rule**: if the analysis shows >3 objects changing, an interface
contract change affecting external callers, data migration, or **changes
landing in more than one repo** (coordinated branches and a deploy order are
not a fast-path change) — tell the user this is not a small change and
recommend the full pipeline (/intake). Let them
decide; record the decision and its reason at the top of `analysis.md`. For borderline
cases the user keeps on the fast path, recommend running /grill against analysis.md before coding.

## 2. Mini scope contract (approval gate)

Append to `analysis.md` and get explicit user approval before touching code
(present any open ASSUMPTIONS.md entries alongside, decision-protocol §4):

- **Change**: exactly what will change (objects, behaviour before → after)
- **Not changing**: adjacent things deliberately left alone
- **Acceptance criteria**: how each is verified (≥1 per change, plus a
  regression check per impacted caller)
- **Rollback**: the exact revert/redeploy step

On approval: `ses status set <ws> mini-contract=approved --note "by <who>"`.

## 3. Change

0. Gate: `ses status require <ws> mini-contract=approved` — non-zero exit = stop.
1. Branch per the repo rules (else the repo's existing branch naming).
   Only the repos the mini contract names are touched — a caller found in
   another repo is reported, not quietly fixed.
2. Surgical diff only. Anything else you itch to fix → PARKED.md.
3. Follow the rules of the repo the file lives in (`ses repo-rules <repo>
   <file>` — not necessarily `<work-repo>`'s), then the surrounding code's
   style, then the standards defaults.
4. Record the branch (`ses status field <ws> branch.<repo-name> <branch>`) and
   `ses status set <ws> change=done`. Nothing is committed yet — commits
   follow verification (§4), so each carries the hashes of the evidence that
   proves it.

## 4. Verify

1. Run /verify-code recipes on every changed file (live via `$SES_DB_CONN`/
   `$SES_KSH_HOST`/`$SES_PY` where reachable; static fallback recorded).
2. Run the regression checks for the impacted callers from §1 — the change
   isn't verified until its callers still work.
3. Capture everything to `evidence/` with
   `<root>/templates/test-evidence.md`, running each command
   through `ses capture` (raw logs land in `evidence/raw/`;
   only its summary goes into the evidence file).
4. All PASS → commit, one commit per logical unit referencing the task id:
   - first inspect the repo's `commit-msg` hook and follow its exact format
     (as /implement §1 step 4 — the hook, not recent history, decides);
   - end each message with its evidence hash lines from
     `ses checkpoint trailer <ws> <evidence files>`
     (`git commit -m "<subject>" -m "<trailer lines>"`).
   Then `ses status set <ws> verify=done`.

## 5. Deliver

1. Self-check `<root>/checklists/change-request.md`. For
   multi-file changes, also run the audit procedure in
   `<root>/agents/scope-auditor.md` against the mini contract
   (subagent where supported, otherwise a separate fresh pass), passing
   `analysis.md` as the contract.
2. Short release note (template: release-notes.md, trimmed): change, deploy
   step, rollback step, evidence table.
3. Push the branch; report to the user; `ses status set <ws> deliver=done`; offer
   /retro (a one-lesson retro is fine for CRs).

## Fault tolerance

Same recovery model as /implement: STATUS.md + branch commits + evidence/ let
any session resume mid-CR without redoing the analysis. On resume run
`ses checkpoint resume <ws>`; exit 3
means uncommitted work — show it and ask keep-or-discard, never fold it in
silently. Each commit ends with the evidence hash lines from
`ses checkpoint trailer <ws> <evidence files>`; /deliver's audit verifies them.
