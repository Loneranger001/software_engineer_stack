# Writing style — how these documents read

The shared prose policy for the documents this framework produces. The register
is fixed: **a senior engineer explaining a change to the colleague who will
maintain it.** Precise, plain, unhurried, nothing being sold. Not a
specification read aloud, not a release announcement, not a chat message.

The test for any sentence: could the maintainer act on it, and would a
competent engineer have written it that way?

## 1. One sentence, one idea

Aim for 15–25 words. A sentence carrying three clauses is three sentences.
Split on the connective instead of escalating the punctuation.

> The job, which runs nightly and is triggered by the scheduler, writes the
> extract file — assuming the previous run completed — to the outbound
> directory, from where the datamart collects it.

> The scheduler runs the job nightly. It writes the extract file to the
> outbound directory, and the datamart collects it from there. A failed
> previous run blocks the next one (§8 Restartability).

At most one em dash per paragraph, and never to bolt on a clause that should
have been its own sentence. A semicolon joins two short related clauses or
nothing at all.

## 2. Name the actor

Active voice with a real subject — the package, the job, the caller, the
operator, *we*. Use the passive only where the actor is genuinely unknown, and
never for a decision.

- "It was decided that the file layout would be extended."
  → "We extend the file layout with a fourth field."
- "Validation is performed before the insert."
  → "`pkg_balance.load_rates` validates each row before inserting it."

If you cannot name the actor, you do not yet understand the design well enough
to write the section.

## 3. Verbs, not noun stacks

Turn nominalisations back into verbs, and never stack three nouns.

- "performs a validation of" → "validates"
- "provides support for" → "supports"
- "the batch job scheduling configuration parameter"
  → "the parameter that schedules the batch job"

## 4. Say the thing, then stop

Cut words that carry no information. Banned outright, no substitute needed:
*leverage, utilise/utilize, robust, seamless, comprehensive, holistic,
streamline, facilitate, best-in-class, significantly, various, a number of.*
Banned openers: *Additionally, Furthermore, Moreover, It is important to note
that, It should be noted that, In order to* (→ "to"), *As mentioned above.*

Prefer the ordinary word: *use* not *utilise*, *before* not *prior to*,
*change* not *modification*.

Never restate the heading. Under `## 5. Data model changes`, the sentence
"This section describes the data model changes" is a wasted line — start with
the change.

These lists are examples of a habit, not the whole rule. Swapping a banned word
for a synonym of the same emptiness fails this section just as hard.

## 5. One name per thing

Fix each object's name at first use and never vary it for elegance. The table
is `BALANCE_SNAPSHOT` in every section — not "the snapshot table", "the
balances table", "the snapshot". Business terms come from the work repo's
`.domain-glossary.md`, used exactly as the entry defines them.

Synonym variation is how two readers end up believing two different designs.
It also breaks matching: the fact-checker, the traceability table, and
/implement all compare names as exact strings.

## 6. Commit, or say plainly that you are not

Hedges do not stack. One qualifier per claim, and only where the uncertainty is
real: "may potentially be able to" is either "can" or an open question. Where
something is genuinely unknown, name it in the document's own vocabulary — an
open question row, a risk row, an `INFERRED` label — rather than blurring it
into soft prose. An admitted gap keeps trust; a confident guess destroys it the
first time the reader checks.

Never write "simply", "just", "obviously", or "should be straightforward". The
reader who is finding it hard now doubts the document.

## 7. Prose earns its place beside a table or diagram

These documents are mostly tables. A paragraph next to one says what the reader
could NOT deduce from it: why this shape, which hop is fragile, what breaks if
the assumption fails. A paragraph that narrates the rows ("The table above
shows four objects…") gets deleted, not improved.

## Gate

Before the document goes to its approval gate, read its prose back at the pace
of a tired reader and confirm:

1. No banned word or opener survives, and no section restates its heading.
2. No sentence carries more than one idea or hides its actor.
3. Each object and business term uses one name throughout.

Brevity is not the target — comprehension is. A five-word sentence that hides
the actor still fails §2.
