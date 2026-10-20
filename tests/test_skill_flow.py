"""Lint the lifecycle wiring: every stage new-task.sh creates is set by a skill of
that pipeline, every gate a skill requires exists in its pipeline, every
framework path and `ses` command a skill or agent references exists, and no
instruction file depends on one harness's path variables."""
import re
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INSTRUCTION_DIRS = ("skills", "com.github.copilot", "core", "checklists", "templates", "standards")


def instruction_files():
    return [f for d in INSTRUCTION_DIRS for f in sorted((ROOT / d).rglob("*.md"))]


def ses_commands():
    loader = SourceFileLoader("ses_cli", str(ROOT / "bin" / "ses"))
    mod = module_from_spec(spec_from_loader("ses_cli", loader))
    loader.exec_module(mod)
    return set(mod.COMMANDS) | {"root", "help"}

# which skills drive which pipeline (a skill may serve several)
PIPELINE_SKILLS = {
    "full": ["intake", "research", "func-design", "tech-design", "grill", "impl-plan", "implement",
             "deliver", "retro"],
    "change-request": ["change-request", "grill", "func-design", "retro"],
    "document": ["document", "deliver"],
    "understand": ["understand"],
    "func-design": ["func-design"],
}


def pipeline_stages():
    text = (ROOT / "scripts" / "new-task.sh").read_text()
    out = {}
    for name, body in re.findall(r"^  ([a-z-]+)\)\n.*?STAGES=\"(.*?)\" ;;", text, re.S | re.M):
        out[name] = [l.split(":")[0] for l in body.splitlines() if l.strip()]
    return out


def skill_text(name):
    d = ROOT / "skills" / name
    return "\n".join(p.read_text() for p in sorted(d.glob("*.md")))


class FlowTest(unittest.TestCase):
    def test_pipelines_parsed(self):
        self.assertEqual(set(pipeline_stages()), set(PIPELINE_SKILLS))

    def test_every_stage_is_recorded_by_a_skill(self):
        for pipeline, stages in pipeline_stages().items():
            text = "\n".join(skill_text(s) for s in PIPELINE_SKILLS[pipeline])
            recorded = set(re.findall(r"ses status set <ws> ([a-z-]+)=", text))
            missing = [s for s in stages if s not in recorded]
            self.assertEqual(missing, [], f"{pipeline}: stages never set by its skills")

    def test_every_required_gate_exists_in_a_pipeline_the_skill_serves(self):
        stages = pipeline_stages()
        for skill in {s for v in PIPELINE_SKILLS.values() for s in v}:
            served = {st for p, sk in PIPELINE_SKILLS.items() if skill in sk for st in stages[p]}
            for args in re.findall(r"ses status require <ws> ([a-z0-9=, -]+)", skill_text(skill)):
                for pair in args.split():
                    stage = pair.split("=")[0]
                    self.assertIn(stage, served, f"/{skill} requires unknown stage '{stage}'")

    def test_referenced_framework_paths_exist(self):
        missing = set()
        for f in instruction_files():
            for ref in re.findall(r"<root>/([A-Za-z0-9_./-]+)", f.read_text()):
                ref = ref.rstrip(".,;:)")
                if ref and not (ROOT / ref).exists():
                    missing.add(f"{f.relative_to(ROOT)} → {ref}")
        self.assertEqual(sorted(missing), [])

    def test_referenced_ses_commands_exist(self):
        known, unknown = ses_commands(), set()
        for f in instruction_files():
            for cmd in re.findall(r"`ses ([a-z][a-z0-9-]*)", f.read_text()):
                if cmd not in known:
                    unknown.add(f"{f.relative_to(ROOT)} → ses {cmd}")
        self.assertEqual(sorted(unknown), [])

    def test_no_harness_specific_paths_or_script_paths(self):
        bad = []
        for f in instruction_files():
            for n, line in enumerate(f.read_text().splitlines(), 1):
                # check_knowledge.py is maintenance, run inside the framework checkout itself
                if "CLAUDE_PLUGIN_ROOT" in line or re.search(r"scripts/(?!check_knowledge)[a-z_-]+\.(py|sh)\b", line):
                    bad.append(f"{f.relative_to(ROOT)}:{n}: {line.strip()}")
        self.assertEqual(bad, [], "use `ses <command>` and <root>/… — they resolve in every harness")

    def test_files_using_root_or_ses_explain_them(self):
        for f in list((ROOT / "skills").glob("*/SKILL.md")) + list((ROOT / "com.github.copilot" / "agents").glob("*.agent.md")):
            text = f.read_text()
            if "<root>/" in text or "`ses " in text:
                self.assertIn("ses root", text, f"{f.relative_to(ROOT)} uses <root>/ses without the note")

    def test_agents_md_lists_every_skill(self):
        agents_md = (ROOT / "AGENTS.md").read_text()
        for d in sorted((ROOT / "skills").iterdir()):
            if (d / "SKILL.md").is_file():
                self.assertIn(f"`skills/{d.name}/SKILL.md`", agents_md)

    def test_no_bare_task_paths_or_hand_edited_status(self):
        bad = []
        for f in (ROOT / "skills").rglob("*.md"):
            for n, line in enumerate(f.read_text().splitlines(), 1):
                if "`work/<id>/" in line or re.search(r"(Update|record it in) STATUS\.md|STATUS\.md →", line):
                    bad.append(f"{f.relative_to(ROOT)}:{n}: {line.strip()}")
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
