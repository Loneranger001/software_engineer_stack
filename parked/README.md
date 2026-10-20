# Parked: Claude Code and Codex packaging

The framework currently ships as a **GitHub Copilot** plugin only. The skills
themselves are harness-neutral (every script runs through `ses`, every
framework file is `<root>/…`), so Claude Code and Codex need packaging, not
rewrites. Their manifests are kept here, tested as valid JSON, and inactive:
no harness looks inside `parked/`.

Both were installed successfully with the real CLIs before being parked
(commit `8e1e323`, version 0.8.0). That commit is on PR #25's branch, not on
main (the PR was squash-merged), so fetch it before using the steps below
that cite it: `git fetch origin pull/25/head`.

## Revive Claude Code

1. `git mv parked/claude-code/.claude-plugin .claude-plugin`
2. Claude Code names an agent after its file, so give it the reviewers as
   `agents/<name>.md` — copies of `com.github.copilot/agents/<name>.agent.md`:
   `mkdir -p agents && for f in com.github.copilot/agents/*.agent.md; do cp "$f" "agents/$(basename "$f" .agent.md).md"; done`
   and add a test that keeps the two copies identical (see
   `tests/test_plugin_manifests.py` at commit `8e1e323`).
3. Set the same `version` in `.claude-plugin/plugin.json` as in `plugin.json`
   and run `claude plugin validate .`.
4. Install: `claude plugin marketplace add Loneranger001/software_engineer_stack`
   then `claude plugin install software-engineer-stack@se-stack`. Claude Code
   puts the plugin's `bin/` on PATH, so `ses` works by name.

Copilot's marketplace lookup prefers `.github/plugin/marketplace.json` over
`.claude-plugin/marketplace.json`, so reviving Claude Code doesn't change
what Copilot installs.

## Revive Codex

1. `git mv parked/codex/.codex-plugin .codex-plugin` and
   `mkdir -p .agents && git mv parked/codex/.agents/plugins .agents/plugins`
2. Set the same `version` in `.codex-plugin/plugin.json` as in `plugin.json`.
3. Install: `codex plugin marketplace add Loneranger001/software_engineer_stack`
   then `codex plugin add software-engineer-stack@se-stack`.
4. Codex plugins can't ship custom agents (openai/codex #18988, #28491), so
   skills run each reviewer as a generic subagent (`core/reviewers.md` option 2).
   For named, read-only reviewer agents, restore `ses setup codex` from
   `bin/ses` at commit `8e1e323`, which writes `~/.codex/agents/<name>.toml`.

Codex shows the model each skill's file path, so skills find `bin/ses` from
their own folder as they do under Copilot.

## After reviving either

Update `tests/test_plugin_manifests.py` (it asserts these folders are not at
the root), the README's Installation section, and bump the version in every
active manifest.
