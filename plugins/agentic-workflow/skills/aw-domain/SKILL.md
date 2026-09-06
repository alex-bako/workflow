---
name: aw-domain
description: Establish or refine a project's DDD ubiquitous language, business invariants and bounded contexts before planning or after domain changes.
---

# Domain language and modeling

Read [the shared contract](../../references/workflow.md). Use the PRD and real
examples, and inspect existing code terminology before proposing replacements.

1. Walk through a concrete business scenario with the user. Identify actors,
   intentions/commands, facts/events, objects with identity, meaningful values,
   and rules. Ask one question at a time where meanings diverge. Prefer domain
   verbs and nouns to infrastructure words such as manager, handler or record.
2. Create a ubiquitous-language table: stable term ID, preferred term, precise
   definition, context, concrete example/counterexample, aliases or discouraged
   ambiguous names. Track proposed/accepted status and the source of acceptance.
   Do not infer synonyms merely because names are similar.
3. Record invariants as falsifiable statements and examples. Distinguish business
   rules from technical choices. Identify identity and lifecycle only where they
   matter. Express transitions and failure outcomes using the agreed terms.
4. Identify bounded contexts only where language, ownership or rules differ.
   The same word may legitimately have different meanings in two contexts.
   Describe integration contracts and translations. Contexts do not automatically
   become microservices, repositories, or database boundaries.
5. Model aggregates/transaction boundaries, value objects, domain services, or
   events only when a concrete invariant requires them. A glossary plus scenarios
   and rules is sufficient for a simple domain. Never mandate repositories,
   factories, event sourcing, CQRS or class hierarchies merely to satisfy DDD.
6. Write/update the domain document and reconcile PRD terms. Link terms/rules to
   requirements and decisions using `aw-context` when a knowledge graph exists.
   Preserve existing API names until a deliberate migration is planned.

Exit: key scenarios can be described unambiguously; important rules have examples;
boundary translations and remaining ambiguities are explicit. Plans, code, tests
and reviews must reuse this language. When implementation teaches something new,
update the model with provenance rather than leaving a one-time glossary stale.
