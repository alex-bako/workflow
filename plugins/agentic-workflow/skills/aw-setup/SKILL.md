---
name: aw-setup
description: Set up this installed plugin's focused Codex agents or Claude compaction setting without cloning the source repository.
---

# Optional native profile setup

The planning, delivery and review skills work without setup or Python. Run this
only when the user wants the bundled native profiles or compaction setting. Native
agents can instead receive the role instructions directly from the coordinator.

Use the existing [setup helper](../../scripts/setup_agents.py) from this installed
skill's actual plugin directory. Resolve that relative path; never assume a cache
version or require a repository clone. Do not start workers or a development graph
for setup. Keep communication concise; use the existing helper without wrappers.

1. Default to the current coding client. Configure both only when requested.
2. For Codex, run the helper with `--codex-home` set to the effective `CODEX_HOME`,
   otherwise `~/.codex`. For Claude, use `--claude-settings` with `settings.json`
   in the effective `CLAUDE_CONFIG_DIR`, otherwise `~/.claude`.
   Expand home paths and quote all paths. Python 3.10+ is required.
3. Read the helper result. On a conflict, report the exact conflicting file and
   stop that setup; do not overwrite customized profiles, settings or backups.
4. Confirm the requested profiles/settings exist, then tell the user to restart
   the configured client. Claude's 200k compaction window also affects the main
   session; it is not a weekly token limit or an isolated subagent context cap.

Mem0 remains the only shared-memory provider. This helper does not install or
configure Mem0 credentials. Report missing Mem0 configuration without accessing
another memory provider. Do not install unrelated plugins. Caveman/Ponytail worker
instructions are already embedded in the bundled agent profiles.
