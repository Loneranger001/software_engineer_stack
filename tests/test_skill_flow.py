"""Lint the lifecycle wiring: every stage new-task.sh creates is set by a skill of
that pipeline, every gate a skill requires exists in its pipeline, and every
framework path a skill or agent references exists."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

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
            recorded = set(re.findall(r"status\.py set <ws> ([a-z-]+)=", text))
            missing = [s for s in stages if s not in recorded]
            self.assertEqual(missing, [], f"{pipeline}: stages never set by its skills")

    def test_every_required_gate_exists_in_a_pipeline_the_skill_serves(self):
        stages = pipeline_stages()
        for skill in {s for v in PIPELINE_SKILLS.values() for s in v}:
            served = {st for p, sk in PIPELINE_SKILLS.items() if skill in sk for st in stages[p]}
            for args in re.findall(r"status\.py require <ws> ([a-z0-9=, -]+)", skill_text(skill)):
                for pair in args.split():
                    stage = pair.split("=")[0]
                    self.assertIn(stage, served, f"/{skill} requires unknown stage '{stage}'")

    def test_referenced_framework_paths_exist(self):
        missing = set()
        for f in list((ROOT / "skills").rglob("*.md")) + list((ROOT / "agents").glob("*.md")) \
                + list((ROOT / "core").glob("*.md")) + list((ROOT / "checklists").glob("*.md")):
            for ref in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([A-Za-z0-9_./-]+)", f.read_text()):
                ref = ref.rstrip(".,;:)")
                if ref and ref != ".generated" and not (ROOT / ref).exists():
                    missing.add(f"{f.relative_to(ROOT)} → {ref}")
        self.assertEqual(sorted(missing), [])

    def test_no_bare_task_paths_or_hand_edited_status(self):
        bad = []
        for f in (ROOT / "skills").rglob("*.md"):
            for n, line in enumerate(f.read_text().splitlines(), 1):
                if "`work/<id>/" in line or re.search(r"(Update|record it in) STATUS\.md|STATUS\.md →", line):
                    bad.append(f"{f.relative_to(ROOT)}:{n}: {line.strip()}")
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
