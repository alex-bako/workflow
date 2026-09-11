# Shared context options — 2026-09-11

Research for the user's request to avoid repeated codebase discovery in fresh
Codex/Claude workers. Recommendations below are proposals, not installed changes
or measured performance rankings. Obsidian is not proposed as a runtime dependency.

## Recommendation

Start with **Serena for current code retrieval + Mem0 for durable decisions and
lessons**, after fixing/verifying Mem0. Keep exact run state in the existing
workflow checkpoints. Evaluate Hindsight as a replacement memory backend if its
coding-specific ingestion/knowledge pages outperform curated Mem0 retrieval.
Use only one primary memory backend to avoid duplicate capture and contradictions.

The largest workflow improvement is retrieving context once per bounded task,
then supplying that context to each worker. A memory server alone does not provide
shared model context or stop agents repeating exploration. New workers still need
their own task instructions, current source evidence and access to the right tools.

## Candidates

| Tool | Verified capabilities | Fit / limits |
| --- | --- | --- |
| [Mem0 coding integration](https://github.com/mem0ai/mem0/blob/main/integrations/claude-code-plugin/README.md) | Repository/project and personal namespaces, automatic capture and later recall, explicit bounded search. | Decisions, DDD language, commands and lessons. Asynchronous extraction is unsuitable for immediate exact handoff state; not a code index. Same backend and repo identity must be verified across clients. |
| [Serena](https://github.com/oraios/serena) | Symbol/reference navigation through language servers or a JetBrains backend; MCP clients include Codex and Claude. | Recommended first code retrieval option. LSP backend is open source; language-server setup remains necessary. Semantic symbols are not the same as natural-language vector retrieval. |
| [Augment Context Engine](https://docs.augmentcode.com/context-services/mcp/overview) | Semantic code retrieval; local MCP follows working-directory edits, remote indexing follows selected default branches; both clients supported. | Managed alternative for broader code retrieval. Paid usage/auth required. For implementation use working-directory indexing, not default-branch results as proof of uncommitted work. A local MCP process does not by itself establish local-only processing. |
| [Hindsight Coding Agents](https://github.com/vectorize-io/hindsight/blob/main/hindsight-docs/docs-integrations/coding-agents.md) | Shared per-repo memory banks, git/session ingestion, architecture/convention knowledge pages; Codex and Claude adapters; cloud, self-hosted or daemon modes. | Strong candidate for richer coding memory. Adds ingestion/retention infrastructure and model work; its startup hooks do not prove every custom child gets context. Pilot before replacing Mem0. |
| [codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) | Persistent structural code graph, call-chain/impact queries, shared coordination daemon, documented Codex/Claude subagent hooks. | Closest graph-oriented alternative for avoiding repeated structural scans. Installer also manages agents/hooks; integrate narrowly with our profiles. Validate language coverage and worktree freshness. Vendor token-saving claims are not a result on this project. |
| [Graphiti MCP](https://github.com/getzep/graphiti/tree/main/mcp_server) | Temporal entities/relations, hybrid retrieval and incremental episodes; graph database and model/embedding integrations. | Consider when historical domain relationships justify it. MCP server is labeled experimental; building ingestion and operating a graph adds work. Not a drop-in current-code index. |

Serena's [workflow documentation](https://github.com/oraios/serena/blob/main/docs/02-usage/040_workflow.md)
explicitly supports multiple agents sharing one HTTP server instance and its
resources for one project. It pre-caches symbols and updates the index after file
changes. Different projects use separate instances. For this workflow, bind each
instance to a specific worktree; never let parallel tasks switch a shared active
project behind one another. Follow the maintainer's current quickstart rather than
an outdated marketplace command.

## Proposed plugin integration

1. Coordinator identifies actual repository, worktree, HEAD and dirty-file hashes.
   Retrieve relevant accepted decisions/terms and current symbol locations once.
2. Emit a bounded context packet, initially target 2–4k tokens: slice acceptance,
   domain invariants, known decisions, relevant code/callers/tests, prior findings,
   exact write ownership and source/snapshot references. This is an initial budget
   to evaluate, not a correctness cap.
3. Every worker receives the packet and its focused brief. Child contexts do not
   inherit the parent's memory automatically. Permit specific read-only retrieval
   tools when supported, or have the coordinator resolve a narrow follow-up query.
   Current Claude worker tool allowlists need explicit integration; merely adding
   an MCP server is insufficient.
4. Refresh only affected context after source changes. Mark memory as a dated
   hypothesis until verified against current code; cache keys include worktree and
   dirty content, not HEAD alone. Independent refuters still inspect source and
   rerun relevant checks.
5. Save verified reusable lessons once through the coordinator. Exact outstanding
   findings, snapshot and next action remain in existing workflow run state.

Obsidian can remain a human-facing archive if desired, but no worker needs it on
this proposed execution path. No context provider was installed or migrated during
this investigation.

## Local observations and acceptance pilot

As of 2026-09-11, installed Codex Mem0 0.3.1 search returned `Memory search failed`.
Its CLI diagnostic using the default Codex data directory reported no API key,
zero capture/flush/retrieval events and scope `local:/Users/alex.bako/work/agentdoc`.
This is the umbrella workspace scope, not proof of memory setup for each nested
repository. A separate hosted `mem0-mcp` connector is configured; its authentication
and shared namespaces were not validated here. Do not claim all Mem0 storage is
broken or empty from the plugin failure alone.

Before adoption, test one real slice in both clients: retrieve the same known
decision, query a symbol and caller, edit an uncommitted file and prove retrieval
sees it, then run two simultaneous worktrees without mixed results. Measure total
tokens including ingestion/retrieval, repeated reads, elapsed time, accepted checks
and repair count against the current workflow. No performance benchmark was run
for Serena, Augment, Hindsight, codebase-memory-mcp or Graphiti in this investigation.
