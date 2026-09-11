import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/agentic-workflow/scripts/setup_agents.py"
SPEC = importlib.util.spec_from_file_location("setup_agents", SCRIPT)
setup_agents = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup_agents)


class SetupAgentsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.bundled = self.root / "bundled"
        self.bundled.mkdir()
        (self.bundled / "worker.toml").write_text('name = "worker"\n')
        self.original = setup_agents.BUNDLED_AGENTS
        setup_agents.BUNDLED_AGENTS = self.bundled

    def tearDown(self):
        setup_agents.BUNDLED_AGENTS = self.original
        self.temp.cleanup()

    def invoke(self, *args):
        return setup_agents.main(list(args))

    def test_idempotently_copies_profiles_and_merges_settings(self):
        home = self.root / "codex"
        settings = self.root / "settings.json"
        settings.write_text(json.dumps({"permissions": {"allow": ["Read"]}, "env": {"KEEP": "yes"}}))
        self.invoke("--codex-home", str(home), "--claude-settings", str(settings))
        self.assertEqual((home / "agents/worker.toml").read_text(), 'name = "worker"\n')
        saved = json.loads(settings.read_text())
        self.assertEqual(saved["permissions"], {"allow": ["Read"]})
        self.assertEqual(saved["env"], {"KEEP": "yes", "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "200000"})
        self.assertEqual((settings.with_name("settings.json.bak")).read_text(), json.dumps({"permissions": {"allow": ["Read"]}, "env": {"KEEP": "yes"}}))
        self.invoke("--codex-home", str(home), "--claude-settings", str(settings))

    def test_profile_collision_leaves_settings_unchanged(self):
        home = self.root / "codex"
        target = home / "agents"
        target.mkdir(parents=True)
        (target / "worker.toml").write_text("custom\n")
        settings = self.root / "settings.json"
        original = '{"keep":true}'
        settings.write_text(original)
        with self.assertRaisesRegex(ValueError, "customized"):
            self.invoke("--codex-home", str(home), "--claude-settings", str(settings))
        self.assertEqual(settings.read_text(), original)
        self.assertFalse(settings.with_name("settings.json.bak").exists())

    def test_rejects_bad_settings_and_symlink(self):
        for content in ("[]", "{bad", '{"env": []}', '{"env":{"DISABLE_AUTO_COMPACT":"1"}}', '{"env":{"DISABLE_COMPACT":"1"}}', '{"autoCompactEnabled":false}', '{"env":{"CLAUDE_AUTOCOMPACT_PCT_OVERRIDE":"50"}}'):
            path = self.root / (str(abs(hash(content))) + ".json")
            path.write_text(content)
            with self.assertRaises(ValueError):
                self.invoke("--claude-settings", str(path))
        real = self.root / "real.json"
        real.write_text("{}")
        link = self.root / "link.json"
        link.symlink_to(real)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.invoke("--claude-settings", str(link))

    def test_requires_an_argument(self):
        with self.assertRaises(SystemExit) as error:
            self.invoke()
        self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
