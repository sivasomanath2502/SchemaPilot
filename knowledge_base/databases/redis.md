# Redis — Full Selection Profile


## Role
In-memory data structure store used for low-latency key-oriented workloads, caching and ephemeral/derived state.

## Useful data structures
Strings, hashes, lists, sets, sorted sets, streams and specialized structures. Select the structure based on access pattern rather than convenience.

## Strong selection signals
- Cache
- Session store
- Rate limiter
- Counter
- Leaderboard
- Queue/stream
- Low-latency key access
- Ephemeral state

## Cache architecture
Define:
- key design
- TTL
- invalidation
- cache miss behavior
- stale-data tolerance
- failure behavior
- memory/eviction policy

## Source of truth
For payments, inventory ownership, account balances and bookings, Redis should not become authoritative merely because it is fast. Keep a durable transactional source of truth when required.

## Scaling
Redis Cluster can distribute keyspace. Evaluate hot keys, memory, eviction, persistence, replication and failure recovery.

## Weak-fit signals
Complex joins -> relational.
Large durable relational dataset -> relational.
Full-text search -> OpenSearch.
Embedded storage engine -> RocksDB.


## Source / grounding
https://redis.io/docs/latest/develop/data-types/
