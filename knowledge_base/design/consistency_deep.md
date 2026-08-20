Consistency and Source of Truth — Deep Explanation

Core Reasoning Summary

Definition: Consistency describes what values different operations can observe and how multiple copies or representations of the same fact converge over time.

Why it exists: Different workloads tolerate different amounts of staleness. Stronger consistency can protect critical business invariants, while eventual consistency can improve scalability and decouple derived systems when temporary divergence is acceptable.

When to use: Choose the consistency level from the business rule and user-facing requirement that the data must satisfy.

When NOT to use: Do not label data "eventually consistent" simply because it is stored in a cache, replica, or search index. The application must establish that the permitted staleness cannot violate the relevant requirement.

Primary rule: Every important business fact needs one authoritative owner. Other representations are derived and must have explicit freshness, failure, and rebuild behavior.

Advantages: Makes correctness and freshness requirements explicit and prevents accidental dependence on stale derived data.

Disadvantages: Stronger consistency can constrain availability or scalability, while weaker consistency requires explicit staleness and reconciliation handling.

Review questions:

How stale can this value acceptably be?

Can stale data violate a business invariant?

Which component owns the fact?

What happens if a derived copy is delayed or lost?

Does this user action require read-after-write behavior?

What consistency assumption is the architecture actually making?

Consistency describes what values different operations can observe, and how multiple copies or representations of the same fact converge over time. It's a spectrum, not a binary — the right level depends on what the business rule can tolerate.

Strong consistency

Use when stale data could violate a critical business rule. Examples: booking ownership, payment state, account balance, inventory reservation, unique identity checks.

Strong-Consistency Boundary

Strong consistency is sufficient when the operation requires reads to observe the authoritative state closely enough to preserve the stated business invariant.

It is not automatically required for every read of the same entity. Derived views such as search or analytics may use a weaker model when their specific product semantics tolerate staleness.

Eventual consistency

Temporary divergence between copies is accepted because the derived value will catch up shortly. Examples: search index, cache, recommendations, analytics projections, non-critical counters (e.g. a "likes" count that's off by one for a second is harmless).

Eventual-Consistency Boundary

Eventual consistency is sufficient only when the product explicitly permits the expected staleness window.

Calling a value "derived" does not automatically make eventual consistency acceptable. If stale data can cause a financial, booking, inventory, identity, or other critical-invariant error, the authoritative operation must use the required consistency mechanism.

Source of truth

Every important business fact should have exactly one authoritative owner. Other representations of that fact are derived and disposable.

Source-of-Truth Boundary

Having one authoritative owner is sufficient to define where correctness is decided, but it does not by itself guarantee that derived copies remain fresh or that failures are recoverable.

Each derived representation still needs an explicit update path, acceptable staleness, failure behavior, and rebuild strategy.

Example:

MySQL      -> authoritative order/payment state
Redis      -> cached representation (derived, disposable)
OpenSearch -> searchable projection (derived, disposable)

If a derived copy is lost or corrupted, it should always be reconstructable from the source of truth.

Read-after-write problem

Read-After-Write Boundary

Read-after-write behavior is a separate requirement from general consistency labeling.

A system may legitimately use eventual consistency for many reads while routing a specific user-facing action to the authoritative source when the user must immediately observe their own write.

A user writes to the primary database, then immediately reads — but that read might hit a lagging replica or a stale cache entry, showing the old value right after the user just changed it. This is jarring for the user and must be explicitly designed for, not left to chance. See replication_deep.md for concrete mitigation strategies (read-from-primary for critical paths, session stickiness, consistency-aware routing).

Failure reasoning

The architecture should explicitly state what happens when:

the cache is unavailable

search indexing has fallen behind or failed

a downstream consumer of an event is delayed

a read replica is stale beyond an acceptable window

Silence on these questions usually means the failure mode hasn't actually been thought through.

Distributed consistency trade-off

CAP Boundary

CAP is a lens for reasoning about distributed-system trade-offs under partition; it is not a database-selection rule by itself.

The agent must first identify the business invariant and actual failure/partition scenario before using CAP terminology to justify a design.

Distributed systems can trade availability, consistency, and partition tolerance differently depending on design. Avoid citing "CAP theorem" as a slogan without connecting it to the actual business invariant and actual architecture in question — start from what the business rule requires, not from the theorem.

Common mistakes

Calling something "eventually consistent" without explaining why the staleness window is acceptable for that specific use case.

Multiple components silently claiming to be the source of truth for the same fact (e.g. both a cache and the database being written to independently without a clear owner).

Not defining read-after-write behavior for a user-facing action that should feel immediate (e.g. seeing your own new comment appear instantly).

Treating CAP theorem as a design decision by itself, instead of a lens applied to a specific requirement.

Common Review Mistakes

Treating strong consistency as necessary for every read.

Treating eventual consistency as automatically safe for every derived value.

Calling data eventual-consistency-safe without specifying an acceptable staleness window.

Allowing multiple components to independently claim authority over the same business fact.

Confusing read-after-write requirements with a blanket requirement for strong consistency everywhere.

Using CAP terminology without connecting it to a concrete distributed failure and business requirement.

Review questions

How stale can this value acceptably be?

What happens if the update to a derived copy is delayed or fails?

Can stale data here cause a financial, booking, or other critical-invariant error?

Which component is the authoritative source of truth for this specific fact?

How is a derived/cached representation rebuilt if lost?

Does this specific user-facing action need read-after-write guarantees?

Source / grounding

Curated distributed data architecture knowledge.