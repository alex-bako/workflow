#!/usr/bin/env python3
"""Launch bounded native workers without plugin/MCP/skill extras.

Codex role config cannot remove inherited MCP except by disabling each server
found at launch; project instructions may still load. Claude 2.1.268 has no
--system-prompt-file, so its supported ephemeral --agents profile is used.
Managed policy can still enforce configuration.
"""
import argparse
import json
import re
from pathlib import Path
import subprocess
import sys
import tempfile

ROLES = {  # role: (tier, effort, turns, tools); models.json maps tiers to models
    "aw-scout": ("light", "low", 8, "Read,Grep,Glob,Write"),
    "aw-researcher": ("standard", "medium", 12, "Read,Grep,Glob,WebFetch,WebSearch,Write"),
    "aw-builder": ("standard", "medium", 24, "Read,Grep,Glob,Bash,Edit,Write"),
    "aw-refuter": ("deep", "high", 16, "Read,Grep,Glob,Bash,Write"),
    "aw-debugger": ("deep", "high", 16, "Read,Grep,Glob,Bash,Write"),
    "aw-product-owner": ("standard", "medium", 12, "Read,Grep,Glob,Bash,Write"),
    "aw-qa": ("standard", "medium", 20, "Read,Grep,Glob,Bash,Write"),
    "aw-router": ("standard", "medium", 10, "Read,Grep,Glob,Bash,Write"),
    "aw-arbiter": ("deep", "high", 8, "Read,Grep,Glob,Write"),
    "aw-planner": ("planner", "high", 20, "Read,Grep,Glob,Bash,Write"),
}
AGENTS = Path(__file__).resolve().parents[1] / "agents"
MODELS = Path(__file__).resolve().parents[1] / "models.json"
INVENTORY_TIMEOUT = 15


def codex_mcp_servers(project):
    result = subprocess.run(["codex", "--config", "features.plugins=false", "--config", "features.apps=false", "mcp", "list", "--json"], cwd=project, text=True, capture_output=True, timeout=INVENTORY_TIMEOUT, check=False)
    if result.returncode:
        raise RuntimeError("could not inventory Codex MCP servers")
    try:
        data = json.loads(result.stdout)
        if not isinstance(data, list) or any(not isinstance(item, dict) or not isinstance(item.get("name"), str) for item in data):
            raise ValueError
        names = [item["name"] for item in data]
        if any(not re.fullmatch(r"[A-Za-z0-9_-]+", name) for name in names):
            raise ValueError
        return names
    except (json.JSONDecodeError, TypeError, ValueError):
        raise RuntimeError("Codex MCP inventory was not valid JSON") from None


def claude_plugins(project):
    result = subprocess.run(["claude", "plugin", "list", "--json"], cwd=project, text=True, capture_output=True, timeout=INVENTORY_TIMEOUT, check=False)
    if result.returncode:
        raise RuntimeError("could not inventory Claude plugins")
    try:
        data = json.loads(result.stdout)
        if not isinstance(data, list) or any(not isinstance(item, dict) or not isinstance(item.get("id"), str) for item in data):
            raise ValueError
        return [item["id"] for item in data]
    except (json.JSONDecodeError, TypeError, ValueError):
        raise RuntimeError("Claude plugin inventory was not valid JSON") from None


def role_instructions(role):
    parts = (AGENTS / f"{role}.md").read_text().split("---", 2)
    if len(parts) != 3 or not parts[2].strip():
        raise RuntimeError(f"invalid bundled role profile: {role}")
    return parts[2].strip()


def prompt(instructions, brief):
    return instructions + "\n\nCoordinator context brief:\n" + brief


def model(role, client):
    tier = ROLES[role][0]
    try:
        return json.loads(MODELS.read_text())["tiers"][tier][client]
    except KeyError:
        raise RuntimeError(f"models.json has no {client} model for tier {tier!r} (role {role})") from None


def codex_command(role, project, servers):
    _, effort, _, _ = ROLES[role]
    command = ["codex", "exec", "--strict-config", "--cd", str(project), "--model", model(role, "codex"), "--config", f'model_reasoning_effort="{effort}"', "--config", "model_auto_compact_token_limit=200000", "--config", 'model_auto_compact_token_limit_scope="total"', "--config", "features.plugins=false", "--config", "features.apps=false", "--config", "features.memory_tool=false", "--config", "agents.enabled=false", "--config", "skills.include_instructions=false", "--json"]
    for server in servers:
        command.extend(["--config", f"mcp_servers.{server}.enabled=false"])
    return command


def claude_command(role, instructions, settings, mcp_config):
    _, effort, turns, tools = ROLES[role]
    name = model(role, "claude")
    agent = {role: {"description": "bounded worker", "prompt": instructions, "tools": tools.split(","), "disallowedTools": ["Agent", "Skill"], "model": name, "effort": effort, "maxTurns": turns}}
    return ["claude", "--print", "--model", name, "--effort", effort, "--autocompact", "200000", "--max-turns", str(turns), "--output-format", "json", "--agents", json.dumps(agent), "--agent", role, "--settings", str(settings), "--mcp-config", str(mcp_config), "--strict-mcp-config", "--disable-slash-commands", "--tools", tools]


def display_command(command):
    shown, redact = [], False
    for part in command:
        shown.append("<profile-redacted>" if redact else part)
        redact = part in {"--system-prompt", "--agents"}
    return shown


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Run one isolated native CLI worker.")
    parser.add_argument("--client", choices=("codex", "claude"), required=True)
    parser.add_argument("--role", choices=tuple(ROLES), required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--brief", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if not 1 <= args.timeout <= 300:
        parser.error("--timeout must be between 1 and 300 seconds")
    return args


def main(argv=None):
    args = parse_args(argv)
    project, brief_path, output = args.project.resolve(), args.brief.resolve(), args.output.resolve()
    if not project.is_dir():
        raise ValueError("--project must be a directory")
    if not brief_path.is_file():
        raise ValueError("--brief must be a file")
    brief = brief_path.read_text()
    if not brief.strip() or "memory status:" not in brief.lower():
        raise ValueError("--brief must be nonempty and include 'Memory status:' provenance")
    if output == brief_path or (not args.dry_run and output.exists()) or not output.parent.is_dir():
        raise ValueError("--output must differ from --brief and have an existing parent")
    instructions = role_instructions(args.role)
    temporary = []
    try:
        if args.client == "codex":
            command = codex_command(args.role, project, codex_mcp_servers(project))
        else:
            settings = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
            json.dump({"enabledPlugins": {name: False for name in claude_plugins(project)}, "autoMemoryEnabled": False, "env": {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "200000"}}, settings)
            settings.close()
            temporary.append(Path(settings.name))
            mcp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
            json.dump({"mcpServers": {}}, mcp)
            mcp.close()
            temporary.append(Path(mcp.name))
            command = claude_command(args.role, instructions, settings.name, mcp.name)
        if args.dry_run:
            print(json.dumps({"command": display_command(command), "timeout_seconds": args.timeout}))
            return 0
        with output.open("x") as stream:
            worker_input = brief if args.client == "claude" else prompt(instructions, brief)
            return subprocess.run(command, cwd=project, input=worker_input, text=True, stdout=stream, timeout=args.timeout, check=False).returncode
    except subprocess.TimeoutExpired:
        print(f"worker timed out after {args.timeout} seconds", file=sys.stderr)
        return 124
    finally:
        for path in temporary:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(1)
