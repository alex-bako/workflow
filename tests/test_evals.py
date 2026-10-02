import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/agentic-workflow"
HARBOR = PLUGIN / "evals/harbor"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def flat(rel):
    return " ".join((PLUGIN / rel).read_text().split())


class HarborTests(unittest.TestCase):
    def test_bundle_carries_models_json_for_run_worker(self):
        prepare = load("prepare", HARBOR / "prepare.py")
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "bundle"
            prepare.build_bundle(dest)
            self.assertEqual((dest / "models.json").read_bytes(), (PLUGIN / "models.json").read_bytes())

    def test_qa_node_check_returns_false_instead_of_raising(self):
        stub = types.ModuleType("rewardkit")
        stub.criterion = lambda **_: (lambda f: f)
        with mock.patch.dict(sys.modules, {"rewardkit": stub}):
            qa = load("qa_rules", HARBOR / "lib/qa_rules.py")
        for error in (OSError("no node"), subprocess.TimeoutExpired("node", 120)):
            with self.subTest(error=type(error).__name__), mock.patch("subprocess.run", side_effect=error):
                self.assertFalse(qa.project_checks_report_actual_node_test_result(Path("/nonexistent")))


class DocTests(unittest.TestCase):
    def test_aw_eval_names_every_harbor_case(self):
        cases = [json.loads(p.read_text()).get("case", "") for p in HARBOR.glob("tasks/*/tests/case.json")]
        last = max(int(c[1:]) for c in cases if re.fullmatch(r"E\d+", c))
        ranges = re.findall(r"E7–E\d+", (PLUGIN / "skills/aw-eval/SKILL.md").read_text())
        self.assertEqual(set(ranges), {f"E7–E{last}"})

    def test_last_bullet_pull_request_closes_the_card(self):
        for rel in ("references/loop.md", "skills/aw-next/SKILL.md"):
            with self.subTest(rel):
                self.assertIn("last open bullet", flat(rel))
        self.assertIn("kind (bullet, card or found)", flat("references/tracker.md"))

    def test_steward_reads_body_acceptance_and_forwards_in_flight(self):
        for rel in ("agents/aw-product-owner.md", "codex-agents/aw-product-owner.toml"):
            with self.subTest(rel):
                for rule in ("its `authority.text` is the issue body", "any item when the policy has no authority file",
                             "every `in_flight` entry (number, branch, phase)", "one `Repositories:` line"):
                    self.assertIn(rule, flat(rel))

    def test_claude_profile_frontmatter_quotes_values_with_a_colon(self):
        for path in sorted((PLUGIN / "agents").glob("*.md")):
            for line in path.read_text().split("---")[1].strip().splitlines():
                value = line.partition(": ")[2]
                with self.subTest(path=path.name, line=line):
                    self.assertTrue(": " not in value or value[:1] in "\"'", line)


if __name__ == "__main__":
    unittest.main()
