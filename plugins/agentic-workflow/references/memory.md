# Mem0-only shared memory

Mem0 is the exclusive provider for cross-session recall and durable lessons.
Do not use Obsidian, Serena memories, another memory server, or parallel automatic
memory stores for this workflow. Canonical PRDs/domain/plans/source and exact
execution checkpoints remain project artifacts; they are not competing memory
providers. Never replace exact checkpoint state with a probabilistic memory result.

## Coordinator entry and handoff

1. Identify the actual Git repository/worktree, user and project/app namespace.
   An umbrella directory may have a different namespace from its nested repos.
   Reuse the configured identity in both clients. Native Mem0 coding-plugin search
   accepts `scope=repo|dir|mine`; a hosted Mem0 MCP may require explicit filters.
   Do not assume tools with similar names search the same namespace.
   Prefer one verified Mem0 read/write MCP connection for coordinator operations.
   If a duplicate coding-plugin search fails while that connection works, use the
   verified connection and report the failed adapter; do not repeatedly invoke
   both. Do not claim automatic capture works merely because manual MCP calls do.
2. Search Mem0 once for the active slice's decisions, domain terms and lessons.
   Start with top_k=3 and a 4,000-character memory allowance. Include memory IDs,
   date/source and uncertainty. One narrowed follow-up only if material information
   is missing. Do not query memory before every grep, test or repair turn.
3. Prepare a worker packet (target 2–4k tokens): accepted scope, relevant Mem0
   facts, code/caller/test locations, prior findings and exact write ownership.
   Include repository/worktree, HEAD and dirty-file fingerprint; validate recalled
   code claims against current source. Refresh affected parts after edits.
4. Include `Memory status:` in each dispatch brief. Record `verified` with query,
   scope and returned IDs (or verified empty result), or `unavailable` with actual
   error. Do not turn a failed search into an empty result. Workers consume the
   coordinator's Mem0 packet rather than repeat recall or load unrelated plugins.
   A worker needing more context returns one specific retrieval question.
5. At accepted decisions, slice completion or handoff, save a short factual lesson
   once through Mem0. Include source, project, date, status and supersession. With
   read/write MCP, verify event completion and read/search the result. With a
   capture-only plugin, a session answer is evidence for later extraction, not
   proof it has been stored: verify recall before claiming persistence. Prefer
   explicit writes for essential decisions. Do not copy transcripts or logs into
   extra stores, repeat unchanged memories, or save secrets.

Mem0 failure: record the error, continue authorized work from explicit documents
and the current packet when sufficient, retry at the next useful boundary. Ask
for credentials only when needed; never invent them. No fallback to another memory
provider, and no claim of verified shared recall until a real search succeeds.

## Minimal workers

Workers need Caveman/Ponytail behavior, the Mem0-derived packet and role-specific
code tools. Their profile embeds those behavior rules; loading full skill libraries
again adds redundant context. Do not expose Skill or general MCP discovery merely
to obtain rules already present. The coordinator alone writes Mem0 and checkpoints.

Use `scripts/run_worker.py` for isolated CLI workers. It disables unrelated plugin/
MCP surfaces and supplies profile instructions plus the coordinator packet. It
does not pretend to query Mem0 itself or validate the truth of the packet. Keep
raw worker output as evidence; incomplete/error/timeout results are not success.

Native Claude agents have explicit tool allowlists; enabled plugin hooks remain
session-level. Codex native roles can disable plugins/skill instructions, but
cannot selectively remove inherited MCP servers. Native workers are acceptable
only in an already minimal host session or when the user accepts that limit.
Otherwise use the isolated process path. Do not advertise a prompt instruction
as technical plugin isolation. Managed policies and project instructions remain
authoritative; report enforced integrations the host cannot suppress.

## Usage budget

200k compaction is a recovery ceiling, not a normal worker size or weekly budget.
Keep routine work well below it through bounded scope and compact handoffs. Use
one coordinator per slice, one builder, then independent scoped review. Preserve
existing required reviewers; changing reviewer count is a product policy decision.
Run deterministic checks before model review, batch valid fixes, and rereview
affected behavior. Reuse still-valid coverage with a recorded rationale. Stop at
the existing repair cap for diagnosis rather than continuing an expensive loop.

Prefer one frontier planning pass, not duplicate PRD/roadmap generation by both
providers. Routine well-specified execution may use a mid-tier coordinator;
reserve frontier effort for material architecture, ambiguous failures and high-risk
judgment. This is a recommendation, not an automatic change to the user's model
or acceptance requirements. Measure accepted slices and total usage, including
retries, retrieval and memory extraction; terse prose alone cannot guarantee savings.
