# Agentic Workflow

The distributable plugin is `plugins/agentic-workflow`. Codex and Claude load the
same skills; keep vendor-specific configuration in their manifests only.

Keep the helper Python-stdlib-only. It routes work and validates recorded evidence;
the host coding agent performs the work. Do not add background agents, network
calls, global hooks, or a graph database without a demonstrated requirement.

After changes run `python3 -m unittest discover -s tests -v` and validate both
plugin manifests. Tests must cover behavior, especially stale evidence, recovery,
review completion, and graph boundaries. Keep user-facing usage in README.md.
