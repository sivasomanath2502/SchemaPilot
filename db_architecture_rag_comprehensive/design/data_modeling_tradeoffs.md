# Data Model Trade-offs


Relational:
- strong relationships
- transactions
- joins
- integrity

Document:
- nested aggregates
- flexible shape
- document-oriented access

Key-value:
- key-based access
- simple/fast operations
- specialized state

Graph:
- relationship traversal
- graph algorithms
- connection-centric queries

Search:
- full-text/relevance
- inverted-index access

Embedded KV:
- application-owned storage engine

## Rule
Choose based on dominant access patterns and business invariants, not "SQL vs NoSQL" ideology.


## Source / grounding
Curated database modeling knowledge.
