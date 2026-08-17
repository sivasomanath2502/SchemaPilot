# OpenSearch — Full Selection Profile


## Role
Distributed search and analytics engine for full-text search, relevance, filtering, faceting and search-oriented analytics.

## Strong selection signals
- Full-text search
- Relevance ranking
- Fuzzy matching
- Autocomplete
- Faceting/filtering
- Large-scale document search
- Logs and search analytics

## Architecture role
Usually a derived search projection:
Primary database -> indexing pipeline -> OpenSearch.

The design should specify indexing latency, failure recovery, rebuild strategy and acceptable staleness.

## Source of truth
Do not use a search index as the authoritative payment, booking or inventory store merely because it can store those documents.

## Weak-fit signals
Exact indexed lookup -> normal database index may be enough.
Transactional OLTP -> MySQL/PostgreSQL.
Cache/session -> Redis.
Embedded KV -> RocksDB.


## Source / grounding
https://docs.opensearch.org/latest/
