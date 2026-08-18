# Consistency and Source of Truth — Deep Explanation

## Definition
Consistency describes what values different operations can observe and how multiple copies/representations converge.

## Strong consistency
Use when stale data can violate a critical business rule.
Examples: booking ownership, payment state, account balance, inventory reservation.

## Eventual consistency
Temporary divergence is accepted because the derived value can catch up.
Examples: search index, cache, recommendations, analytics projections.

## Source of truth
Every important business fact should have one authoritative owner.

Example:
MySQL -> authoritative order state
Redis -> cached representation
OpenSearch -> searchable projection

## Read-after-write
A user may write to the primary and immediately read from a lagging replica or stale cache. The system must define whether that is acceptable.

## Distributed consistency trade-off
Distributed systems can trade availability, consistency and partition tolerance in different ways. Avoid using CAP as a slogan; start with the business invariant and actual architecture.

## Review questions
- How stale can this value be?
- What happens if the update is delayed?
- Can stale data cause financial or booking errors?
- Which component is authoritative?
- How is derived state rebuilt?
