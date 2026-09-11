#!/usr/bin/env python3
"""Install bundled Codex profiles and configure Claude auto-compaction."""

import argparse
import json
import os
from pathlib import Path
import stat
import sys
import tempfile


BUNDLED_AGENTS = Path(__file__).resolve().parents[1] / "codex-agents"
AUTO_COMPACT_WINDOW = "200000"


def fail(message):
    raise ValueError(message)


def reject_symlink(path):
    if path.is_symlink():
        fail(f"Refusing symlink target: {path}")


def profiles_for(destination):
    profiles = sorted(BUNDLED_AGENTS.glob("*.toml"))
    if not profiles:
        fail(f"No bundled Codex profiles in {BUNDLED_AGENTS}")
    target_dir = destination / "agents"
    if target_dir.exists():
        reject_symlink(target_dir)
        if not target_dir.is_dir():
            fail(f"Codex agents path is not a directory: {target_dir}")
    for source in profiles:
        target = target_dir / source.name
        if target.exists() or target.is_symlink():
            reject_symlink(target)
            if not target.is_file() or target.read_bytes() != source.read_bytes():
                fail(f"Refusing to overwrite customized profile: {target}")
    return profiles, target_dir


def settings_for(path):
    reject_symlink(path)
    if not path.exists():
        return None, {"env": {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": AUTO_COMPACT_WINDOW}}
    if not path.is_file():
        fail(f"Claude settings path is not a file: {path}")
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Malformed Claude settings JSON: {path}") from error
    if not isinstance(value, dict):
        fail("Claude settings JSON must be an object")
    env = value.get("env", {})
    if not isinstance(env, dict):
        fail("Claude settings env must be an object")
    if value.get("autoCompactEnabled") is False or any(
        env.get(key) not in (None, "", False, 0, "0")
        for key in ("DISABLE_AUTO_COMPACT", "DISABLE_COMPACT")
    ):
        fail("Claude settings disable auto-compaction; resolve conflict first")
    if env.get("CLAUDE_AUTOCOMPACT_PCT_OVERRIDE") not in (None, ""):
        fail("Claude settings override auto-compaction percentage; resolve conflict first")
    updated = dict(value)
    updated["env"] = dict(env)
    updated["env"]["CLAUDE_CODE_AUTO_COMPACT_WINDOW"] = AUTO_COMPACT_WINDOW
    if updated == value:
        return None, None
    return path.read_bytes(), updated


def atomic_bytes(path, content, mode=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        if mode is not None:
            os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def install_profiles(profiles, target_dir):
    target_dir.mkdir(parents=True, exist_ok=True)
    for source in profiles:
        target = target_dir / source.name
        if not target.exists():
            atomic_bytes(target, source.read_bytes(), stat.S_IMODE(source.stat().st_mode))


def write_settings(path, original, updated):
    if updated is None:
        return
    if original is None:
        atomic_bytes(path, (json.dumps(updated, indent=2) + "\n").encode())
        return
    backup = path.with_name(path.name + ".bak")
    if backup.exists() or backup.is_symlink():
        fail(f"Refusing to overwrite settings backup: {backup}")
    mode = stat.S_IMODE(path.stat().st_mode)
    atomic_bytes(backup, original, mode)
    atomic_bytes(path, (json.dumps(updated, indent=2) + "\n").encode(), mode)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path)
    parser.add_argument("--claude-settings", type=Path)
    args = parser.parse_args(argv)
    if args.codex_home is None and args.claude_settings is None:
        parser.error("at least one of --codex-home or --claude-settings is required")

    # Preflight every requested output before changing either destination.
    profile_plan = profiles_for(args.codex_home) if args.codex_home else None
    settings_plan = settings_for(args.claude_settings) if args.claude_settings else None
    if settings_plan and settings_plan[0] is not None and settings_plan[1] is not None:
        backup = args.claude_settings.with_name(args.claude_settings.name + ".bak")
        if backup.exists() or backup.is_symlink():
            fail(f"Refusing to overwrite settings backup: {backup}")

    if profile_plan:
        install_profiles(*profile_plan)
    if settings_plan:
        write_settings(args.claude_settings, *settings_plan)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)
