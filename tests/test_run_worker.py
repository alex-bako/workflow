import contextlib
import importlib.util
import io
import json
from pathlib import Path
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
        self.assertIn("gpt-5.6-terra", command)
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
        self.assertIn("haiku", command)
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

    @patch("subprocess.run")
    def test_malformed_inventory_fails_closed(self, run):
        run.return_value = type("Result", (), {"returncode": 0, "stdout": "{}"})()
        with self.assertRaisesRegex(RuntimeError, "Codex MCP inventory"):
            run_worker.codex_mcp_servers(self.project)
        with self.assertRaisesRegex(RuntimeError, "Claude plugin inventory"):
            run_worker.claude_plugins(self.project)


if __name__ == "__main__":
    unittest.main()
