# Optional curated knowledge graph

Read a small existing index directly. The query helper below is a convenience,
not a skill prerequisite; do not create an index solely to use this plugin.

This is a project-owned index, not an automatically inferred source of truth.
Use existing requirement, ADR, term and slice IDs. Nodes and edges carry provenance.
Keep detailed content in canonical documents/code. Querying follows both incoming
and outgoing edges for context; stored relation direction retains its meaning.

```json
{
  "nodes": [
    {"id":"TERM-reservation","kind":"term","label":"Reservation","status":"accepted","source":"docs/domain/DOMAIN.md#reservation"},
    {"id":"REQ-1","kind":"requirement","label":"Reserve available inventory","status":"accepted","source":"docs/product/PRD.md#req-1"},
    {"id":"M1.T1","kind":"slice","label":"Reserve one item end to end","status":"accepted","source":"docs/roadmap/ROADMAP.md#m1t1"}
  ],
  "edges": [
    {"from":"REQ-1","relation":"uses_term","to":"TERM-reservation","status":"accepted","source":"docs/product/PRD.md#req-1"},
    {"from":"M1.T1","relation":"implements","to":"REQ-1","status":"accepted","source":"docs/roadmap/ROADMAP.md#m1t1"}
  ]
}
```

Recommended node kinds: term, invariant, context, requirement, decision, milestone,
slice, code, test. Recommended relations: uses_term, constrains, belongs_to,
implements, verifies, depends_on, supersedes, translates_to. Add new kinds/relations
when a concrete retrieval or impact question needs them; no ontology framework.

`depends_on` edges form a DAG. Other relations can contain cycles. Proposed or
superseded nodes/edges are retained but excluded from normal context retrieval.
Store an optional `commit` or timestamp where it helps detect stale provenance.
Two bounded contexts may intentionally contain different terms with the same label;
use distinct IDs. Source anchors are checked by the agent, not resolved by the CLI.

```sh
python3 /path/to/plugin/scripts/workflow.py context docs/workflow/knowledge.json
python3 /path/to/plugin/scripts/workflow.py context docs/workflow/knowledge.json --seed M1.T1 --hops 2 --limit 15
```

Without `--seed` this validates structure, IDs, dangling references and dependency
cycles. With a seed it returns a bounded accepted neighborhood, internal edges and
a truncation flag. Distance and deterministic ID order govern selection; this is
not semantic ranking. A missing edge does not prove absence of impact. Read source
material and inspect callers/tests before deciding safety or completion.

Use this index for questions such as “which invariant does this slice implement?”
and “which slices depend on this decision?” Use normal code search/LSP for detailed
symbol navigation. Introduce a graph database or extracted code graph only if
measured size/update/query needs exceed this curated index.
