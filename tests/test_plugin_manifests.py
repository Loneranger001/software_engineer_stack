"""The GitHub Copilot plugin: manifest, marketplace, and reviewer agents. Claude Code and Codex
packaging is parked (parked/README.md) — kept valid, but not active at the repository root."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "plugin.json"                                   # Agent Plugins 1.0
MARKETPLACE = ROOT / ".github" / "plugin" / "marketplace.json"
AGENTS = ROOT / "com.github.copilot" / "agents"
AGENT_PLUGINS_FIELDS = {"$schema", "name", "version", "description", "author", "homepage",
                        "repository", "license", "keywords", "extensions"}
REVIEWERS = {"code-reviewer", "doc-fact-checker", "scope-auditor"}
# agents that write: name → tools (Copilot maps Edit/Write→edit)
WRITERS = {"design-griller": {"Read", "Grep", "Glob", "Bash", "Edit", "Write"}}


def load(p):
    return json.loads(p.read_text())


class CopilotPluginTest(unittest.TestCase):
    def test_manifest_is_agent_plugins_1_0(self):
        m = load(MANIFEST)
        self.assertEqual(m["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")
        self.assertLessEqual(set(m), AGENT_PLUGINS_FIELDS)
        self.assertRegex(m["name"], r"^[a-z0-9](?:[a-z0-9.-]{0,62}[a-z0-9])?$")
        self.assertNotIn("--", m["name"])
        self.assertLessEqual(len(m["description"]), 1024)
        self.assertRegex(m["version"], r"^\d+\.\d+\.\d+$")

    def test_marketplace_lists_the_repository_root(self):
        mkt = load(MARKETPLACE)
        self.assertEqual({"name", "owner", "plugins"} - set(mkt), set())
        entry = next(p for p in mkt["plugins"] if p["name"] == load(MANIFEST)["name"])
        self.assertEqual(entry["source"], "./")

    def test_agents_are_copilot_agents(self):
        files = {p.name[:-len(".agent.md")]: p for p in AGENTS.glob("*.agent.md")}
        self.assertEqual(set(files), REVIEWERS | set(WRITERS))
        for name, path in files.items():
            self.assertFalse(path.is_symlink(), f"{path} must be a real file")
            text = path.read_text()
            self.assertRegex(text, rf"\A---\nname: {name}\ndescription: .+\n")
            # Copilot maps Read→read, Grep/Glob→search, Bash→execute: reviewers are read-only
            tools = {t.strip() for t in re.search(r"^tools: (.*)$", text, re.M).group(1).split(",")}
            self.assertEqual(tools, WRITERS.get(name, {"Read", "Grep", "Glob", "Bash"}), path)

    def test_every_agent_has_delegation_rules(self):
        rules = (ROOT / "core" / "reviewers.md").read_text()
        for path in AGENTS.glob("*.agent.md"):
            self.assertIn(f"`{path.name[:-len('.agent.md')]}`", rules,
                          f"core/reviewers.md must say how {path.name} is delegated")

    def test_parked_packaging_stays_valid_and_inactive(self):
        for p in (ROOT / "parked").rglob("*.json"):
            load(p)
        for active in (".claude-plugin", ".codex-plugin", ".agents"):
            self.assertFalse((ROOT / active).exists(),
                             f"{active}/ is parked — revive it per parked/README.md, then update this test")


if __name__ == "__main__":
    unittest.main()
