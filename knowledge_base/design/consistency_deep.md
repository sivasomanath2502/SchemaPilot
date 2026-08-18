# Consistency and Source of Truth — Deep Explanation

## Definition
Consistency describes what values different operations can observe, and how multiple copies or representations of the same fact converge over time. It's a spectrum, not a binary — the right level depends on what the business rule can tolerate.

## Strong consistency
Use when stale data could violate a critical business rule. Examples: booking ownership, payment state, account balance, inventory reservation, unique identity checks.

## Eventual consistency
Temporary divergence between copies is accepted because the derived value will catch up shortly. Examples: search index, cache, recommendations, analytics projections, non-critical counters (e.g. a "likes" count that's off by one for a second is harmless).

## Source of truth
Every important business fact should have exactly one authoritative owner. Other representations of that fact are derived and disposable.

Example:
```
MySQL      -> authoritative order/payment state
Redis      -> cached representation (derived, disposable)
OpenSearch -> searchable projection (derived, disposable)
```
If a derived copy is lost or corrupted, it should always be reconstructable from the source of truth.

## Read-after-write problem
A user writes to the primary database, then immediately reads — but that read might hit a lagging replica or a stale cache entry, showing the old value right after the user just changed it. This is jarring for the user and must be explicitly designed for, not left to chance. See `replication_deep.md` for concrete mitigation strategies (read-from-primary for critical paths, session stickiness, consistency-aware routing).

## Failure reasoning
The architecture should explicitly state what happens when:
- the cache is unavailable
- search indexing has fallen behind or failed
- a downstream consumer of an event is delayed
- a read replica is stale beyond an acceptable window

Silence on these questions usually means the failure mode hasn't actually been thought through.

## Distributed consistency trade-off
Distributed systems can trade availability, consistency, and partition tolerance differently depending on design. Avoid citing "CAP theorem" as a slogan without connecting it to the actual business invariant and actual architecture in question — start from what the business rule requires, not from the theorem.

## Common mistakes
- Calling something "eventually consistent" without explaining *why* the staleness window is acceptable for that specific use case.
- Multiple components silently claiming to be the source of truth for the same fact (e.g. both a cache and the database being written to independently without a clear owner).
- Not defining read-after-write behavior for a user-facing action that should feel immediate (e.g. seeing your own new comment appear instantly).
- Treating CAP theorem as a design decision by itself, instead of a lens applied to a specific requirement.

## Review questions
- How stale can this value acceptably be?
- What happens if the update to a derived copy is delayed or fails?
- Can stale data here cause a financial, booking, or other critical-invariant error?
- Which component is the authoritative source of truth for this specific fact?
- How is a derived/cached representation rebuilt if lost?
- Does this specific user-facing action need read-after-write guarantees?

## Source / grounding
Curated distributed data architecture knowledge.
