# Reliability and Failure Handling


## Reliability questions
For each architecture identify:
- single points of failure
- backup requirements
- restore process
- replication/failover
- cache failure
- search-index failure
- partial network failure

## Supporting system failure
If Redis fails, the application should define whether it falls back to the primary DB.
If OpenSearch fails, transactional operations should normally remain possible if search is non-critical.
If asynchronous indexing fails, records should be retried/rebuilt.

## Review rule
A design is incomplete if it only describes the happy path.


## Source / grounding
Curated reliability architecture knowledge.
