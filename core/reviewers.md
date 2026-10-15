# Running a reviewer — scope-auditor, code-reviewer, doc-fact-checker

The reviewers judge work without inheriting the author's context, so they run
apart from the session that produced the work. Use the first option the
harness offers:

1. **The installed agent of that name** — Claude Code plugin:
   `software-engineer-stack:<name>`; Copilot plugin: `<name>`; Codex: `<name>`
   when `ses setup codex` registered it.
2. **A fresh subagent** (Claude Code's Agent tool, Copilot's task agent,
   Codex's spawn_agent) told to read `<root>/agents/<name>.md` in full,
   follow it exactly, and stay read-only.
3. **No subagents at all** — run the procedure yourself as a separate, fresh
   pass: re-read every input from disk rather than from memory of writing it,
   and hold yourself to the report format.

Every delegation prompt carries the inputs the procedure lists (task
workspace path, repos with branch and mainline, or the documents), plus the
`ses` command you resolved and `<root>` — a subagent may not have `ses` on
PATH. The report comes back to the calling skill, whose gate acts on it.
