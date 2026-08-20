Redis — Full Selection Profile

Role

In-memory data structure store used for low-latency key-oriented workloads, caching and ephemeral/derived state.

Core Selection Summary

Definition: Redis is an in-memory data structure store used for low-latency key-oriented workloads, caching, and ephemeral or derived state.

Why it exists: Redis is optimized for fast access to data structures such as strings, hashes, lists, sets, sorted sets, and streams when the access pattern benefits from low latency and key-oriented operations.

When to use: Prefer Redis for cache, session storage, rate limiting, counters, leaderboards, queues/streams, low-latency key access, or other ephemeral/derived state where its operational characteristics fit the workload.

When NOT to use: Do not select Redis as the authoritative database for payments, inventory ownership, account balances, or bookings merely because it is fast. Do not use it as a substitute for relational storage when complex joins or a large durable relational dataset are central requirements.

Primary selection rule: Select Redis because the workload needs low-latency key-oriented access or one of its data structures—not because any application data can technically be stored as a key/value pair.

Advantages: Very low-latency access, multiple useful data structures, and strong fit for caching and ephemeral workloads.

Disadvantages: Memory capacity and eviction behavior must be managed; distributed deployments introduce hot-key, replication, persistence, and failure-recovery concerns.

Review questions:

Is the dominant access pattern key-oriented and latency-sensitive?

Is the data authoritative or derived/ephemeral?

What TTL, invalidation, and stale-data rules apply?

What happens on cache miss or Redis failure?

Are there hot keys or memory/eviction risks?

Does the workload actually require Redis rather than a durable relational store?

Useful data structures

Strings, hashes, lists, sets, sorted sets, streams and specialized structures. Select the structure based on access pattern rather than convenience.

Data-Structure Boundary

A Redis data structure is appropriate when its operations directly match the application's access pattern.

The availability of many data structures is not sufficient reason to choose Redis. The workload must benefit from their low-latency, key-oriented semantics and the operational model of Redis.

Strong selection signals

Cache

Session store

Rate limiter

Counter

Leaderboard

Queue/stream

Low-latency key access

Ephemeral state

Cache architecture

Define:

key design

TTL

invalidation

cache miss behavior

stale-data tolerance

failure behavior

memory/eviction policy

Cache Boundary

A Redis cache is sufficient when the cached data can tolerate the defined staleness and the system has a correct behavior for cache misses and Redis failures.

The cache is not required to establish correctness when the authoritative database already provides the needed invariant.

A cache entry must not silently become authoritative merely because it is faster to read.

Source of truth

For payments, inventory ownership, account balances and bookings, Redis should not become authoritative merely because it is fast. Keep a durable transactional source of truth when required.

Source-of-Truth Boundary

Redis may store a copy or derived representation of authoritative data.

For correctness-sensitive state such as payments, inventory ownership, account balances, and bookings, Redis is not sufficient by itself to establish durable transactional correctness merely because it provides low latency.

The authoritative durable system must make the correctness decision when such a requirement exists.

Scaling

Redis Cluster can distribute keyspace. Evaluate hot keys, memory, eviction, persistence, replication and failure recovery.

Scaling Boundary

Redis Cluster can distribute keyspace when the workload requires it, but clustering is not required merely because the dataset or request volume is large.

Before distributing Redis, evaluate key distribution, hot keys, memory pressure, eviction behavior, persistence requirements, replication, and failure recovery.

Weak-fit signals

Complex joins -> relational.
Large durable relational dataset -> relational.
Full-text search -> OpenSearch.
Embedded storage engine -> RocksDB.

Source / grounding

https://redis.io/docs/latest/develop/data-types/

Common Mistakes

Choosing Redis solely because low latency sounds desirable.

Treating a cache as the authoritative source of payment, inventory, balance, or booking state.

Failing to define TTL and invalidation behavior.

Ignoring cache-miss and Redis-failure behavior.

Choosing a Redis data structure based on convenience rather than access pattern.

Ignoring hot keys, memory pressure, or eviction behavior.

Assuming Redis Cluster automatically solves all scaling and availability concerns.