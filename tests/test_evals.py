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

    def test_builder_red_evidence_sits_apart_from_the_final_checks(self):
        stub = types.ModuleType("rewardkit")
        stub.criterion = lambda **_: (lambda f: f)
        with mock.patch.dict(sys.modules, {"rewardkit": stub}):
            build = load("build_rules", HARBOR / "lib/build_rules.py")
        red = {"command": "node --test", "exit": 1, "assertion": "tags missing"}
        green = {"command": "node --test", "exit": 0, "result": "pass 4"}
        report = {"status": "complete", "changed_files": ["src/items.mjs"], "red": [red], "checks": [green]}
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            for data, ok in ((report, True), ({**report, "red": []}, False),
                             ({**report, "red": [green]}, False), ({**report, "red": [], "checks": [red, green]}, False),
                             ({**report, "red": 1}, False), ({**report, "red": [{"command": "false", "exit": 1}]}, False)):
                (ws / "build-report.json").write_text(json.dumps(data))
                with self.subTest(data=data):
                    self.assertEqual(build.red_evidence_reported(ws), ok)
            (ws / "build-report.json").write_text(json.dumps(report))
            with mock.patch.object(build, "_node_test", return_value=0), \
                 mock.patch.object(build, "_changed", return_value={"src/items.mjs"}):
                self.assertTrue(build.report_matches_reality(ws))


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

    def test_every_planning_entry_point_grills_in_rounds(self):
        for rel in ("references/workflow.md", "references/planning.md", "skills/aw-feature/SKILL.md",
                    "skills/aw-discover/SKILL.md", "skills/aw-domain/SKILL.md", "skills/aw-roadmap/SKILL.md",
                    "skills/aw-plan/SKILL.md"):
            with self.subTest(rel):
                self.assertIn("grilling.md", flat(rel))
                self.assertNotRegex(flat(rel), r"(?i)one[- ](?:material |guided )?question[- ](?:at a time|per turn)|pending question")
        grilling = flat("references/grilling.md")
        for rule in ("frontier", "AskUserQuestion", "up to four", "❓ Q1", "Never answer a decision on the user's behalf",
                     "hard to reverse, surprising without its context and the result of a real tradeoff",
                     "The user then confirms", "A non-material choice is the coordinator's call"):
            self.assertIn(rule, grilling)

    def test_loop_asks_open_decisions_in_one_round_and_gates_cards_with_open_decisions(self):
        for rel in ("agents/aw-planner.md", "codex-agents/aw-planner.toml"):
            with self.subTest(rel):
                self.assertIn("return every open decision whose prerequisites are settled", flat(rel))
                self.assertIn("why that check fails at the base commit", flat(rel))
        for rel in ("references/loop.md", "skills/aw-next/SKILL.md"):
            with self.subTest(rel):
                self.assertRegex(flat(rel), r"one (?:numbered|\[grilling\]\(grilling\.md#asking-a-round\)) round")
                self.assertNotIn("Ask one question with a recommendation", flat(rel))
                self.assertIn("aw-plan ahead", flat(rel))
        self.assertIn("`aw-plan ahead [N]`", flat("skills/aw-plan/SKILL.md"))
        self.assertIn("`open_decisions`", flat("references/tracker.md"))

    def test_checks_must_fail_before_the_change_and_risky_plans_get_a_review(self):
        self.assertIn("why it fails at the base commit", flat("skills/aw-plan/SKILL.md"))
        for role, rule in (("aw-builder", "report it failing before the fix (command, failing assertion)"),
                           ("aw-qa", "missing red evidence is a finding"),
                           ("aw-refuter", "Brief target `plan`")):
            for rel in (f"agents/{role}.md", f"codex-agents/{role}.toml"):
                with self.subTest(rel):
                    self.assertIn(rule, flat(rel))
        loop = flat("references/loop.md")
        self.assertIn("the builder's red evidence (failing command and assertion per new check)", flat("skills/aw-next/SKILL.md"))
        for rule in ("New behavior has a test that fails without the change", "QA reruns it green itself",
                     "one `aw-refuter` with target `plan`",
                     "the vendor the planner did not use", "persisted data or migrations, auth or security",
                     "record the skip in Progress"):
            self.assertIn(rule, loop)

    def test_claude_profile_frontmatter_quotes_values_with_a_colon(self):
        for path in sorted((PLUGIN / "agents").glob("*.md")):
            for line in path.read_text().split("---")[1].strip().splitlines():
                value = line.partition(": ")[2]
                with self.subTest(path=path.name, line=line):
                    self.assertTrue(": " not in value or value[:1] in "\"'", line)


if __name__ == "__main__":
    unittest.main()
