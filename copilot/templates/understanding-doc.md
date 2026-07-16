# Understanding Document — {INTERFACE / COMPONENT NAME}

- Repo: {repo}@{commit}
- Interface type: {batch job | online/API | data pipeline | report/extract | library}
- Scope of this document: {which parts are covered, which are not}
- Produced: {date} — all statements verified against the code at the commit above.

<!-- Emphasis by interface type (keep all sections; go deep where it matters):
     batch job     → §3 flow, §6 dependencies (schedule!), §7 errors/recovery
     online/API    → §2 entry points, §6 consumers, §7 error contract
     data pipeline → §5 data, §6 upstream/downstream, §7 restartability
     report        → §5 data lineage, §6 consumers, refresh schedule
     The SAME type always uses the SAME emphasis — consistency per type. -->

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

## 6. Dependencies & associated objects — the complete picture

<!-- Both directions, exhaustively. Record the grep/queries used so the map
     is reproducible. "None found" requires showing the search that found none. -->

### Dependency map

<!-- Drawn FROM the tables below — every node/edge here must have a table row,
     and vice versa (the fact-checker verifies both directions). Group with
     subgraphs; style the interface itself distinctly. -->
```mermaid
flowchart LR
    subgraph upstream [Upstream]
        U1[{feed file / source table}]
        U2[{scheduler entry}]
    end
    subgraph iface [{THIS INTERFACE}]
        M[{main package / script}]
        A1[{associated pkg_x}]
    end
    subgraph downstream [Downstream]
        D1[{consumer job / datamart}]
    end
    U2 -->|triggers| M
    U1 -->|read by| M
    M --> A1
    M -->|produces {file/table}| D1
```

### Upstream (what this interface depends on)

| Dependency | Type | How used | Source |
|---|---|---|---|
| {feed file / table / package / service} | {…} | {…} | {file:line / query} |

### Downstream (what depends on this interface)

| Consumer | Type | What it consumes | Source |
|---|---|---|---|

### Associated objects

| Object | Type | Relationship | Source |
|---|---|---|---|
| {pkg_x} | PL/SQL package | {called by main proc for …} | {…} |
| {run_x.ksh} | KSH | {wrapper / scheduler entry} | {…} |

### Schedule / triggers

| Trigger | Where defined | When |
|---|---|---|

### Configuration

| Parameter / env var / config file | Where set | Effect |
|---|---|---|

## 7. Error handling & recovery

{How failures surface (return codes, log locations, alert tables) and how the
interface is restarted/recovered. Source references required.}

## 8. Operational notes

- Logs: {where}
- Monitoring: {what watches this}
- Known quirks: {verified ones only; suspicions marked as such}

## 9. Open questions / unverified areas

{Anything the code alone could not answer.}
