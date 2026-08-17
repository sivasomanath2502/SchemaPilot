# Sharding — Deep Explanation

## Definition
Sharding is horizontal distribution of one logical dataset across multiple database nodes. Each shard owns a subset of records. A router, application layer, or database-native mechanism determines which shard should handle a request.

## Why sharding exists
A single database node has finite CPU, memory, storage, I/O and network capacity. Sharding can increase aggregate capacity when one node remains the bottleneck after schema optimization, query tuning, indexes, vertical scaling, caching, replication and other simpler techniques.

## Example
Suppose a users table has 2 billion records and one database cannot sustain the required workload. A sharded design might place different users on different nodes:

- Shard A: users whose shard key maps to A
- Shard B: users whose shard key maps to B
- Shard C: users whose shard key maps to C

The application must know how to route a user request to the correct shard.

## Shard key
The shard key determines placement. A good key should have high enough cardinality, distribute data and traffic evenly, avoid hotspots, and support important queries.

## Hash sharding
A hash of the shard key determines the shard.

Advantages:
- generally good distribution
- reduces sequential-range hotspots

Disadvantages:
- range queries may touch many shards
- changing distribution can require data movement depending on implementation

## Range sharding
A key range maps to a shard.

Example:
- IDs 1–1,000,000 -> A
- IDs 1,000,001–2,000,000 -> B

Advantages:
- range queries can target a subset of shards
- useful for ordered data

Risk:
If new writes concentrate in the newest range, one shard can become a hotspot.

## Geographic sharding
Data is placed according to region. It can reduce latency and help with residency requirements, but creates cross-region query and uneven-load concerns.

## Tenant sharding
A tenant/customer determines placement. This can keep tenant-local queries on one shard, but a very large tenant can become a hotspot.

## Cross-shard query
A query that needs records from multiple shards may require fan-out, parallel execution and result merging. This increases network traffic and latency.

## Cross-shard transaction
A transaction that modifies multiple shards is more difficult than a single-shard transaction. Good domain boundaries and shard keys try to keep critical transactions local.

## Hotspot
A hotspot occurs when a disproportionate amount of traffic or data goes to one shard. A shard key can have excellent total distribution and still be bad for traffic distribution.

## Rebalancing
As data grows, shards may become uneven. Rebalancing moves data between nodes and can consume significant network, disk and CPU resources.

## Operational complexity
Sharding adds routing, monitoring, backup, restore, schema migration, rebalancing and failure-handling complexity.

## When NOT to shard
Do not shard merely because:
- the application has many registered users
- the database is considered old-fashioned
- a presentation wants to show advanced architecture

First determine the actual bottleneck.

## Decision sequence
1. Correct schema.
2. Query optimization.
3. Correct indexes.
4. Vertical scaling.
5. Caching where justified.
6. Read replicas where justified.
7. Partitioning where appropriate.
8. Sharding only when simpler techniques cannot satisfy capacity requirements.

## Review questions
- What exact resource is exhausted?
- What is the shard key?
- How evenly will data and traffic distribute?
- Which queries become cross-shard?
- Can critical transactions remain within one shard?
- How is a hot tenant/key handled?
- How is rebalancing performed?
- How are backups and restores performed?
