# Read vs Write Workload — Deep Explanation

## Read-heavy workload
A workload where retrieval dominates. Caching, read replicas, query/index optimization and search projections may help.

## Write-heavy workload
A workload where inserts/updates dominate. Index maintenance, transaction duration, lock contention, storage throughput and replication overhead become important.

## Example
10,000 requests/sec with an 80:20 split means approximately 8,000 reads/sec and 2,000 writes/sec, assuming the requests map directly to database operations.

## Important caveat
HTTP requests are not necessarily database operations. One API call may execute multiple queries or no database query at all.

## Hot data
A small portion of records may receive most traffic. Hotspots can make caching or data-distribution strategy more important than total dataset size.

## Design rule
The agent should state assumptions and distinguish application traffic from actual database operations.
