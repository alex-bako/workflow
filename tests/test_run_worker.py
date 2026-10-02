import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("run_worker", ROOT / "plugins/agentic-workflow/scripts/run_worker.py")
run_worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(run_worker)


class WorkerLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        self.brief = self.project / "brief.txt"
        self.brief.write_text("Goal: inspect one file\nMemory status: coordinator supplied no recall\n")
        self.output = self.project / "worker.out"

    def invoke(self, *args):
        return run_worker.main([*args, "--project", str(self.project), "--brief", str(self.brief), "--output", str(self.output)])

    def dry(self, *args):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(self.invoke(*args, "--dry-run"), 0)
        return json.loads(stdout.getvalue())["command"]

    @patch.object(run_worker, "codex_mcp_servers", return_value=["mem0", "context7"])
    def test_codex_disables_inventory_plugins_skills_and_uses_explicit_role_model(self, inventory):
        command = self.dry("--client", "codex", "--role", "aw-builder")
        models = json.loads((ROOT / "plugins/agentic-workflow/models.json").read_text())["tiers"]
        self.assertEqual(command[command.index("--model") + 1], models["standard"]["codex"])
        self.assertIn("features.plugins=false", command)
        self.assertIn("features.apps=false", command)
        self.assertIn("features.memory_tool=false", command)
        self.assertIn("agents.enabled=false", command)
        self.assertIn("skills.include_instructions=false", command)
        self.assertIn('mcp_servers.mem0.enabled=false', command)
        self.assertIn('mcp_servers.context7.enabled=false', command)
        self.assertNotIn("--ignore-user-config", command)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", command)
        inventory.assert_called_once_with(self.project.resolve())

    @patch.object(run_worker, "claude_plugins", return_value=["mem0@market", "ponytail@market"])
    def test_claude_uses_strict_empty_mcp_explicit_tools_and_redacted_profile(self, plugins):
        command = self.dry("--client", "claude", "--role", "aw-scout")
        models = json.loads((ROOT / "plugins/agentic-workflow/models.json").read_text())["tiers"]
        self.assertEqual(command[command.index("--model") + 1], models["light"]["claude"])
        self.assertIn("--strict-mcp-config", command)
        self.assertIn("--disable-slash-commands", command)
        self.assertIn("--agents", command)
        self.assertIn("--agent", command)
        self.assertIn("--max-turns", command)
        self.assertIn("json", command)
        self.assertIn("Read,Grep,Glob,Write", command)
        self.assertIn("<profile-redacted>", command)
        self.assertNotIn("--dangerously-skip-permissions", command)
        plugins.assert_called_once_with(self.project.resolve())

    @patch.object(run_worker, "codex_mcp_servers", return_value=[])
    @patch("subprocess.run")
    def test_execution_writes_raw_output_and_passes_embedded_profile_and_brief(self, run, _):
        def fake(command, **kwargs):
            kwargs["stdout"].write("raw worker output\n")
            return type("Result", (), {"returncode": 0})()
        run.side_effect = fake
        self.assertEqual(self.invoke("--client", "codex", "--role", "aw-scout"), 0)
        self.assertEqual(self.output.read_text(), "raw worker output\n")
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", run.call_args_list[-1].args[0])
        self.assertIn("Caveman", run.call_args_list[-1].kwargs["input"])
        self.assertIn("Memory status:", run.call_args_list[-1].kwargs["input"])

    def test_rejects_missing_memory_provenance_and_bad_timeout(self):
        self.brief.write_text("Goal: no provenance\n")
        with self.assertRaisesRegex(ValueError, "Memory status"):
            self.invoke("--client", "codex", "--role", "aw-scout")
        with self.assertRaises(SystemExit):
            self.invoke("--client", "codex", "--role", "aw-scout", "--timeout", "301")

    def test_refuses_to_overwrite_an_existing_output(self):
        self.output.write_text("source artifact\n")
        with self.assertRaisesRegex(ValueError, "--output"):
            self.invoke("--client", "codex", "--role", "aw-scout")
        self.assertEqual(self.output.read_text(), "source artifact\n")

    @patch("subprocess.run")
    def test_codex_inventory_excludes_plugin_servers_and_rejects_ambiguous_names(self, run):
        run.return_value = type("Result", (), {"returncode": 0, "stdout": '[{"name":"mem0-mcp"}]'})()
        self.assertEqual(run_worker.codex_mcp_servers(self.project), ["mem0-mcp"])
        self.assertIn("features.plugins=false", run.call_args.args[0])
        self.assertIn("features.apps=false", run.call_args.args[0])
        run.return_value.stdout = '[{"name":"ambiguous.name"}]'
        with self.assertRaisesRegex(RuntimeError, "Codex MCP inventory"):
            run_worker.codex_mcp_servers(self.project)

    def test_bundled_profiles_match_roles_and_share_paragraphs(self):
        plugin = ROOT / "plugins/agentic-workflow"
        shared = set()
        for role, (_, effort, turns, tools) in run_worker.ROLES.items():
            claude_model, codex_model = run_worker.model(role, "claude"), run_worker.model(role, "codex")
            with self.subTest(role=role):
                _, front, body = (plugin / f"agents/{role}.md").read_text().split("---", 2)
                meta = {k: v.strip('"') for k, v in (line.split(": ", 1) for line in front.strip().splitlines())}
                self.assertEqual((meta["name"], meta["model"], meta["effort"], meta["maxTurns"]), (role, claude_model, effort, str(turns)))
                if "tools" in meta:  # aw-qa leaves tools open for browser QA
                    self.assertEqual(meta["tools"].replace(" ", ""), tools)
                toml = (plugin / f"codex-agents/{role}.toml").read_text()
                field = lambda key: re.search(rf'^{key} = "([^"]*)"$', toml, re.M).group(1)
                self.assertEqual((field("name"), field("model"), field("model_reasoning_effort")), (role, codex_model, effort))
                self.assertEqual(field("description"), meta["description"])
                instructions = re.search(r'^developer_instructions = """\n(.*?)\n"""$', toml, re.M | re.S).group(1)
                self.assertEqual(instructions, body.strip())
                block, *rest = instructions.split("\n\n")
                self.assertTrue(block.endswith(f"Turn budget: {turns}."))
                self.assertEqual(len(rest), 2)
                shared.add(tuple(rest))
        self.assertEqual(len(shared), 1)

    def test_arbiter_judges_at_refuter_tier_without_shell_or_edit(self):
        arbiter, refuter = run_worker.ROLES["aw-arbiter"], run_worker.ROLES["aw-refuter"]
        self.assertEqual(arbiter[:2], refuter[:2])
        self.assertLess(arbiter[2], refuter[2])
        self.assertEqual(arbiter[3], "Read,Grep,Glob,Write")
        body = (ROOT / "plugins/agentic-workflow/agents/aw-arbiter.md").read_text()
        for rule in ("Reclassify", "Repeats", "Out of scope", "`stop`", "`repair`", "`replan`", "`ask`", "n >= 3", "after_round", "found_work"):
            self.assertIn(rule, body)

    def test_gate_and_found_work_rules_reach_every_entry_point(self):
        plugin = ROOT / "plugins/agentic-workflow"
        flat = lambda rel: " ".join((plugin / rel).read_text().split())  # noqa: E731
        # Every passage that rules out an attempt cap still defers review rounds to the gate.
        for path in sorted((plugin / "references").glob("*.md")) + sorted((plugin / "skills").glob("*/SKILL.md")):
            for para in path.read_text().split("\n\n"):
                if re.search(r"attempt[- ]cap", para):
                    with self.subTest(path=path.name):
                        self.assertIn("review gate", " ".join(para.split()))
        for rel in ("references/delivery.md", "skills/aw-review/SKILL.md"):  # remote rounds pass the gate too
            self.assertIn("stage `remote`", flat(rel))
            self.assertNotRegex(flat(rel), r"(?i)\b(fix|repair) valid findings")
        steward = flat("agents/aw-product-owner.md")
        for rule in ("Title: the failing test, check or symptom verbatim", "no `found` key", "unfiled found work",
                     "resumed after it"):
            self.assertIn(rule, steward)
        nxt = flat("skills/aw-next/SKILL.md")
        for rule in ("A `blocked` one resumes only when the found issue or question its Progress names is resolved",
                     "unfiled found work", "name the issue in Progress"):
            self.assertIn(rule, nxt)

    def test_unknown_tier_or_client_fails_clearly(self):
        with patch.dict(run_worker.ROLES, {"aw-scout": ("galactic", "low", 8, "Read")}):
            with self.assertRaisesRegex(RuntimeError, "no claude model for tier 'galactic'"):
                run_worker.model("aw-scout", "claude")
        with self.assertRaisesRegex(RuntimeError, "no gemini model for tier 'light'"):
            run_worker.model("aw-scout", "gemini")

    def test_planner_tier_is_used_by_aw_planner_only(self):
        tiers = {role: spec[0] for role, spec in run_worker.ROLES.items()}
        self.assertEqual([role for role, tier in tiers.items() if tier == "planner"], ["aw-planner"])
        self.assertEqual(run_worker.ROLES["aw-planner"], ("planner", "high", 20, "Read,Grep,Glob,Bash,Write"))
        models = json.loads((ROOT / "plugins/agentic-workflow/models.json").read_text())
        self.assertEqual(set(tiers.values()) | {models["coordinator"]}, set(models["tiers"]))
        self.assertEqual(models["coordinator"], "deep")

    def test_model_names_live_only_in_models_json_and_stamped_lines(self):
        plugin = ROOT / "plugins/agentic-workflow"
        tiers = json.loads((plugin / "models.json").read_text())["tiers"].values()
        names = {name for tier in tiers for name in tier.values()}
        names |= {name.rsplit("-", 1)[-1] for tier in tiers for name in (tier["codex"],)}
        pattern = re.compile(r"(?i)(?<![\w.-])(gpt-\d[\w.-]*|" + "|".join(map(re.escape, names)) + r")(?![\w-])")
        files = [*plugin.glob("agents/*.md"), *plugin.glob("codex-agents/*.toml"),
                 *plugin.glob("references/**/*.md"), *plugin.glob("skills/**/*.md")]
        self.assertGreater(len(files), 20)
        for path in files:
            text = re.sub(r'^model(: .*| = ".*")$', "", path.read_text(), count=1, flags=re.M)
            with self.subTest(path=path.relative_to(plugin).as_posix()):
                self.assertIsNone(pattern.search(text))

    @patch("subprocess.run")
    def test_malformed_inventory_fails_closed(self, run):
        run.return_value = type("Result", (), {"returncode": 0, "stdout": "{}"})()
        with self.assertRaisesRegex(RuntimeError, "Codex MCP inventory"):
            run_worker.codex_mcp_servers(self.project)
        with self.assertRaisesRegex(RuntimeError, "Claude plugin inventory"):
            run_worker.claude_plugins(self.project)


if __name__ == "__main__":
    unittest.main()
