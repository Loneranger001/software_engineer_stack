# Writing standard — documents people read

> Applies to every document people read: the review versions of the
> functional and technical designs (fdd.review.md, tdd.review.md), how-to
> guides, KB articles, understanding documents, and release notes. It does
> not apply to the agent versions of the designs (fdd.md, tdd.md) or to
> other working files (scope contract, research notes, impl doc, grill log,
> STATUS.md, handoff summaries): agents read those, and they are written to
> be complete and exact. A writing rule in the repo's rules files
> (`ses repo-rules`) or a style guide the client prescribes wins where it
> differs.

These rules are a subset of the writing rules of ASD-STE100 Simplified
Technical English. The STE dictionary is not used: business and technical
terms come from the domain glossary and the document's own table of terms.

`ses prose-lint <file>` checks the mechanical rules. It is a floor. A clean
lint does not make a sentence clear, and you fix a finding by rewriting the
sentence, never by working around the pattern.

## 1. Write about the system, not about how the document was made

The reader sees the system. The reader does not see the research, the task,
the scope contract, or the stages that produced the document. These stay in
a workspace that nobody hands over.

- State the fact. Do not say who found it or how.
  - ✗ Research identified no implementation of the resend rule.
  - ✓ The system does not resend an order today.
- Do not use framework words: research, research notes, this task, scope
  contract, workspace, fact-check, or stage names such as /intake or /grill.
- Keep sources out of the text. A review version has none: they stay in
  the agent version. A how-to or KB article keeps them in its source
  section, as code references (`file:line`). Do not cite research-notes.md
  or any other workspace file. The reader cannot open it.
- Keep IDs such as FR1, BR1, or S1 out of the sentences. A review version
  shows none: its hidden `covers:` anchors hold them. Other documents put
  them in a column.
- A fact that you could not check is an open question. Write it as a
  question in the open-questions section.

## 2. Words

- Use one term for one meaning. Use the term from the glossary or from the
  document's table of terms each time. Do not change to a synonym.
- Do not make up terms. If a reader cannot find a term in the table of terms
  or in a dictionary, describe the thing.
  - ✗ the task-owned message / publication identity
  - ✓ the ID that the system gives each message that it publishes
- Do not join words with a slash. Write "or" or "and", or select one word.
  Paths, code, and acronyms such as I/O are not affected.
- Use a maximum of three words in a noun group. Break a longer group with a
  verb or a preposition.
  - ✗ vendor order transmission status update
  - ✓ the system updates the status of each order that it sends to a vendor
- Use a verb, not a noun made from a verb.
  - ✗ Validation of the order is performed.
  - ✓ The system checks the order.
- Use plain words: "use", not "utilize" or "leverage"; "help" or "let", not
  "facilitate"; "to", not "in order to"; "before", not "prior to"; "after",
  not "subsequent to"; "about", not "with respect to". Do not use
  "seamless", "robust", or "going forward". The lint lists these words.

## 3. Sentences

- Write one idea in each sentence.
- A step or an instruction has a maximum of 20 words. Other sentences have
  a maximum of 25 words.
- Use the active voice. Name the actor: the system, the nightly job, the
  buyer. In the numbered steps of a component, the component is the actor,
  so a step can start with its verb.
- Use the present tense for what the system does. In a design for a change,
  the "Before and after" table shows what changes. The steps describe the
  system as it will be.
- Keep the articles (a, an, the). Do not write in telegraph style. A table
  cell can be a short phrase.
- Do not use an -ing word to join two clauses.
  - ✗ On receiving the file, the job loads it.
  - ✓ When the job receives the file, it loads it.
- Put a condition first: "If the vendor does not accept EDI orders, the
  system skips the order."

## 4. Paragraphs and structure

- Write about one topic in each paragraph. A paragraph has a maximum of six
  sentences. Put the main point first.
- Start the document with what the reader needs most: a review version
  with "In short", a KB article with the short answer.
- Use a numbered list for a sequence, a bulleted list for items at the same
  level, and a table for items that have the same attributes. Do not put
  long prose in a table.
- Say each thing in full one time, in the section that owns it. Another
  section names it in a few words and gives its ID: "Check that the vendor
  accepts EDI orders (BR1)." The words must agree with the full statement.

## What the lint checks

| Kind | Finds | Fix |
|---|---|---|
| PROCESS | Words about how the document was made: research, this task, scope contract, workspace, fact-check, stage names, "we found", "analysis shows" | State the fact about the system |
| SLASH | Two words joined by a slash | "or", "and", or one word |
| LONG | A sentence of more than 25 words, or more than 20 in a numbered step | Split it |
| PARAGRAPH | A paragraph of more than six sentences | Split it by topic |
| WORDS | A word from the plain-words list in §2 | The plain word that the lint gives |

The lint does not check HTML comments, fenced blocks, `inline code`, block
quotes (use them to quote a source word for word), the header lines above
the first `##` heading, the handoff summary, headings, table header rows, or
the sections that hold source references (Appendix, Sources, and
Verification of this article).
