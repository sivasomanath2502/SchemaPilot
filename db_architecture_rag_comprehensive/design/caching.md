# Caching Strategy


## When caching helps
Caching is useful when:
- reads repeat
- source data changes less frequently than it is read
- latency matters
- database load is a bottleneck

## Common patterns
Cache-aside:
1. read cache
2. on miss read DB
3. populate cache
4. return

Write-through or write-behind may be appropriate in specific architectures but introduce consistency trade-offs.

## Required decisions
- cache key
- TTL
- invalidation
- stale-data policy
- cache failure behavior
- memory/eviction policy

## Review rule
Never introduce Redis without identifying the exact hot read/state workload it solves.


## Source / grounding
https://redis.io/docs/latest/develop/
