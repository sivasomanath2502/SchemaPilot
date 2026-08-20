Database Architecture Anti-Patterns — Deep Review Guide

Core Reasoning Summary

Definition: An anti-pattern is a recurring architectural choice that appears reasonable but creates predictable correctness, scalability, or operational problems in the stated context.

Why it exists: Anti-patterns help the Review Agent reject attractive but weak reasoning, especially technology-first decisions that are not supported by workload or business requirements.

When to use: Use these rules when reviewing a proposed architecture or database selection to test whether a recommendation is requirement-driven.

When NOT to use: An anti-pattern label is not an absolute prohibition. A choice such as sharding, Redis, OpenSearch, MongoDB, soft delete, or multiple agents can be valid when the workload and requirements justify it.

Primary rule: Flag the reasoning pattern, not merely the technology. The same technology can be correct in one workload and an anti-pattern in another.

Advantages: Prevents premature complexity and encourages evidence-based architecture decisions.

Disadvantages: Overusing anti-pattern rules as hard bans can reject valid architectures.

Review questions:

What requirement justifies the proposed technology or mechanism?

What measurable workload evidence supports it?

Is the recommendation solving the actual bottleneck or invariant?

What simpler alternative was considered?

Is the anti-pattern being treated as a conditional warning or an absolute rule?

Premature sharding

Adding sharding before demonstrating a single-node capacity problem.

Boundary: Sharding is not an anti-pattern when simpler scaling mechanisms are inadequate and measured capacity, storage, availability, or distribution requirements justify it. The anti-pattern is adopting it without that evidence.

Technology shopping

Adding MySQL + MongoDB + Redis + OpenSearch simply to make an architecture look advanced.

Boundary: Multiple databases are justified when each addresses a distinct workload or requirement that the primary database does not satisfy well. The anti-pattern is adding them without distinct requirements.

Cache as source of truth

Using Redis as authoritative transactional state without understanding durability and consistency requirements.

Boundary: Redis is appropriate as authoritative state only when the application's durability and consistency requirements are explicitly compatible with that choice. The anti-pattern is assuming low latency makes Redis sufficient for correctness-sensitive transactional state.

Search as transaction store

Using OpenSearch as the authoritative payment, booking or inventory system.

Boundary: OpenSearch can contain derived representations of transactional data and is appropriate when search is the actual workload. The anti-pattern is using search capabilities as a substitute for the authoritative transactional mechanism.

Index everything

Adding indexes without identifying the queries they support.

Boundary: An index is justified when a concrete query/access path benefits from it enough to outweigh storage and write-maintenance cost. The anti-pattern is indexing without a workload or query rationale.

Graph because relationships exist

Every relational application has relationships. Graph databases are for relationship-centric traversal.

Boundary: Neo4j or another graph database becomes a candidate when variable-depth traversal and relationship discovery are central workloads. Ordinary relationships or CRUD are not sufficient justification.

MongoDB because schema is flexible

Flexibility is useful only when it matches access patterns and data ownership.

Boundary: Flexible schema is a selection signal only when document boundaries, access patterns, and ownership benefit from it. JSON-like data alone is not sufficient.

Replica solves writes

Read replicas primarily help reads/availability; they do not automatically increase primary write capacity.

Boundary: Replicas can reduce read load or improve read availability when the workload permits replication lag. They do not make a single primary write path horizontally scalable by themselves.

User count means sharding

User count must be translated into traffic, data size, concurrency and capacity requirements.

Boundary: A large user count can justify sharding only when the resulting workload exceeds simpler capacity or distribution options. User count alone is not a capacity measurement.

Strong consistency everywhere

Not every derived value requires immediate consistency. Search and cache can often tolerate staleness.

Boundary: Eventual consistency is acceptable only when the product semantics permit temporary staleness. Correctness-sensitive invariants still require the appropriate authoritative consistency mechanism.

Soft delete everywhere

Soft delete introduces query, uniqueness and storage complexity and should be a requirement-driven choice.

Boundary: Soft delete is justified when retaining records while hiding them from normal access is a concrete requirement. It is not automatically required for every entity.

Agent-specific anti-pattern

Do not create an agent for every tiny task. Four well-defined agents are easier to reason about than ten loosely defined agents.

Boundary: The number of agents should follow clear responsibility boundaries and coordination needs. Four agents is not a universal optimum; more agents can be justified when their responsibilities are distinct and their interactions remain understandable.

Common Review Mistakes

Treating an anti-pattern warning as an absolute prohibition.

Rejecting a technology without checking the workload-specific boundary.

Using user count, request volume, or "modern architecture" as a substitute for capacity analysis.

Flagging a technology without identifying the actual invariant, query, or operational problem involved.