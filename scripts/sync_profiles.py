#!/usr/bin/env python3
"""Stamp each native role profile's model line from run_worker ROLES and models.json."""

import argparse
import importlib.util
from pathlib import Path
import re
import sys

PLUGIN = Path(__file__).resolve().parents[1] / "plugins/agentic-workflow"


def sync(plugin=PLUGIN, write=True):
    """Return the profiles whose model line differs from the mapping; rewrite them if write."""
    spec = importlib.util.spec_from_file_location("run_worker", plugin / "scripts/run_worker.py")
    worker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker)
    changed = []
    for role in worker.ROLES:
        for path, pattern, line in (
                (plugin / f"agents/{role}.md", r"^model: .*$", f"model: {worker.model(role, 'claude')}"),
                (plugin / f"codex-agents/{role}.toml", r'^model = ".*"$', f'model = "{worker.model(role, "codex")}"')):
            text = path.read_text()
            new, count = re.subn(pattern, line, text, count=1, flags=re.M)
            if not count:
                raise ValueError(f"No model line in {path}")
            if new != text:
                changed.append(path)
                if write:
                    path.write_text(new)
    return changed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="List drifted profiles and fail; write nothing")
    args = parser.parse_args()
    try:
        changed = sync(write=not args.check)
    except (ValueError, OSError, RuntimeError) as error:
        parser.exit(1, f"error: {error}\n")
    for path in changed:
        print(path.relative_to(PLUGIN.parents[1]))
    sys.exit(1 if args.check and changed else 0)
