# Lessons

> Append-only self-improvement memory, written by /retro. Every stack skill
> reads this at start and applies entries matching its stage/language/repo.
>
> Format (one line per lesson):
> `- [YYYY-MM-DD] [stage:<stage>] [lang:<plsql|sql|ksh|python|->] [repo:<name|->] <actionable lesson> (task <id>)`
>
> Tags: stage = intake|research|tech-design|impl-plan|implement|deliver|
> change-request|document|understand|verify|any. Use `-` when a tag doesn't apply.
> Curation (merging/pruning) only via /retro §4 with user approval.

<!-- lessons below this line -->
- [2026-08-14] [stage:verify] [lang:plsql] [repo:mfcs-rail-int] Compile every changed database object in MFCS DEV as ALASKAR before deployment; inspect compilation errors and explicitly distinguish expected privilege/reference failures from invalid-code errors. (task CHG1-4684)
- [2026-08-12] [stage:research] [lang:sql] [repo:-] For an interface task in a multi-repository workspace, identify all candidate repos from the scope contract, refresh and search each `origin/main`, and profile missing conventions before designing; a nominated repo or feature branch can omit tables, views, and consumers. (task MFCS-4684)
- [2026-08-12] [stage:implement] [lang:-] [repo:-] Inspect the local `commit-msg` hook before the first checkpoint commit and use its exact format; recent history and framework examples can be insufficient. (task MFCS-4684)
