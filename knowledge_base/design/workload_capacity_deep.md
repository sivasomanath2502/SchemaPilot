# Workload and Capacity Planning — Deep Explanation

## User count is not traffic
Registered users, daily/monthly active users, concurrently-online users, and requests per second are all different quantities, and conflating them leads to wrong capacity assumptions. "10 million registered users" says very little on its own about database load.

## Important dimensions to establish
- total registered users
- daily/monthly active users
- concurrently active users
- average requests per second (RPS)
- peak RPS
- read/write ratio
- current data size
- expected data growth rate
- latency target
- availability target

## Example capacity calculation
If 1,000,000 active users each generate roughly 10 requests per minute:
```
1,000,000 × 10 / 60 ≈ 166,667 requests/sec average
```
This is only a rough estimate — real traffic depends heavily on actual user behavior and request distribution, and should be treated as a starting assumption to state explicitly, not a precise prediction.

## Important caveat — HTTP requests are not database operations
One API call may execute multiple database queries, a cached response with zero queries, or a single query — there's no fixed ratio. Any workload estimate should distinguish "application-level traffic" from "actual database operations," and state which one a given number refers to.

## Read vs write workload
**Read-heavy workload** — retrieval dominates. Caching (`caching.md`), read replicas (`replication_deep.md`), query/index optimization (`indexing_deep.md`), and search projections (`search_architecture.md`) are the typical levers.

**Write-heavy workload** — inserts/updates dominate. Index maintenance cost, transaction duration, lock contention, storage write throughput, and replication overhead (replicating every write) become the important constraints.

A 90:10 read/write ratio means approximately 90% reads and 10% writes of the relevant operations. This split should inform which optimization levers are actually worth prioritizing.

## Hot data and hotspots
A small portion of records can receive a disproportionate share of traffic (a viral post, a popular event's seats). Hotspots can make caching strategy or data-distribution design more important than the raw total dataset size — a system correctly sized for average load can still buckle under a concentrated hot key. See "hot keys" in `caching.md` and "hotspot" in `sharding_deep.md` for concrete mitigation approaches.

## Peak traffic
Ticket releases, flash sales, promotions, and batch jobs can create short traffic spikes far larger than average load. Any capacity plan should state the peak assumption explicitly and design for it — average-load sizing alone is a common and costly underestimate.

## Data growth estimation
A rough estimate:
```
records/day × average row/document size × retention period
```
Then account for indexes (which add their own storage), replicas (each a full additional copy), audit/history data (see `temporal_audit_data.md`), and backups.

## Capacity dimensions to check
- CPU
- RAM
- storage (and its growth rate)
- IOPS (storage input/output operations per second)
- network bandwidth
- database connection limits
- lock contention under concurrent load
- query latency under realistic (not just average) load

## Design principle
"10 million users" is not, by itself, evidence for sharding, read replicas, or any specific architectural decision. The agent (and the reviewer) should translate a business-scale statement into concrete workload assumptions — RPS, read/write ratio, data growth, peak multiplier — *before* making architecture decisions based on it.

## Common mistakes
- Treating registered user count as if it directly implies request rate.
- Sizing only for average load and ignoring realistic peak multipliers.
- Confusing HTTP request rate with database operation rate.
- Recommending sharding/read replicas/caching from a vague "it's a big app" impression rather than a stated workload estimate.
- Ignoring hotspot risk because aggregate numbers look manageable.

## Review questions
- What specific numbers (RPS, read/write ratio, data growth, peak multiplier) support this architecture decision?
- Is this an application-traffic number or a database-operation number?
- What is the assumed peak-to-average ratio, and is it realistic for this domain?
- Could a small number of hot records dominate load in a way the average numbers hide?
