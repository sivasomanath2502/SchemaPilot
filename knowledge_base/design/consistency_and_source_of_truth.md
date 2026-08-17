# Consistency and Source of Truth


## Strong consistency candidates
- payments
- account balances
- booking ownership
- inventory reservation
- unique identities

## Eventual consistency candidates
- search projections
- caches
- recommendations
- analytics
- non-critical counters

## Source of truth
Every business fact should have an authoritative owner.

Example:
MySQL = order/payment truth
Redis = cache
OpenSearch = search projection

## Failure reasoning
The architecture should explain what happens when:
- cache is unavailable
- search indexing fails
- a consumer is delayed
- a replica is stale

## Review rule
Do not call something "eventually consistent" without explaining why staleness is acceptable.


## Source / grounding
Curated distributed data architecture knowledge.
