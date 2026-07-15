# Understanding Document — {INTERFACE / COMPONENT NAME}

- Repo: {repo}@{commit}
- Scope of this document: {which parts are covered, which are not}
- Produced: {date} — all statements verified against the code at the commit above.

## 1. Purpose

{What this interface/component exists to do, in business terms.}

## 2. At a glance

| Aspect | Value | Source |
|---|---|---|
| Entry points | {proc / script / endpoint} | {file:line} |
| Trigger / schedule | {cron, event, manual} | {…} |
| Inputs | {files, tables, parameters} | {…} |
| Outputs | {files, tables, return codes} | {…} |
| Key configuration | {…} | {…} |

## 3. End-to-end flow

```mermaid
flowchart TD
    {diagram of the main path}
```

{Narrative walk-through of the flow. Reference each hop: file:line.}

## 4. Components

### 4.1 {Component}

- Location: {path}
- Responsibility: {…}
- Key logic: {described with file:line references}
- Error handling: {…}

## 5. Data

| Table / file | Read/Write | Role | Notes |
|---|---|---|---|

## 6. Error handling & recovery

{How failures surface (return codes, log locations, alert tables) and how the
interface is restarted/recovered. Source references required.}

## 7. Operational notes

- Logs: {where}
- Monitoring: {what watches this}
- Known quirks: {verified ones only; suspicions marked as such}

## 8. Open questions / unverified areas

{Anything the code alone could not answer.}
