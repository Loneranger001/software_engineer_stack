---
name: document
description: Produce a how-to guide, knowledge-base article, or understanding document for an existing interface or component - fully verified against the code, fact-checked, and converted to the needed formats. Use when the user asks for documentation of existing functionality.
argument-hint: <howto|kb-article|understanding-doc> <interface/component/topic>
---

# /document — code-verified documentation

> Path note: `${CLAUDE_PLUGIN_ROOT}` is this framework's root — the ancestor
> directory of this file containing `plugin.json`/`skills/`. Claude Code resolves
> it automatically; other harnesses resolve it from this file's location.

Pipeline: `analyze → draft → fact-check → deliver`. The defining rule: this
skill documents what the code DOES, not what anyone believes it does.

## 0. Preamble

1. Load lessons tagged `stage:document` from
   `${CLAUDE_PLUGIN_ROOT}/knowledge/lessons.md`.
2. Determine the doc type; if not given, ask:
   - **howto** — a procedure someone performs (template: howto.md)
   - **kb-article** — answers a recurring question/problem (template: kb-article.md)
   - **understanding-doc** — explains how an interface/component works
     (template: understanding-doc.md)
3. Create the workspace:
   `${CLAUDE_PLUGIN_ROOT}/scripts/new-task.sh <task-id> <root> document`
   (or resume). Record doc type + target in STATUS.md.
4. Agree the scope with the user in two sentences (which component, which
   aspects, intended audience) and record it in STATUS.md — even docs tasks
   get scope discipline.
5. Unknowns follow `${CLAUDE_PLUGIN_ROOT}/core/decision-protocol.md`: for
   documentation, "check checkable facts" means read/run the code — a claim
   you can't verify is labelled, never guessed confidently.

## 1. Analyze

1. Read the target code completely: entry points, config, callers, data
   objects, error paths, logs. For an interface: trace one real flow
   end-to-end before writing anything.
2. Where the environment is reachable, RUN things to confirm behaviour
   (queries, `--help`, dry-run modes) and capture outputs to `evidence/`.
   For a howto: execute each step yourself where safe; steps you could not
   execute are marked `⚠ UNVERIFIED` in the final doc.
3. Build a fact table as you go: claim → source (`file:line` / run output).
   This becomes the doc's verification section.

## 2. Draft

1. Fill the matching template into `work/<id>/<doc-name>.md`.
2. Write for the stated audience; lead with the short answer / purpose.
3. Every behavioural statement must trace to the fact table. Suspicions and
   folklore are either verified or explicitly labelled as open questions.
4. Diagrams: use mermaid for flows (renders in Markdown, survives conversion).

## 3. Fact-check gate

1. Run the fact-check procedure in
   `${CLAUDE_PLUGIN_ROOT}/agents/doc-fact-checker.md` on the draft — as a
   subagent where the harness supports it, otherwise as a separate fresh pass
   in its report format. It re-verifies each claim against the code; resolve
   every finding (fix the doc or the fact table).
2. STATUS.md → `fact-check: done`.

## 4. Deliver

1. Ask which output formats are needed (or read from STATUS.md); convert via
   `${CLAUDE_PLUGIN_ROOT}/scripts/md2docx.sh | md2pdf.sh | md2confluence.sh`
   into `work/<id>/deliverables/`.
2. Present the doc; note any `⚠ UNVERIFIED` steps and open questions so the
   user can close them.
3. STATUS.md → `deliver: done`.

## Fault tolerance

The fact table in the draft doubles as the resume point — on interruption,
the next run reads it and continues analysis from the first unsourced section.
