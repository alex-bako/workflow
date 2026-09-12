import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_release", ROOT / "scripts/check_release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


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
            market = root / '.agents/plugins/marketplace.json'
            value = json.loads(market.read_text())
            value['plugins'][0]['source']['path'] = '../../outside'
            market.write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                release.check(root)
