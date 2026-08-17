# Query-Aware Schema Design


## Principle
Schema, indexes and query patterns should be designed together.

## Query analysis
For each important query identify:
- filters
- joins
- sorting
- grouping
- expected cardinality
- frequency
- latency requirement

## Example
User order history:
WHERE user_id = ?
ORDER BY created_at DESC

This naturally motivates investigation of a composite index aligned to user_id and created_at.

## Escalation order
First optimize query/schema/indexes. Then consider caching or read models. Only then consider specialized databases.

## Review rule
Every non-trivial index, denormalization or supporting database should have a workload/query justification.


## Source / grounding
Curated query-aware database design knowledge.
