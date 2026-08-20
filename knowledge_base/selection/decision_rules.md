Database Selection Rules and Anti-Patterns

Core Reasoning Summary

Definition: These rules provide high-level guardrails for database selection and architecture review.

Why they exist: They prevent technology-first reasoning and force the agent to connect a database choice to workload, data model, invariants, queries, and scaling requirements.

When to use: Use these rules as an early decision filter and review checklist before finalizing a database architecture.

When NOT to use: Do not treat any rule as an unconditional prohibition. Each rule is a default boundary that can be overridden when the actual workload and requirements provide explicit evidence.

Primary rule: The rules narrow candidates and reject weak reasoning; the final decision must still be grounded in the application's actual requirements.

Review questions:

What workload evidence supports the decision?

Which invariant or query requirement drives the database choice?

Is a specialized database solving a distinct problem?

What assumption would make the rule's default recommendation inappropriate?

Has the simplest viable architecture been considered?

Rules

Start with the workload, not technology popularity.

Choose the primary data model first.

Identify the strongest business invariants.

Design around important queries.

Prefer one database when one is sufficient.

Add Redis only for a concrete cache/ephemeral requirement.

Add OpenSearch only for a concrete search requirement.

Add Neo4j only when traversal is central.

Treat RocksDB as infrastructure/embedded storage, not default application storage.

Consider sharding only after simpler scaling mechanisms are inadequate.

Rule Boundaries

1. Start with the workload: Technology familiarity may still be an operational factor, but it must not replace workload analysis.

2. Choose the primary data model first: The data model narrows candidates; it does not automatically select a database. Business invariants, queries, workload, and operations still distinguish candidates.

3. Identify business invariants: An invariant identifies the required correctness guarantee. It does not by itself determine which database provides that guarantee.

4. Design around important queries: Query patterns guide schema and database selection, but one query should not automatically determine the entire architecture unless it is a dominant or correctness-critical workload.

5. Prefer one database when one is sufficient: This is a complexity preference, not a ban on multi-database architectures. Add systems when they provide a distinct requirement-level benefit.

6. Add Redis only for a concrete cache/ephemeral requirement: Low latency alone is not enough to make Redis authoritative transactional storage. Evaluate durability, consistency, source-of-truth, TTL, and failure behavior.

7. Add OpenSearch only for a concrete search requirement: A search box or text field alone is not sufficient. Dedicated relevance, fuzzy search, autocomplete, faceting, or similar search behavior should justify it.

8. Add Neo4j only when traversal is central: The existence of relationships is not sufficient. Variable-depth traversal and relationship discovery should be central workloads.

9. Treat RocksDB as infrastructure/embedded storage: Key/value access alone is not sufficient. The embedded local-storage deployment model must itself be a meaningful requirement.

10. Consider sharding only after simpler scaling mechanisms are inadequate: User count or traffic alone is not sufficient. Evaluate measured capacity, data size, growth, hotspots, availability, and distribution requirements.

Anti-patterns

"Modern system = microservices + 4 databases."

"10 million users = sharding."

"Search box = OpenSearch."

"Relationships = graph DB."

"Flexible schema = MongoDB."

"Fast = Redis as source of truth."

"Every table needs an index on every foreign key and filter."

"Every entity needs soft delete."

Anti-Pattern Boundary

The Review Agent should actively flag these patterns as reasoning warnings, not automatic rejection rules.

A technology or architecture mentioned by an anti-pattern can still be correct when the actual workload and requirements justify it.

For example:

multiple databases can be correct when each has a distinct workload requirement

sharding can be correct when simpler scaling mechanisms are inadequate

OpenSearch can be correct when dedicated search behavior is required

Neo4j can be correct when traversal is central

MongoDB can be correct when document boundaries and access patterns fit

Redis can be authoritative only when the application's durability and consistency requirements explicitly permit that architecture

indexes should be chosen from actual query patterns and cost

soft delete is appropriate when retention/hiding semantics are a concrete requirement

The anti-pattern is the unsupported reasoning shortcut, not necessarily the technology itself.

Source / grounding

Curated project decision rules.

Common Review Mistakes

Treating a default rule as an absolute law.

Treating an anti-pattern label as a ban on the named technology.

Selecting a database from one feature without checking the complete workload.

Using user count as a substitute for capacity analysis.

Treating "search box" as sufficient evidence for OpenSearch.

Treating relationships as sufficient evidence for Neo4j.

Treating flexible schema as sufficient evidence for MongoDB.

Treating low latency as sufficient evidence for Redis as source of truth.

Adding multiple databases without identifying distinct requirements.

Sharding before evaluating simpler scaling mechanisms.

Adding indexes without identifying the queries they support.

Adding soft delete without a retention or lifecycle requirement.