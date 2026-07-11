---
name: repo-profile
description: Scan a work repository and infer its conventions and standards into a cached .conventions.md that all other stack skills consult. Use when starting work in a repo that has no .conventions.md yet, or to refresh a stale one.
argument-hint: "[repo-path]"
---

# /repo-profile — learn the repo's own rules

Existing repos have their own conventions, and those ALWAYS beat the framework
defaults in `${CLAUDE_PLUGIN_ROOT}/standards/`. This skill captures them once
into `.conventions.md` at the repo root, so every other skill can honor them.

## 1. Scan

Sample broadly, not exhaustively — read representative files per language
(newest + oldest + largest few), plus any existing docs:

1. **Layout**: where each language lives (src/plsql, sql/, bin/, tools/…),
   deployment/install scripts, test directories.
2. **Existing standards docs**: CONTRIBUTING, README sections, wiki exports,
   `*.standards*` — quote them as authoritative rather than re-inferring.
3. **Per language** (PL/SQL, SQL, KSH, Python — skip absent ones):
   - Naming: objects, variables, parameters (prefixes like p_/v_/g_, case)
   - File organization: one object per file? spec/body split? header blocks?
   - Error handling: exception patterns, error/log tables, return codes
   - Logging: framework packages, print/echo conventions, log locations
   - SQL style: keyword case, alias style, hint usage, ANSI vs old joins
   - Testing: utPLSQL/pytest/harness scripts and how they're invoked
4. **Git**: branch naming, commit message style (scan `git log --oneline -50`),
   tagging/release patterns.
5. **Deployment model**: how DDL/packages/scripts reach environments (install
   scripts, ordering manifests, CI).

## 2. Write .conventions.md

Structure the findings as:

```markdown
# Conventions — <repo> (profiled <date>, commit <sha>)
## Layout
## Git
## PL/SQL       (naming, errors, logging, testing — each with 1-2 real examples file:line)
## SQL
## KSH
## Python
## Deployment
## Unresolved   (things the repo is inconsistent about — note both variants)
```

Rules:

- Every convention cites at least one real example (`file:line`). No example →
  it goes under Unresolved, not asserted.
- Inconsistent repos: record the dominant variant and the exceptions; skills
  should follow the file being edited first, dominant variant second.
- Never copy secrets/connect strings into the profile.

## 3. Cache & staleness

- Write to `<repo>/.conventions.md`. Ask the user whether to commit it or
  gitignore it (teams differ).
- Header records the commit profiled at. Other skills should suggest a refresh
  when the profile is older than ~3 months or the repo has visibly diverged.
- Re-runs: re-profile and diff against the existing file, preserving any
  hand-edits the user made (theirs win — this file is user-ownable).
