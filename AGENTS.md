# Agentic Workflow

The distributable plugin is `plugins/agentic-workflow`. Codex and Claude load the
same skills. Keep vendor configuration in manifests and native agent profiles;
shared delegation policy lives in references/subagents.md.

Use Mem0 exclusively for shared recall and session lessons. Do not use Obsidian
or other memory providers. Preserve canonical project docs and exact checkpoints.

Keep the helper Python-stdlib-only. It routes work and validates recorded evidence;
the host coding agent performs the work. Do not add background agents, network
calls, global hooks, or a graph database without a demonstrated requirement.
Recorded exception: plugin `scripts/tracker.py` reaches GitHub only via the user's `gh` CLI.
Harbor and RewardKit (`plugins/agentic-workflow/evals/harbor/`) are optional, development-only eval tools, never runtime dependencies; plugin scripts stay stdlib-only.

After changes run `python3 -m unittest discover -s tests -v` and validate both
plugin manifests. Tests must cover behavior, especially stale evidence, recovery,
review completion, and graph boundaries. Keep user-facing usage in README.md.
