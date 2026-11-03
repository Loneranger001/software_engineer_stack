# Running a reviewer — scope-auditor, code-reviewer, doc-fact-checker, and the design griller

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

## The design griller

`design-griller` (/grill Phase 1) is delegated the same way, with three
differences. It writes — the grill log, the design's gap fixes, evidence —
so it is not read-only. Its prompt carries its inputs and nothing else: no
summary of the design, no expected findings. And option 3 does not apply: a
pass by the session that wrote or discussed the design is the anchoring the
griller exists to avoid. Without a subagent tool, /grill runs Phase 1 only in
a session the user confirms is fresh (`<root>/skills/grill/SKILL.md` §1).
