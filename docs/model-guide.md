# Model guide — which model to run each stage on

Every stage of this framework is driven from the same model picker, but the stages are not the same
kind of work. `/repo-profile` skims a repo and summarises it; `/grill` has to think of the edge cases
nobody wrote down. Running the first on a frontier model wastes an order of magnitude of budget;
running the second on a cheap tier silently degrades every artifact downstream of it.

This guide assigns one model and one effort level per stage, with a cross-provider alternative and the
condition under which the alternative is the better pick.

**The selection principle, once:** *spend where the error is silent; save where a gate or a harness
catches it.* Then, among models that clear the bar, take the cheaper one.

The framework makes that principle unusually easy to apply, because it already tells you where the
catches are:

| Stage has… | Examples | Consequence |
|---|---|---|
| A **human approval gate** | `/intake` scope contract, `/tech-design` TDD, `/impl-plan` impl doc | You read it before anything proceeds — a cheaper model's slip is caught by you |
| An **automated harness** | `/implement` → per-step `/verify-code` + checkpoint commits + `code-reviewer`; `/document` → `doc-fact-checker`; `/deliver` → `scope-auditor` | Mechanical errors surface before the stage closes |
| **Neither** | `/grill` (a case never raised is never missed), `/research` (a fabricated source reference looks like a real one), `code-reviewer` (a bug it doesn't report ships) | This is where frontier spend actually pays |

> **Verified 2026-08-13.** Model names, prices and Copilot multipliers change monthly. Re-check the
> Copilot model picker and [Models and pricing for GitHub Copilot](https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing)
> before treating any number here as current. See [§7](#7-what-things-cost) for how to refresh.

---

## 1. The provider families, and what each is actually best at

The three families are genuinely differentiated right now, so the table below assigns stages to
whichever family wins that stage rather than defaulting to one vendor.

**OpenAI — GPT-5.6 (Sol / Terra / Luna).** Benchmarked deliberately on *agentic* work: Terminal-Bench,
Agents' Last Exam, BrowseComp, OSWorld. Sol lands within about a point of frontier intelligence while
completing tasks in roughly 61% less time at about half the cost, and adds a `max` reasoning-effort
level above `high`. Terra is the price-performance sweet spot ($1/$6). Luna ($0.10/$0.60) is the
cheapest credible coding tier by a wide margin — it still scores 74.6 on the Artificial Analysis Coding
Agent Index against Sol's 80. **Known weak spot:** SWE-Bench Pro — resolving real issues in real repos —
is the one benchmark where GPT-5.6 trails Claude significantly. That single fact decides `/implement`.

**Anthropic — Claude 5 (Opus / Sonnet).** Leads exactly where GPT-5.6 trails: multi-file repository
surgery, and code review with high precision *and* recall (and it holds that accuracy at lower effort,
which makes it cheaper to use well than its headline price suggests).

**Google — Gemini (3.1 Pro / 3.7 Flash).** The cheapest 1M-context frontier reasoning ($2/$12), and
Flash is the cheapest fast tier after Luna. This is the long-context escape hatch: reach for it when
"how much can I read in one pass" is the binding constraint rather than "how well can I reason".

**Open-weight.** Not in Copilot's picker; see [§8](#8-appendix--open-weight--byok) if you run the
AGENTS.md tier or your own endpoint.

### Effort levels across providers

The `effort` column below is written once and reads correctly whichever family you pick:

| This guide says | Anthropic | OpenAI | Google |
|---|---|---|---|
| `low` | `effort: low`, thinking off for pure mechanics | reasoning effort `low` | minimal thinking budget |
| `medium` | `effort: medium` | reasoning effort `medium` | moderate thinking budget |
| `high` | `effort: high` (the default) | reasoning effort `high` | high thinking budget |
| `xhigh` | `effort: xhigh` — the documented sweet spot for coding/agentic work | between `high` and `max` on Sol | max thinking budget |
| `max` | `effort: max` | Sol's new `max` level | — |

Where Copilot doesn't expose an effort control for a given model, the model choice carries the whole
decision — pick one tier up rather than trying to compensate with prompt text.

---

## 2. Stage-by-stage

| Stage | Recommended | Effort | Why this family wins here | Alternative (and when) |
|---|---|---|---|---|
| `/repo-profile` | **GPT-5.6 Luna** | low | Wide, shallow read across many files; summarisation, not judgment. Output is cached in `.conventions.md` and you review it | Gemini 3.7 Flash when the repo won't fit and you want 1M context in one pass |
| `/intake` | **GPT-5.6 Terra** | high | Requirement parsing plus ambiguity/out-of-scope detection on a small input — and the scope contract is user-approved before anything downstream runs, so the gate absorbs the residual risk at $1/$6 | Claude Sonnet 5 `high` for a vague, multi-system brief where gap-hunting *is* the job |
| `/research` | **GPT-5.6 Terra** | high | Agentic search is precisely what the GPT-5.6 suite is tuned and benchmarked on. The hard rule here is "every finding carries a source reference", not code surgery | Gemini 3.1 Pro for read-heavy sweeps of a large legacy codebase; Sol `high` if research keeps coming back shallow |
| `/tech-design` | **Claude Opus 5** | xhigh | The TDD is the contract for everything after it — a structural error costs the whole downstream pipeline. Highest-leverage spend in the stack | GPT-5.6 Sol at `max`: near-frontier at roughly half the cost and much faster, when design turnaround matters more than the last few points |
| `/grill` | **Claude Opus 5** *and* **GPT-5.6 Sol** — two passes, union the findings | xhigh / `max` | Pure recall of cases nobody wrote down; nothing downstream catches a case that was never raised. **Diversity beats size here** — two providers' blind spots barely overlap, and Sol's `max` level exists for this shape of problem | Single-pass Sol at `max` when budget forces one run; add Gemini 3.1 Pro as a third opinion on the data and lifecycle categories |
| `/impl-plan` | **GPT-5.6 Terra** | high | Bounded, format-heavy decomposition of an *already-approved* TDD into ordered steps, test plan and rollback — behind a user gate. $1/$6 against $3/$15 for no measurable loss | Claude Sonnet 5 `high` when the plan spans package specs and bodies plus a data migration, and step ordering is genuinely load-bearing |
| `/implement` | **Claude Sonnet 5** | xhigh | The one stage where the provider choice isn't close: SWE-Bench Pro (real issues, real repos, multi-file) is where GPT-5.6 measurably trails Claude, and PL/SQL package work is exactly that shape. **Escalate to Opus 5 `xhigh`** when the impl doc has more than ~8 steps, touches package specs/bodies, or includes a data migration | GPT-5.6 Terra for mechanically-specified steps (config, boilerplate KSH, straight CRUD). Per-step verification and checkpoint commits make it safe to mix models *per step* |
| `/verify-code` | **GPT-5.6 Luna** | low (thinking off) | Runs fixed recipes and captures output; interpretation is mostly pass/fail. Hand a genuinely puzzling failure back to the `/implement` model instead of upgrading this stage | Gemini 3.7 Flash if you'd rather have one Flash-tier vendor across all the cheap stages |
| `code-reviewer` agent | **Claude Opus 5** | high | High precision *and* recall on real bug-finding, and it holds accuracy at lower effort — so `high`, not `xhigh`. A bug the reviewer misses ships | **GPT-5.6 Sol as a second reviewer** on risky diffs — different false-negative profile, so union the findings. A supplement, not a replacement |
| `doc-fact-checker` agent | **GPT-5.6 Terra** | medium | Literal claim-versus-code matching at high volume; wants literalness, not creativity | Claude Sonnet 5 `medium` for TDDs and understanding docs, where claims are inferential rather than lookup-able |
| `scope-auditor` agent | **GPT-5.6 Terra** | medium | Narrow checklist comparison of the diff against the scope contract | Luna for single-file change requests |
| `/document` | **Claude Sonnet 5** | high | Prose quality carries the deliverable, and `doc-fact-checker` already gates accuracy | GPT-5.6 Terra for KB articles regenerated from an existing interface map |
| `/understand` | **GPT-5.6 Terra** | high | Interactive Q&A — latency matters as much as depth, and Terra is cheap and fast enough to iterate against | Gemini 3.1 Pro when the trace spans a very large codebase and 1M context is the binding constraint |
| `/change-request` | **Claude Opus 5** for the impact analysis → **Claude Sonnet 5** for the change | high → xhigh | Misjudging "is this actually small?" is *the* CR failure mode, and no full-pipeline gate sits behind it. The change itself is `/implement`-shaped, so it inherits that stage's reasoning | GPT-5.6 Sol `high` for the analysis when the interface is already well understood; Terra throughout for a one-object, one-language CR |
| `/deliver` | **GPT-5.6 Terra** | medium | Assembly, release notes and pandoc conversions; `scope-auditor` is the real gate | Luna for the conversion and bundling mechanics alone |
| `/retro` | **Claude Sonnet 5** | high | Judging which stumbles *generalise* into lessons is the whole task, and a bad lesson poisons every future run's preamble. The input is tiny, so the cost is negligible | GPT-5.6 Terra `high` when you're only appending mechanical lesson entries |
| `/meeting-minutes` | **GPT-5.6 Luna** | low | High input, low reasoning; structured summarisation | Gemini 3.7 Flash for very long transcripts |

**The shape of that assignment:** OpenAI carries the agentic-and-bounded middle (`/intake`, `/research`,
`/impl-plan`, `/understand`, `/deliver`, both cheap reviewer agents) and the whole cheap tier
(`/repo-profile`, `/verify-code`, `/meeting-minutes`). Anthropic holds the four places where errors are
silent and expensive (`/tech-design`, `/implement`, `code-reviewer`, CR impact analysis) plus the
prose-led `/document` and `/retro`. `/grill` runs both on purpose. Gemini is the long-context escape
hatch throughout.

---

## 3. Three ready-made configurations

**Balanced** — the table above. This is the default recommendation.

**Cost-capped** — when premium requests are the constraint:

| Change from balanced | Risk you're accepting |
|---|---|
| Terra replaces Sonnet 5 on `/document`, `/retro` | Flatter prose; lessons that generalise less well |
| Single-pass Sol `max` replaces the two-model `/grill` | Loses the cross-provider blind-spot coverage — the main reason `/grill` exists |
| Luna replaces Terra on `/deliver`, `scope-auditor`, `doc-fact-checker` | Weaker claim-checking; lean harder on your own read of the evidence bundle |
| Opus 5 → Sonnet 5 on `/tech-design` and `code-reviewer` | Design gaps and missed bugs — the two failure modes with no gate behind them |

Keep `/implement` on Sonnet 5 even here; downgrading it converts saved tokens into re-work.

**Quality-first** — Opus 5 from `/research` through `code-reviewer`; `/grill` at `max` on both
providers; `/implement` on Opus 5 `xhigh` unconditionally. Still use Luna for `/repo-profile`,
`/verify-code` and `/meeting-minutes` — there is no quality upside available on those.

---

## 4. Effort settings — the parts that bite

- **`high` is the sensible default**; `xhigh` is the documented sweet spot for coding and agentic work.
- **`max` is not a free upgrade.** It shows diminishing returns and can overthink simple tasks. Reserve
  it for `/grill` and for design work on high-blast-radius changes.
- **Don't disable thinking on Claude Opus 5 to save money.** With thinking off it can occasionally write
  a tool call into its visible text instead of emitting a real tool call — the turn completes, the call
  never runs, and nothing errors. Inside `/implement`'s step loop that's a step that silently didn't
  happen. It can also leak `<thinking>` tags into output. Lower `effort` instead; `low`/`medium` on
  Claude 5 are strong and already cut most of the cost.
- **At `xhigh`/`max`, allow a large output budget** (≥64K where you control it) so long stages don't
  truncate mid-step.
- Lower effort makes models more literal and more scope-bound. That's a feature for `/impl-plan` and
  `/verify-code`, and a liability for `/grill`.

---

## 5. Prompting notes that change the model math

Three places where a prompt change is worth more than a model upgrade:

**`code-reviewer` and severity filters.** Current models follow "only report high-severity issues" or
"be conservative, don't nitpick" *literally*. They still find the bugs — they just decline to report
findings below the stated bar, so measured recall falls while precision rises. Ask for every finding
with a confidence level and an estimated severity, and filter downstream. This recovers more real bugs
than moving up a model tier.

**`/grill` and model diversity.** Two mid-tier models from different providers surface a wider union of
edge cases than one frontier model run twice. The stage's whole value is coverage, so buy coverage.

**Prompt caching and when to switch models.** Every stage re-reads the same framework files
(`knowledge/lessons.md`, `core/decision-protocol.md`, `standards/`, the templates). Keeping that
preamble byte-stable is what makes the cheap picks genuinely cheap. Switching model mid-task discards
the cache — so **switch models at stage boundaries**, which is exactly where `STATUS.md` makes it safe
to stop and restart anyway.

---

## 6. How to actually set the model

This framework does not pin models — no skill or agent here sets one, deliberately, so the guide can
stay advisory while prices move. Selection is a harness action:

- **GitHub Copilot** — the model picker in Chat/agent mode, per session. Since the recommendation
  changes between stages, switch it when you switch stages (§5 explains why that's also the cheap
  moment to do it).
- **Claude Code** — `/model` before invoking the stage.
- **API / opencode / AGENTS.md tier** — whatever your client sets per request.

If you'd rather have the three reviewer agents pinned rather than inherited, adding a `model:` line to
`agents/*.md` works in Claude Code; note that `scripts/build_copilot.py` currently emits only
`name`/`description` into the generated `.agent.md` files, so it would need a generator change to reach
Copilot. That's a deliberate non-goal of this guide.

---

## 7. What things cost

**On Copilot, the currency is the premium-request multiplier**, not tokens. Approximate, and volatile:

| Tier | Multiplier |
|---|---|
| Claude Opus class | ~27× |
| Claude Sonnet class | ~9× |
| Gemini Pro / GPT Codex class | ~6× |
| Flash / Luna class | ~1× or included |

Those multipliers have moved sharply and repeatedly (Opus went 7.5× → 15× → 27× inside 60 days at one
point). Treat the table as a shape, not a quote.

**API list prices** (per 1M tokens, input/output):

| Model | Input | Output |
|---|---|---|
| Claude Opus 5 | $5.00 | $25.00 |
| Claude Sonnet 5 | $3.00 | $15.00 |
| GPT-5.6 Sol | $2.50 | $15.00 |
| GPT-5.6 Terra | $1.00 | $6.00 |
| GPT-5.6 Luna | $0.10 | $0.60 |
| Gemini 3.1 Pro | $2.00 | $12.00 |
| Gemini 3.7 Flash | $0.75 (intro) | $3.75 (intro) |

Gemini 3.7 Flash's introductory rate runs to 2026-12-31, after which it doubles to $1.50/$7.50. Gemini
Pro pricing rises to $4/$18 for prompts above 200K tokens — relevant if you take the long-context
alternative on `/research` or `/understand`. OpenAI and Anthropic both discount cached input heavily,
which is the other half of the §5 caching point.

**To refresh this section:** check the Copilot picker plus
[Models and pricing for GitHub Copilot](https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing),
then the three provider pricing pages —
[OpenAI](https://developers.openai.com/api/docs/pricing),
[Anthropic](https://platform.claude.com/docs/en/about-claude/models/overview),
[Google](https://ai.google.dev/gemini-api/docs/pricing) — and update the date stamp at the top. If a
model in the stage table has been retired, replace it with the same *tier* from the same provider
rather than re-deriving the whole table; the assignments are driven by stage shape, not by specific
model versions.

---

## 8. Appendix — open-weight / BYOK

None of these are in Copilot's picker today; they apply if you run the AGENTS.md tier, opencode, or
your own endpoint.

| Model | Use it for | Note |
|---|---|---|
| **Kimi K3** | `/research`, `/understand` | Strongest open all-rounder, ~1M context |
| **GLM-5.2** | `/implement`, long-horizon agent runs | The open substitute where Claude is recommended; strong on SWE-Bench Pro-style work |
| **DeepSeek V4 Pro** | `/tech-design`, `/grill` on a budget | ~80.6% SWE-bench Verified at roughly $0.435/$0.87 |
| **Qwen3-Coder / Qwen3.6-27B** | `/verify-code`, `/repo-profile`, air-gapped work | Runs on a single consumer GPU; the practical pick when code cannot leave the building |

For a PL/SQL and KSH codebase specifically, verify any open-weight pick on your own code before
trusting it on `/implement` — these languages are far less represented in training data than Python or
TypeScript, and the gap between models widens there.

---

## Sources

Pricing, benchmarks and availability referenced above, as of 2026-08-13:

- [Models and pricing for GitHub Copilot](https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing) · [Supported AI models in GitHub Copilot](https://docs.github.com/en/copilot/reference/ai-models/supported-models)
- [GPT-5.6 benchmarks across Intelligence, Speed and Cost — Artificial Analysis](https://artificialanalysis.ai/articles/gpt-5-6-has-landed) · [GPT-5.6 Sol vs Terra vs Luna — Vellum](https://www.vellum.ai/blog/gpt-5-6-sol-terra-luna-explained) · [OpenAI API pricing](https://developers.openai.com/api/docs/pricing)
- [Claude models overview](https://platform.claude.com/docs/en/about-claude/models/overview) · [Claude model migration guide](https://platform.claude.com/docs/en/about-claude/models/migration-guide)
- [Gemini Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing) · [Introducing Gemini 3.7 Flash](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-3-7-flash/)
- [Best open-weight LLMs for agentic coding 2026 — MindStudio](https://www.mindstudio.ai/blog/best-open-source-llms-agentic-coding-2026)
