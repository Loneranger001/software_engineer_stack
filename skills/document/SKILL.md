---
name: document
description: Produce a how-to guide, knowledge-base article, or understanding document for an existing interface or component - fully verified against the code, fact-checked, and converted to the needed formats. Use when the user asks for documentation of existing functionality.
argument-hint: <howto|kb-article|understanding-doc> <interface/component/topic>
---

# /document — code-verified documentation

> Framework files: `<root>` is what `ses root` prints — run it once. Every
> framework script runs as `ses <command>` (`ses help` lists them). If `ses`
> is not on PATH, use `python3 <skill-dir>/../../bin/ses` in its place —
> `<skill-dir>` is the folder this SKILL.md was loaded from — here and for
> every `ses` below. If neither runs, stop and ask the user (README →
> Install); never guess another path.

Pipeline: `analyze → draft → fact-check → deliver`. The defining rule: this
skill documents what the code DOES, not what anyone believes it does.

## 0. Preamble

1. Load applicable lessons: `ses lessons document` — it prints only
   the matching entries; don't read the lesson files whole.
2. Determine the doc type; if not given, ask:
   - **howto** — a procedure someone performs (template: howto.md)
   - **kb-article** — answers a recurring question/problem (template: kb-article.md)
   - **understanding-doc** — explains how an interface/component works
     (template: understanding-doc.md)
3. Resolve `<work-repo>`, `<workspace-root>`, and the `<repo-set>` per
   `<root>/core/repo-resolution.md` (enumerate with
   `ses list-repos <repos-folder>` and confirm
   the list with the user — the dependency map spans every repo in it), then
   create the workspace:
   `ses new-task <task-id> auto document <work-repo> <repo-set>`
   (or resume, taking both paths from
   `ses status show <ws>`, where `<ws>` =
   `<workspace-root>/work/<id>`). Record doc type + target:
   `ses status field <ws> doc-type <type>` and
   `ses status field <ws> target "<target>"`.
4. Agree the scope with the user in two sentences (which component, which
   aspects, intended audience) and record it:
   `ses status field <ws> doc-scope "<the two sentences>"` — even docs tasks
   get scope discipline.
5. Unknowns follow `<root>/core/decision-protocol.md`: for
   documentation, "check checkable facts" means read/run the code — a claim
   you can't verify is labelled, never guessed confidently.

## 1. Analyze

1. Read the target code completely: entry points, config, callers, data
   objects, error paths, logs. For an interface: trace one real flow
   end-to-end before writing anything. If a previous /understand run left an
   interface map for this target (`<workspace-root>/work/*/interface-map.md`), start from it —
   check its recorded commit for staleness, then deepen rather than re-derive
   (its fact table seeds yours).
   - For an **understanding-doc**, classify the interface type first (batch
     job, online/API, data pipeline, report/extract, library) — the template
     defines which sections get depth per type, and the SAME type must always
     get the SAME emphasis so your documents stay consistent. If the repo's
     rules files (`ses repo-rules`) prescribe a documentation format, it wins;
     a new format choice of yours goes in the workspace (`ses status field <ws>
     doc-format "..."`), not into the team's rules files.
   - Build the **complete dependency map** both directions (upstream feeds,
     downstream consumers, associated packages/scripts, schedules, config) —
     searched with `ses search --ws <ws> -- <patterns>` (every
     repo, counts first) and its per-repo rows recorded so the map is
     reproducible. "Nothing depends on this" requires showing the search
     that found nothing. Then
     draw it as the §6 mermaid diagram (upstream / interface / downstream
     subgraphs, labelled edges) — the diagram and the tables must agree in
     both directions; the fact-checker treats a node without a table row (or
     vice versa) as a finding.
2. Where the environment is reachable, RUN things to confirm behaviour
   (queries, `--help`, dry-run modes) and capture outputs to `evidence/`.
   For a howto: execute each step yourself where safe; steps you could not
   execute are marked `⚠ UNVERIFIED` in the final doc.
3. Build a fact table as you go: claim → source (`file:line` / run output).
   This becomes the doc's verification section.
4. `ses status set <ws> analyze=done`.

## 2. Draft

1. Fill the matching template into `<ws>/<doc-name>.md`.
2. Write for the stated audience; lead with the short answer / purpose.
3. Every behavioural statement must trace to the fact table. Suspicions and
   folklore are either verified or explicitly labelled as open questions.
4. Diagrams: use mermaid for flows (renders in Markdown, survives conversion).
5. `ses status set <ws> draft=done`.

## 3. Fact-check gate

1. Run the fact-check procedure in
   `<root>/com.github.copilot/agents/doc-fact-checker.agent.md` on the draft —
   delegated per `<root>/core/reviewers.md`. It re-verifies each claim against the code; resolve
   every finding (fix the doc or the fact table).
2. `ses status set <ws> fact-check=done`.

## 4. Deliver

1. Ask which output formats are needed (unless `ses status get <ws> formats`
   already answers it) and record them: `ses status field <ws> formats
   "<docx,pdf,...>"`. Convert via
   `ses md2docx | ses md2pdf | ses md2confluence`
   into `<ws>/deliverables/`.
2. Present the doc; note any `⚠ UNVERIFIED` steps and open questions so the
   user can close them.
3. `ses status set <ws> deliver=done`.

## Fault tolerance

The fact table in the draft doubles as the resume point — on interruption,
the next run reads it and continues analysis from the first unsourced section.
