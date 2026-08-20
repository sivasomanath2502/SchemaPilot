Caching Strategy — Deep Explanation

Core Reasoning Summary

Definition: A cache stores a copy of data that is expensive or slow to recompute or refetch, using a faster-access layer to reduce latency and source-database load.

Why it exists: Caching trades storage and consistency complexity for lower read latency and reduced load on the source system.

When to use: Use caching when reads repeat, source data changes less frequently than it is read, latency matters, and measured source-database read load is a meaningful bottleneck.

When NOT to use: Do not introduce a cache when the workload is not sufficiently repeat-heavy, when stale data is unacceptable and cannot be safely controlled, or before the actual hot read path has been identified.

Primary rule: A cache is a performance/derived-state mechanism. It does not automatically become the source of truth, and cache correctness depends on explicit freshness, invalidation, failure, and rebuild behavior.

Advantages: Lower read latency and reduced source-database load.

Disadvantages: Adds invalidation, staleness, failure, memory, eviction, stampede, and hot-key complexity.

Review questions:

What exact hot workload does the cache solve?

What staleness is acceptable?

What is the invalidation strategy?

What happens when the cache fails?

What prevents a cache stampede?

What prevents hot-key overload?

Is the cache authoritative or derived?

A cache stores a copy of data that is expensive or slow to recompute/refetch, in a faster-access layer (typically in-memory, e.g. Redis), trading storage/consistency complexity for latency and reduced load on the source database.

When caching helps

Reads repeat (the same or similar data is requested frequently).

Source data changes less frequently than it is read (low write-to-read ratio on that data).

Latency matters for the read path.

The database is a bottleneck under read load that caching can absorb.

Caching does NOT help, and can actively hurt, when data changes on nearly every read (cache hit rate will be low, adding complexity for little benefit) or when strict real-time correctness is required and staleness is unacceptable.

Common patterns

Cache-aside (lazy loading) — the most common pattern:

Read cache.

On miss, read the database.

Populate the cache with the result.

Return the result.

Write-through — writes go to the cache and the database together, keeping the cache always current at write time, at the cost of added write latency.

Write-behind (write-back) — writes go to the cache first and are asynchronously flushed to the database, reducing write latency but introducing a window where the cache and database can diverge, and risk of data loss if the cache fails before flushing.

Cache invalidation

This is the hardest part of caching in practice ("there are only two hard things in computer science: cache invalidation and naming things"). Strategies:

Invalidation Boundary

TTL, explicit invalidation, and event-driven invalidation are mechanisms for controlling cache freshness; none of them automatically guarantees zero staleness.

If strict freshness is required, the architecture must ensure that the chosen cache strategy cannot expose an unacceptable stale value, or the critical read must bypass the cache.

TTL (time-to-live) — the simplest approach; entries expire automatically after a fixed duration. Simple but can serve stale data until expiry, or cause a wave of re-fetches if many keys share the same TTL and expire together.

Explicit invalidation on write — when the source data changes, the application actively deletes or updates the corresponding cache key. More accurate, but requires every write path to remember to invalidate correctly — a common source of subtle bugs if any write path is missed.

Event-driven invalidation — a change-data-capture or message-queue mechanism triggers invalidation, decoupling the write path from remembering to invalidate directly.

Cache stampede (thundering herd)

Stampede Boundary

Stampede mitigation reduces concurrent duplicate recomputation after cache misses. It does not eliminate cache invalidation, staleness, or source-database failure concerns.
When a popular cache key expires, many concurrent requests can all miss the cache simultaneously and hit the database at once, causing a sudden load spike — potentially bad enough to overload the database right when the cache was supposed to protect it.

Mitigations:

Locking/single-flight — only one request recomputes the value on a miss; concurrent requests wait for that result instead of all hitting the database independently.

Early/probabilistic expiration — refresh a value slightly before it actually expires, staggered per key, to avoid many keys expiring at the same instant.

Stale-while-revalidate — serve the stale value immediately while asynchronously refreshing it in the background.

Hot keys

A small number of keys (e.g. a viral post, a popular event) can receive disproportionate traffic. This can overload a single cache node/shard even if overall cache capacity is sufficient, because the load isn't evenly distributed.

Mitigations:

Replicate especially hot keys across multiple cache nodes.

Add a short local (in-process) cache layer in front of the shared cache for extremely hot keys.

Monitor for hot-key patterns explicitly, since average metrics can hide them.

Required design decisions

Failure Boundary

A cache failure policy must be chosen from the application's correctness and capacity requirements.

Falling back to the database is sufficient only if the database can safely absorb the additional load and the resulting behavior remains acceptable.

If it cannot, the architecture must define a degraded or failed response rather than assuming fallback is always safe.

Cache key design (must be unique and deterministic for the same logical data)

TTL value, and whether it varies by data type

Invalidation strategy (TTL-only, explicit, event-driven, or a mix)

Stale-data policy (is serving slightly stale data acceptable for this use case?)

Cache failure behavior (does the application degrade to hitting the database directly, or fail?)

Memory/eviction policy (e.g. LRU) when the cache is full

When NOT to introduce a cache

The workload isn't actually read-heavy or repeat-heavy enough to benefit.

The data must always be perfectly fresh (e.g. real-time account balance mid-transaction) and no staleness at all is acceptable.

The performance problem hasn't been diagnosed yet — adding Redis reflexively without identifying the exact hot read path it solves is a common mistake.

Common mistakes

Introducing Redis "because it's standard" without identifying a specific hot workload.

No defined invalidation strategy, leading to silently stale data.

No defined behavior for cache failure, so a Redis outage takes down the whole read path instead of degrading gracefully.

Ignoring cache stampede risk for popular keys with a shared TTL.

Treating the cache as a source of truth rather than a derived, disposable copy.

Review rule

Never introduce a cache without identifying the exact hot read/state workload it solves, its invalidation strategy, and its failure-mode behavior.

Source / grounding

https://redis.io/docs/latest/develop/

Common Review Mistakes

Treating caching as automatically beneficial without identifying the hot read path.

Treating TTL as a guarantee of freshness.

Treating write-through as an atomic cache/database transaction without explicit coordination.

Using write-behind for correctness-sensitive state without accepting its durability window.

Assuming cache failure can always fall back safely to the database.

Solving cache stampede while ignoring hot keys or stale-data semantics.

Treating a cache as authoritative simply because it is faster.