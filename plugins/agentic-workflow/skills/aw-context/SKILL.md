---
name: aw-context
description: Retrieve scoped Mem0 context and prepare compact worker packets; use project relationship indexes when relevant.
---

# Shared project context

Read [the shared contract](../../references/workflow.md) and
[Mem0-only memory](../../references/memory.md). Start with one scoped Mem0 recall
for the active slice. Prepare a small source/snapshot-linked packet for workers;
do not have every child repeat the search. Record actual memory status and save
accepted lessons through Mem0 only. Do not access Obsidian or another memory store.

If structural relationships answer the task, use the existing project index below
and [knowledge graph format](../../references/knowledge.md). It is a project
artifact; do not create a new graph or index just to support memory recall.

Use a graph only when relationships help answer a concrete question. Reuse an
existing graph if available; otherwise keep a curated JSON index in the project.
This graph describes project knowledge. The separate execution graph routes work.

1. Start with IDs already present in the domain document, PRD, ADRs and roadmap.
   Add nodes for terms, rules, requirements, decisions, slices and important code
   seams. Do not index every symbol or generate a second copy of the codebase.
2. Add typed edges with a source reference. Preserve direction: `S depends_on D`
   means D must complete before S. `S implements R`, `R uses_term T`, and
   `TEST verifies R` support context selection and impact tracing.
3. Distinguish accepted facts from proposed relationships. Preserve superseded
   nodes and explicit replacement links. Check contradictory terms against the
   bounded context before merging them. Never auto-promote an inferred edge.
4. Query a small bounded neighborhood around the active slice or changed concept.
   Read the returned sources. Follow omitted important dependencies separately;
   a bounded query is not exhaustive review coverage. Report truncation.
5. After accepted changes, update affected edges and provenance. Validate dangling
   IDs and dependency cycles. Treat the graph as an index: canonical docs/code
   remain authoritative, and stale edges must be checked before use.

Mem0 does not replace typed dependency checks or exact execution checkpoints.
No additional graph server, embeddings or memory provider are required.
