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
