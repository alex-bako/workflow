import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_release", ROOT / "scripts/check_release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)
sync_profiles = release.sync_profiles


class ReleaseTests(unittest.TestCase):
    def test_release_identity_and_installed_entry_points(self):
        version = release.check()
        self.assertEqual(release.check(tag=f"v{version}"), version)
        with self.assertRaises(ValueError):
            release.check(tag="v999.0.0")
        self.assertEqual(release.check(after="0.0.0"), version)
        for previous in (version, "999.0.0", "invalid"):
            with self.subTest(previous=previous), self.assertRaises(ValueError):
                release.check(after=previous)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("plugins", ".agents", ".claude-plugin"):
                shutil.copytree(ROOT / name, root / name)
            manifest = root / release.PLUGIN / ".claude-plugin/plugin.json"
            original = manifest.read_text()
            value = json.loads(original)
            value['version'] = '999.0.0'
            manifest.write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                release.check(root)
            manifest.write_text(original)
            release.check(root)
            for name in ("skills/aw-next/SKILL.md", "codex-agents/aw-arbiter.toml", "agents/aw-planner.md",
                         "codex-agents/aw-planner.toml", "models.json"):
                with self.subTest(missing=name):
                    packaged = root / release.PLUGIN / name
                    packaged.unlink()
                    with self.assertRaisesRegex(ValueError, name):
                        release.check(root)
                    packaged.write_text("restored")
            market = root / '.agents/plugins/marketplace.json'
            value = json.loads(market.read_text())
            value['plugins'][0]['source']['path'] = '../../outside'
            market.write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                release.check(root)

    def test_profiles_match_models_json_and_drift_fails_release(self):
        self.assertEqual(sync_profiles.sync(write=False), [])
        result = subprocess.run([sys.executable, str(ROOT / "scripts/sync_profiles.py"), "--check"],
                                capture_output=True, text=True, check=False)
        self.assertEqual((result.returncode, result.stdout), (0, ""))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("plugins", ".agents", ".claude-plugin"):
                shutil.copytree(ROOT / name, root / name)
            plugin = root / release.PLUGIN
            planner = plugin / "codex-agents/aw-planner.toml"
            planner.write_text(planner.read_text().replace('model = "', 'model = "stale-', 1))
            self.assertEqual(sync_profiles.sync(plugin, write=False), [planner])
            with self.assertRaisesRegex(ValueError, "aw-planner.toml"):
                release.check(root)
            self.assertIn('model = "stale-', planner.read_text())  # --check never writes
            self.assertEqual(sync_profiles.sync(plugin), [planner])
            self.assertEqual(sync_profiles.sync(plugin, write=False), [])
            models = plugin / "models.json"
            value = json.loads(models.read_text())
            value["tiers"]["deep"]["claude"] = "other"
            models.write_text(json.dumps(value))
            drifted = {path.name for path in sync_profiles.sync(plugin, write=False)}
            self.assertEqual(drifted, {"aw-refuter.md", "aw-debugger.md", "aw-arbiter.md"})
