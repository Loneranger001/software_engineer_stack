# Interface Map — {INTERFACE / INTEGRATION NAME}

- Repo: {repo}@{commit}
- Interface type: {batch job | online/API | data pipeline | report/extract | library}
- Intent of this investigation: {orientation | specific question: "…" | pre-change reconnaissance}
- Investigated: {date} — statements verified against the code at the commit above.

<!-- Working map built by /understand. Lighter than an understanding-doc: it
     records what was verified and where, so explanations, Q&A, and later
     stages (/document, /change-request, /intake) build on it instead of
     re-investigating. Same emphasis-by-type rules as understanding-doc.md. -->

## 1. Identity

| Aspect | Value | Source |
|---|---|---|
| Entry points | {proc / script / endpoint} | {file:line} |
| Trigger / schedule | {cron, event, manual, caller} | {…} |
| Inputs | {files, tables, parameters} | {…} |
| Outputs / side effects | {files, tables, return codes, messages} | {…} |
| Key configuration | {…} | {…} |

## 2. End-to-end flow

```mermaid
flowchart TD
    {main path, trigger → final effect}
```

{Narrative of the main path. Every hop: file:line. Error paths included —
how failure surfaces, what state is left, how it recovers.}

## 3. Dependency map

<!-- Both directions, with the searches recorded so the map is reproducible.
     "None found" requires showing the search that found none. Diagram and
     tables must agree in both directions. -->

```mermaid
flowchart LR
    subgraph upstream [Upstream]
        U1[{feed / source / scheduler}]
    end
    subgraph iface [{THIS INTERFACE}]
        M[{main package / script}]
    end
    subgraph downstream [Downstream]
        D1[{consumer}]
    end
    U1 -->|{how}| M
    M -->|{produces}| D1
```

### Upstream (what this interface depends on)

| Dependency | Type | How used | Source |
|---|---|---|---|

### Downstream (what depends on this interface)

| Consumer | Type | What it consumes | Source |
|---|---|---|---|

### Associated objects, schedule, configuration

| Object / trigger / parameter | Type | Relationship / effect | Source |
|---|---|---|---|

### Searches used

| Looking for | Command / query | Result summary |
|---|---|---|

## 4. Fact table

<!-- The backbone of every explanation given, and the resume point. -->

| # | Claim | Source (file:line / query / run output) | Status |
|---|---|---|---|
| 1 | {…} | {…} | verified \| INFERRED |

## 5. Q&A log

| Question | Answer (short) | Source |
|---|---|---|

## 6. Open questions / unverified areas

{What the code and environment alone could not answer, and who could.}
