#!/usr/bin/env python3
"""Check this repository's release identity and marketplace entry points."""

import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
NAME = "agentic-workflow"
PLUGIN = f"plugins/{NAME}"
SEMVER = r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"


def check(root=ROOT, tag=None, after=None):
    manifests = [json.loads((root / PLUGIN / vendor / "plugin.json").read_text())
                 for vendor in (".codex-plugin", ".claude-plugin")]
    version = manifests[0].get("version", "")
    if not re.fullmatch(SEMVER, version):
        raise ValueError("Release version must be plain X.Y.Z SemVer")
    for manifest in manifests:
        if manifest.get("name") != NAME or manifest.get("version") != version:
            raise ValueError("Plugin manifests must have matching names and versions")
        if not manifest.get("description") or not manifest.get("author", {}).get("name"):
            raise ValueError("Plugin description and author are required")
    if tag is not None and tag != f"v{version}":
        raise ValueError(f"Tag {tag!r} must match v{version}")
    if after is not None:
        if not re.fullmatch(SEMVER, after):
            raise ValueError("Previous release must be plain X.Y.Z SemVer")
        if tuple(map(int, version.split("."))) <= tuple(map(int, after.split("."))):
            raise ValueError(f"Release {version} must be newer than {after}")
    if manifests[0].get("skills") != "./skills/":
        raise ValueError("Codex skills must point to ./skills/")
    for path, source in (
        (".agents/plugins/marketplace.json", {"source": "local", "path": f"./{PLUGIN}"}),
        (".claude-plugin/marketplace.json", f"./{PLUGIN}"),
    ):
        market = json.loads((root / path).read_text())
        entries = market.get("plugins", [])
        if market.get("name") != NAME or len(entries) != 1:
            raise ValueError(f"Unexpected marketplace identity or entries: {path}")
        entry = entries[0]
        if entry.get("name") != NAME or entry.get("source") != source or "version" in entry:
            raise ValueError(f"Marketplace must reference the bundled plugin without duplicating version: {path}")
    for file in ("skills/aw-setup/SKILL.md", "skills/aw-feature/SKILL.md",
                 "scripts/setup_agents.py", "graphs/development.json", "graphs/planning.json",
                 "skills/aw-eval/SKILL.md", "references/evals.md",
                 "evals/website/design.md", "evals/website/candidate.html",
                 "evals/website/control.html"):
        if not (root / PLUGIN / file).is_file():
            raise ValueError(f"Missing packaged file: {file}")
    return version


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag")
    parser.add_argument("--after", help="Require a version newer than this released version")
    args = parser.parse_args()
    try:
        print(check(tag=args.tag, after=args.after))
    except (ValueError, OSError) as error:
        parser.exit(1, f"error: {error}\n")
