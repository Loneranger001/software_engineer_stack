# {Title} — functional design

- Status: draft | approved by {name} on {date}
- For: {who reads it: business owner, UAT testers, …}

<!-- REVIEW VERSION — what people read and approve. Write it from the
     fact-checked fdd.md (the agent version), for the recorded audience, and
     keep it in step: every change to fdd.md changes this file in the same
     edit (checked by: ses review-version check <ws>/fdd.md).
     - Simple first: two pages is the aim, four the most. A reader who stops
       after "In short" knows what changes and what to decide.
     - Plain words and short sentences: <root>/standards/writing.md (check:
       ses prose-lint <file>). No code (ses fdd-lint <file>).
     - Say what the system does. Never say how the design was made — no
       research, task, scope contract, stage names, or sources.
     - No visible IDs. End each paragraph, step, or table row with a hidden
       anchor that names the fdd.md IDs it covers: an HTML comment that
       starts with "covers:", as in the rows below. Every FR, BR, EX, TS and
       Q of fdd.md is covered somewhere.
     - audience=business: no component, table, or column names. A
       technical audience may name components and tables where it helps.
     - A section with nothing to say holds one line ("None."), or is
       deleted when a reader would not miss it. -->

## In short

{Today, a purchase order waits for the weekly run before it goes to the
vendor. After this change, the nightly run sends each approved order on the
day that the buyer approves it. Buyers no longer send EDI orders by hand.}
<!-- covers: FR1 -->

## What changes

<!-- Forward and change modes. Each row is concrete: "orders reach the
     vendor the same night", not "faster processing". As-built mode: rename
     the section "What it does" and use three to six bullets. -->
| | Today | After this change |
|---|---|---|
| {How orders reach vendors} | {A buyer sends them each week} | {The nightly run sends them on the day of approval} <!-- covers: FR1 --> |

## How it works

<!-- One numbered list for the whole flow, in the order a reader would see
     it happen — not one list per component. 20 words at most per step. -->
1. {Each night, the system finds every approved order that it has not sent.}
2. {It checks that the vendor accepts EDI orders. If not, the order goes on
   the buyer's exception report.} <!-- covers: BR1, EX1 -->
3. {It sends the other orders to the vendor and marks them as sent.}

## Rules

- {An order goes to a vendor only if the vendor accepts EDI orders.} <!-- covers: BR1 -->

## When something goes wrong

| What happens | Who finds out | What they do |
|---|---|---|
| {The vendor does not accept EDI orders} | {The buyer, from the exception report} | {Turn on EDI for the vendor, or send the order by hand. The next run sends it.} <!-- covers: EX1 --> |

## Not included

- {Orders that go back to the vendor as returns.}

## How it will be tested

| Situation | Expected result |
|---|---|
| {An approved order for a vendor that accepts EDI} | {The order is in that night's vendor file and is marked as sent.} <!-- covers: TS1 --> |

## Questions for you

1. {Must an order that the vendor rejects twice go to the buyer's manager?} <!-- covers: Q1 -->

## Approval

| Name | Role | Date | Decision |
|---|---|---|---|
