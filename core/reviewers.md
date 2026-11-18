# Running a reviewer — scope-auditor, code-reviewer, doc-fact-checker

The reviewers judge work without inheriting the author's context, so they run
apart from the session that produced the work. Their procedures live in
`<root>/com.github.copilot/agents/<name>.agent.md`, which the Copilot plugin
also installs as custom agents. Use the first option the harness offers:

1. **The installed custom agent of that name** — `scope-auditor`,
   `code-reviewer`, `doc-fact-checker` (in Copilot, delegate to it as a
   subagent; the user can also pick it with `/agent`).
2. **A fresh subagent** (the harness's task/subagent tool) told to read
   `<root>/com.github.copilot/agents/<name>.agent.md` in full, follow it
   exactly, and stay read-only.
3. **No subagents at all** — run the procedure yourself as a separate, fresh
   pass: re-read every input from disk rather than from memory of writing it,
   and hold yourself to the report format.

Every delegation prompt carries the inputs the procedure lists (task
workspace path, repos with branch and mainline, or the documents), plus the
`ses` command you resolved and `<root>` — a subagent may not have `ses` on
PATH. The report comes back to the calling skill, whose gate acts on it.

## Keep every report, and say how it ran

The calling skill saves each report, whole, the moment it returns — a
review nobody can find later did not happen, as far as a gate or a resumed
session can tell:

```sh
ses review record <ws> <reviewer> <target> --mode <custom-agent|subagent|self-pass> [--doc <file>] [--scope "§…"] <report-file|->
```

`<mode>` is the option above that actually ran (1 = `custom-agent`,
2 = `subagent`, 3 = `self-pass`); `<target>` names what was reviewed — `fdd`,
`tdd`, `tdd-grill` (the grill's scoped re-check), the repo name for each
code-review pass, `delivery` for the /deliver scope audit, `cr` for a change
request, the document's name for /document. A doc-fact-checker report
also names the document it checked (`--doc`, required): it is fingerprinted
then, so record the report the moment it returns, before any edit. It lands in
`<ws>/reviews/<reviewer>-<target>-<n>.md` and in STATUS
(`review.<reviewer>.<target>`). Each gate then checks the latest report
instead of trusting memory: `ses review require <ws> <reviewer> <target>`
exits 3 unless it passes — and, for a doc-fact-checker report, unless the
document is unchanged since it. So an edit made after a PASS (a revision the
user asks for at approval, a lint rewrite, an amendment) cannot reach an
approval unchecked.

A **self-pass** is the author re-reading its own work. It is better than no
review, and much weaker than an independent one: every gate that rests on
one says so to the user in the approval it asks for ("the fact-check was a
self-pass — no independent reviewer was available"), so the user can get an
independent review first.

## Re-checks: scope them by what changed (doc-fact-checker)

A document's first fact-check reads it whole. Every later check is a
re-check, scoped to what changed — after fixing findings, after a revision
at approval, after a lint rewrite, after an amendment or a scope-contract
change. Re-reading every claim to confirm one edited section costs a full
review each round and finds nothing the scoped check would miss.

```sh
ses review changed <ws> <doc>
```

It lists the sections changed, added or removed since the document's last
fact-check (whatever its target: `tdd` and `tdd-grill` both check tdd.md),
plus that report's findings when it did not pass. The re-check covers:

- those sections, and the sections those findings name;
- claims elsewhere that rely on what changed — the caller in §6, the §7 row
  that tests it, the flow that draws it. The reviewer follows these itself
  ("Optional scope" in the doc-fact-checker procedure).

Give the reviewer that list and the findings as its scope. Record the
report with `--scope` naming the sections it covered. The title, the
metadata lines above the first section (Status, Inputs, approval notes) and
the handoff summary are outside the fingerprint, so updating them needs no
re-check; `ses handoff check` holds the summary to the body. A renamed or
moved section shows as removed and added: check the added one.

Check the whole document again only when the code it describes moved under
it (rebased onto a newer mainline, a repo re-pinned), when most sections
changed, or when the user asks.

A task begun before 0.17.0 has reports without a fingerprint, and `changed`
says so. Scope its first re-check by hand to the sections edited since (the
change list, the grill log). Recording that report fingerprints the
document, and from then on `changed` lists the scope.
