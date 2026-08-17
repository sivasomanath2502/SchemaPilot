# Database Trade-off Matrix


| Technology | Dominant model | Strongest use | Primary concern |
|---|---|---|---|
| MySQL | Relational | OLTP/transactions | complex scale requires careful architecture |
| PostgreSQL | Relational | complex SQL/relational | operational/advanced feature complexity |
| MongoDB | Document | flexible/nested documents | relational joins/integrity may be less natural |
| Redis | Key/data structures | cache/low latency | memory and source-of-truth semantics |
| RocksDB | Embedded KV | storage engine | not a general application DB |
| Neo4j | Graph | relationship traversal | unnecessary for ordinary CRUD |
| OpenSearch | Search | full-text/relevance | not primary transactional truth |

Use this matrix for first-pass retrieval. Final selection must combine it with user requirements.


## Source / grounding
Curated decision matrix.
