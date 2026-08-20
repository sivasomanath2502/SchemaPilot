Query-Aware Schema Design

Core Reasoning Summary

Definition: Query-aware schema design treats schema structure, indexes, and important query patterns as one design problem.

Why it exists: A schema that looks correct in isolation can still perform poorly for the application's dominant queries. Conversely, an optimization that helps one query can impose unnecessary write or maintenance cost.

When to use: Use query-aware design whenever schema, indexing, denormalization, pagination, or supporting-database decisions are being considered.

When NOT to use: Do not optimize around a query that is rare, unimportant, or not representative of the actual workload unless it is correctness-critical.

Primary rule: Every non-trivial schema or database optimization should be traceable to an important workload/query requirement.

Advantages: Connects database structure to actual application behavior and reduces speculative optimization.

Disadvantages: Requires realistic query patterns, cardinality estimates, frequency, and latency requirements.

Review questions:

Which queries are actually important?

What filters, joins, sorting, grouping, and cardinalities do they have?

How frequently do they run?

What latency is required?

What schema/index change does the query justify?

Could the same problem be solved more simply?

Has the resulting query plan been validated?

Principle

Schema, indexes and query patterns should be designed together.

Query analysis

For each important query identify:

Query-Importance Boundary

A query is a design driver when it is sufficiently important because of frequency, latency sensitivity, business importance, or resource cost.

The presence of a query alone does not justify a specialized index, denormalized structure, cache, or database.

filters

joins

sorting

grouping

expected cardinality

frequency

latency requirement

Example

Example Boundary

The order-history query justifies investigating an index aligned with user_id and created_at; it does not by itself prove that the index is required.

The actual query plan, data distribution, frequency, and workload should determine whether the index provides enough benefit to justify its maintenance cost.

User order history:
WHERE user_id = ?
ORDER BY created_at DESC

This naturally motivates investigation of a composite index aligned to user_id and created_at.

Escalation order

First optimize query/schema/indexes. Then consider caching or read models. Only then consider specialized databases.

Escalation Boundary

This is a default simplification strategy, not an absolute ordering rule.

If a requirement already establishes that a specialized capability is fundamental—for example, dedicated relevance search or central graph traversal—the agent may evaluate that capability directly.

However, a specialized database should not be introduced merely to compensate for an unoptimized query or schema.

Review rule

Every non-trivial index, denormalization or supporting database should have a workload/query justification.

Justification Boundary

A workload/query justification establishes why an optimization is being considered; it does **not automatically prove that the proposed optimization is the best solution.

The agent should compare simpler alternatives, expected benefit, operational cost, and correctness implications before finalizing the decision.

Source / grounding

Curated query-aware database design knowledge.

Common Review Mistakes

Designing indexes from the schema without looking at real queries.

Treating every query as equally important.

Assuming a query's existence proves an index or denormalization is necessary.

Optimizing a rare query while ignoring the dominant workload.

Adding a specialized database before checking schema/query/index alternatives.

Treating the escalation order as an absolute rule.

Failing to consider write and maintenance costs.

Making a query-aware recommendation without validating the resulting query plan.