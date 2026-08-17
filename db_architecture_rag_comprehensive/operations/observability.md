# Database Observability


## What to monitor
- query latency
- slow queries
- CPU
- memory
- disk
- connections
- lock contention
- replication lag
- cache hit/miss
- search indexing lag
- error rate

## Agent relevance
The Review Agent should prefer recommendations that can be measured.

Example:
"Add Redis" should ideally be tied to a measurable read bottleneck or latency requirement.

"Add an index" should be tied to a query plan or high-frequency access path.


## Source / grounding
Curated database observability knowledge.
