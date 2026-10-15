"""One repository, three plugin formats: keep the manifests and the Copilot agent copies in step."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = ROOT / ".claude-plugin" / "plugin.json"
COPILOT = ROOT / "plugin.json"                       # Agent Plugins 1.0 — read by GitHub Copilot
CODEX = ROOT / ".codex-plugin" / "plugin.json"
AGENT_PLUGINS_FIELDS = {"$schema", "name", "version", "description", "author", "homepage",
                        "repository", "license", "keywords", "extensions"}


def load(p):
    return json.loads(p.read_text())


class ManifestTest(unittest.TestCase):
    def test_manifests_agree(self):
        claude, copilot, codex = load(CLAUDE), load(COPILOT), load(CODEX)
        for key in ("name", "version", "description"):
            self.assertEqual(copilot[key], claude[key], f"plugin.json {key} differs from .claude-plugin")
            self.assertEqual(codex[key], claude[key], f".codex-plugin {key} differs from .claude-plugin")

    def test_copilot_manifest_is_agent_plugins_1_0(self):
        m = load(COPILOT)
        self.assertEqual(m["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")
        self.assertLessEqual(set(m), AGENT_PLUGINS_FIELDS)
        self.assertRegex(m["name"], r"^[a-z0-9](?:[a-z0-9.-]{0,62}[a-z0-9])?$")
        self.assertNotIn("--", m["name"])

    def test_codex_manifest_points_at_skills(self):
        self.assertEqual(load(CODEX)["skills"], "./skills/")

    def test_marketplaces_list_the_root_as_the_plugin(self):
        name = load(CLAUDE)["name"]
        claude_mkt = load(ROOT / ".claude-plugin" / "marketplace.json")   # Claude Code and Copilot
        self.assertIn({"name": name, "source": "./"},
                      [{"name": p["name"], "source": p["source"]} for p in claude_mkt["plugins"]])
        codex_mkt = load(ROOT / ".agents" / "plugins" / "marketplace.json")
        entry = next(p for p in codex_mkt["plugins"] if p["name"] == name)
        self.assertEqual(entry["source"], {"source": "local", "path": "./"})
        self.assertEqual(entry["policy"]["installation"], "AVAILABLE")

    def test_copilot_agents_are_exact_copies(self):
        # Copilot names agents NAME.agent.md and Claude Code names them after the file, so each
        # reviewer exists twice; agents/ is canonical. Fix drift with:
        #   for f in agents/*.md; do cp "$f" com.github.copilot/agents/$(basename "$f" .md).agent.md; done
        canonical = {p.stem: p.read_bytes() for p in (ROOT / "agents").glob("*.md")}
        copies = {p.name[:-len(".agent.md")]: p for p in (ROOT / "com.github.copilot" / "agents").glob("*.agent.md")}
        self.assertEqual(sorted(copies), sorted(canonical))
        for name, path in copies.items():
            self.assertFalse(path.is_symlink(), f"{path} must be a real file (symlinks may not load)")
            self.assertEqual(path.read_bytes(), canonical[name], f"{path} differs from agents/{name}.md")

    def test_agent_tools_use_names_copilot_maps(self):
        # Copilot maps Read→read, Grep/Glob→search, Bash→execute; anything else would be dropped
        for p in (ROOT / "agents").glob("*.md"):
            tools = re.search(r"^tools: (.*)$", p.read_text(), re.M).group(1)
            self.assertLessEqual({t.strip() for t in tools.split(",")}, {"Read", "Grep", "Glob", "Bash"}, p)


if __name__ == "__main__":
    unittest.main()
