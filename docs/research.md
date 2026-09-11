# Design research — 2026-09-06

The requested graph engineering covers both agent orchestration and project
knowledge. They share IDs and artifact references, but serve different purposes.

| Approach | Findings | Choice for this plugin |
| --- | --- | --- |
| Graph Engineering research | Recent work describes explicit evolving structures for tasks, agents and system state; the term is emerging, not a single standard. | Apply explicit routes, roles, evidence and bounded feedback. Do not claim an optimal topology or guaranteed savings. |
| LangGraph | A full stateful graph runtime with persistent checkpointers and replay. Replayed nodes can run again; side-effect/idempotency boundaries remain important. | Defer adoption until an external scheduler, many concurrent runs, or durable distributed execution is needed. The current coding host already executes agents. |
| Agent Graph (`@c4a/agent-graph`) | A skills-oriented work-contract layer that supplies routes/resources from facts; it explicitly does not schedule agents or invoke models. | Closest conceptual fit. Its provider/schema/host integration adds more machinery than this fixed workflow needs. Use a small explicit transition table now; reconsider this existing package before expanding into a generic engine. |
| Microsoft GraphRAG | Extracted knowledge graphs support local entity queries and broad community-summary retrieval. Global search can be resource-intensive. | Not an orchestration tool, and corpus-wide LLM extraction is unnecessary for a small project relationship index. |
| DDD ubiquitous language | Domain experts and developers share precise language tied to the model and refine it through use. | Establish terms, examples, invariants and context boundaries, then reuse them through planning, implementation and review. No mandatory tactical DDD architecture. |

Implementation: one graph for legal stage transitions and review/repair routing;
one optional curated node/edge document for project context. The host agent owns
worker selection and concurrent execution. The helper owns checkpoint writes,
revision checks and structural completion gates. It does not attest model output
or implement a distributed scheduler. Memory providers remain optional.

Reviewed primary sources:

- [Graph Engineering in the Era of LLM Agents](https://arxiv.org/abs/2608.21156)
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangGraph replay tests](https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/tests/test_time_travel.py)
- [Agent Graph](https://github.com/context4ai/agent-graph)
- [Microsoft GraphRAG query overview](https://microsoft.github.io/graphrag/query/overview/)
- [Ubiquitous Language — Martin Fowler](https://martinfowler.com/bliki/UbiquitousLanguage.html)
- [Codex plugin authoring](https://learn.chatgpt.com/docs/build-plugins)
- [Claude plugin authoring](https://code.claude.com/docs/en/plugins)
- [Mem0 MCP](https://docs.mem0.ai/platform/mem0-mcp)

Context7 was used for current Codex/Claude plugin packaging and LangGraph replay
semantics. Local CLI help was checked for supported plugin/validation commands.
No end-to-end token savings, autonomous milestone success rate, or model quality
benchmark is claimed. Behavioral tests exercise local state/graph invariants.

## Focused models and bounded context — 2026-09-11

The user supplied a Reddit account of frontier-model orchestration with cheaper
scouts/builders and strong independent refuters. Its usage percentages lack a
controlled baseline, task mix and quality measurements; no savings percentage is
inferred. Adopt its concrete practices: role-specific models, exact ownership,
bounded context, short reports, artifact handoffs, independent checks and no
overlapping editors. Do not automatically adopt every named plugin or the
author's model names. Local defaults reflect available Codex models and Claude
aliases; record substitutions and evaluate on a real slice.

Current primary documentation and local CLI checks:

- [Codex custom subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents):
  native TOML profiles under personal/project `.codex/agents`; explicit model and
  reasoning effort; profile settings override spawn settings. Install profiles
  explicitly rather than inventing a Codex plugin-manifest agents field.
- [Codex role parser](https://github.com/openai/codex/blob/main/codex-rs/agent-roles/src/agent_role_config.rs):
  required name, description and developer instructions; normal config fields.
- [Codex config reference](https://learn.chatgpt.com/docs/config-file/config-reference):
  per-profile `model_auto_compact_token_limit=200000`, scope `total`, selects a
  compaction trigger without changing the coordinator or model capacity.
- [Claude subagents](https://code.claude.com/docs/en/sub-agents): fresh scoped
  contexts, explicit model/tool selection, maxTurns; parent skill invocation is
  not inherited. Embed essential Caveman/Ponytail rules in each profile.
- [Claude plugin reference](https://code.claude.com/docs/en/plugins-reference):
  native `agents/*.md`; plugin agent hooks/permissionMode are not a per-agent
  environment mechanism. No unsupported frontmatter is used.
- [Claude environment variables](https://code.claude.com/docs/en/env-vars#claude_code_auto_compact_window):
  `CLAUDE_CODE_AUTO_COMPACT_WINDOW=200000` selects the compaction calculation
  window, capped by actual model capacity. Default trigger ~95%. Process/session
  scope includes coordinator and subagents; no claim of subagent-only enforcement.

Context7 and official pages checked; local clients Codex 0.154.0 and Claude
2.1.268. Profile loading/checks do not prove model quality or guaranteed savings.
Measure actual selected models, token use, retries and accepted outcomes in a pilot.
