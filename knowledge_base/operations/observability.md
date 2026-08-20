Database Observability

Core Reasoning Summary

Definition: Database observability is the practice of measuring database behavior and health through signals such as latency, resource usage, contention, replication lag, cache behavior, indexing lag, and errors.

Why it exists: Observability turns architectural assumptions into measurable evidence. It helps determine whether a database, index, cache, replica, or search system is actually solving the workload problem.

When to use: Use observability whenever an architecture makes performance, capacity, consistency, or reliability claims that should be validated from production or representative workload measurements.

When NOT to use: Do not treat a single metric as sufficient evidence for an architectural change. A metric should be interpreted in the context of the workload, query path, correctness requirements, and failure behavior.

Primary rule: Architectural recommendations should be tied to measurable symptoms or requirements rather than introduced solely because a technology is available.

Advantages: Enables evidence-based tuning, detects bottlenecks, and provides feedback for validating architectural decisions.

Disadvantages: Metrics add operational complexity, and measurements can be misleading if they do not represent the relevant workload or query path.

Review questions:

What measurable problem is the recommendation solving?

Which metric demonstrates that the problem exists?

Is the measurement representative of the workload?

What metric would show that the change worked?

Could the metric be a symptom rather than the root cause?

What correctness or reliability trade-off accompanies the optimization?

What to monitor

query latency

slow queries

CPU

memory

disk

connections

lock contention

replication lag

cache hit/miss

search indexing lag

error rate

Agent relevance

The Review Agent should prefer recommendations that can be measured.

Measurement Boundary

A measurable metric is evidence for an architectural decision, not automatically proof of its root cause.

A high latency metric, for example, does not by itself prove that Redis, an index, a replica, or another specific technology is required. The recommendation should connect the metric to the relevant query path, workload behavior, and bottleneck.

Likewise, the absence of a measured bottleneck is a reason to avoid speculative optimization, but it does not prove that no future scaling change will ever be required.

Example:
"Add Redis" should ideally be tied to a measurable read bottleneck or latency requirement.

"Add an index" should be tied to a query plan or high-frequency access path.

Source / grounding

Curated database observability knowledge.

Common Mistakes

Treating one metric as proof of a root cause.

Recommending Redis merely because traffic is high.

Recommending an index merely because a column appears in queries.

Measuring only averages and missing tail latency or contention.

Ignoring replication lag, cache staleness, or indexing lag when they affect user-visible behavior.

Making architecture changes without defining how success will be measured.

Treating observability as a substitute for understanding the actual workload and correctness requirements.