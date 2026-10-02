#!/usr/bin/env python3
"""Check this repository's release identity and marketplace entry points."""

import argparse
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("sync_profiles", Path(__file__).with_name("sync_profiles.py"))
sync_profiles = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync_profiles)
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
                 "evals/website/control.html", "skills/aw-next/SKILL.md",
                 "references/tracker.md", "references/loop.md", "scripts/tracker.py",
                 "agents/aw-product-owner.md", "agents/aw-qa.md", "agents/aw-router.md",
                 "agents/aw-arbiter.md", "codex-agents/aw-product-owner.toml",
                 "codex-agents/aw-qa.toml", "codex-agents/aw-router.toml",
                 "codex-agents/aw-arbiter.toml", "models.json", "agents/aw-planner.md",
                 "codex-agents/aw-planner.toml", "evals/tracker/gh", "evals/tracker/state.json",
                 "evals/tracker/steward/state.json", "evals/tracker/steward/ROADMAP.md",
                 "evals/scope/plan.md", "evals/scope/state.json",
                 "evals/router/plan.md", "evals/router/change-a.patch",
                 "evals/harbor/README.md", "evals/harbor/prepare.py",
                 "evals/gate/project/docs/plans/T1.md", "evals/harbor/lib/gate_rules.py",
                 *(f"evals/gate/{v}/docs/plans/T1.review.json" for v in "abcd"),
                 *(f"evals/harbor/tasks/gate-{v}/task.toml" for v in "abcd"),
                 *(f"evals/tracker/intake/{f}" for f in (
                     "report.md", "report-vague.md", "storage-runs.log", "found-9.json")),
                 *(f"evals/harbor/tasks/steward-intake-{v}/task.toml" for v in "abc"),
                 *(f"evals/harbor/tasks/{task}/task.toml" for task in (
                     "qa-a", "qa-b", "router-a", "router-b", "steward-pick",
                     "steward-conflict", "steward-refused-write", "loop-one-pass"))):
        if not (root / PLUGIN / file).is_file():
            raise ValueError(f"Missing packaged file: {file}")
    drifted = sync_profiles.sync(root / PLUGIN, write=False)
    if drifted:
        raise ValueError("Profiles drift from models.json (run python3 scripts/sync_profiles.py): "
                         + ", ".join(path.name for path in drifted))
    return version


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag")
    parser.add_argument("--after", help="Require a version newer than this released version")
    args = parser.parse_args()
    try:
        print(check(tag=args.tag, after=args.after))
    except (ValueError, OSError, RuntimeError) as error:
        parser.exit(1, f"error: {error}\n")
