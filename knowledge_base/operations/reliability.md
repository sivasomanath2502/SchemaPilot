Reliability and Failure Handling

Core Reasoning Summary

Definition: Reliability and failure handling describe how an architecture behaves when components, dependencies, networks, or supporting systems fail instead of assuming the normal happy path.

Why it exists: A database architecture is not complete if it only explains successful requests. Reliability planning identifies failure modes, defines expected behavior, and prevents supporting-system failures from unnecessarily becoming authoritative-data failures.

When to use: Apply explicit failure handling whenever the architecture contains a database, cache, search system, replication/failover mechanism, asynchronous pipeline, or external dependency whose failure can affect correctness or availability.

When NOT to use: Do not add complex failover, fallback, or recovery mechanisms without a failure scenario and business requirement that justifies them.

Primary rule: Every important dependency should have an explicit failure behavior. The correct response may be fallback, retry, rebuild, degraded operation, or refusal of the operation depending on the data's correctness requirements.

Advantages: Makes failure behavior explicit, improves resilience, and exposes hidden single points of failure.

Disadvantages: Failure handling adds implementation and operational complexity, and fallbacks can introduce stale data or inconsistent behavior if their boundaries are not defined.

Review questions:

What happens when each critical dependency fails?

Which failures may be handled by fallback?

Which failures must stop the operation to preserve correctness?

Can derived systems be rebuilt from authoritative data?

How are retries bounded and made safe?

Where are the remaining single points of failure?

Reliability questions

For each architecture identify:

single points of failure

backup requirements

restore process

replication/failover

cache failure

search-index failure

partial network failure

Supporting system failure

If Redis fails, the application should define whether it falls back to the primary DB.
If OpenSearch fails, transactional operations should normally remain possible if search is non-critical.
If asynchronous indexing fails, records should be retried/rebuilt.

Failure-Handling Boundary

A fallback is sufficient only when the fallback can preserve the required correctness and availability semantics for that operation.

A Redis failure does not automatically require fallback to the primary database; fallback is appropriate only if the primary can safely handle the resulting load and the operation's semantics permit it.

Similarly, OpenSearch failure can be isolated from transactional operations only when search is genuinely non-critical for those operations.

For asynchronous indexing, retry or rebuild is sufficient only when the authoritative source remains available and the projection can be reconstructed without losing authoritative state.

Review rule

A design is incomplete if it only describes the happy path.

Common Mistakes

Assuming every dependency failure should trigger a fallback.

Falling back to a primary database without checking whether it can handle the additional load.

Treating a cache or search failure as equivalent to authoritative database failure.

Retrying operations without considering duplicate side effects or idempotency.

Designing failover without defining what happens to in-flight operations.

Assuming replication or failover eliminates every failure mode.

Claiming resilience without identifying remaining single points of failure.

Source / grounding

Curated reliability architecture knowledge.