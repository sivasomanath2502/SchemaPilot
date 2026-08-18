# SQL vs NoSQL — Deep Explanation

## Quick reference — data model trade-offs
| Model | Strengths | Typical fit |
|---|---|---|
| **Relational (SQL)** | Strong relationships, transactions, joins, referential integrity | Central entities with clear relationships, transactional consistency needs |
| **Document** | Nested aggregates, flexible/evolving shape | Bounded aggregates read/written as a unit, schema that varies or evolves |
| **Key-value** | Fast key-based access, simple operations | Caching, session state, specialized simple lookups |
| **Graph** | Relationship traversal, graph algorithms | Connection-centric queries (social graphs, recommendations, fraud rings) |
| **Search (inverted index)** | Full-text relevance, fuzzy matching | Search-centric access patterns, not general transactional storage |
| **Embedded key-value** | Application-owned storage engine, no server process | Building a custom storage layer, not a typical application-facing choice |

The decision rule below explains *why* — this table is a summary, not a substitute for reasoning about the actual workload.

## SQL definition
Relational SQL databases organize data into tables with defined schemas, and provide joins, constraints, transactions, and declarative querying (SQL) across related tables.

## NoSQL definition
"NoSQL" is a broad family, not one database model — it includes document, key-value, graph, and wide-column systems. Search engines are also specialized non-relational systems, sometimes grouped loosely under the same umbrella. Treating "NoSQL" as a single alternative to compare against SQL is itself a category error — each NoSQL type has a different shape and different strengths.

## Relational strengths — use when
- Relationships between entities are central to the domain.
- Transactions need to span multiple entities atomically.
- Referential integrity matters (foreign keys enforcing valid references).
- SQL joins and aggregations are a natural fit for the required queries.
- Business rules benefit from database-level constraints (see `schema_constraints.md`).

## Document strengths — use when
The application naturally reads and writes bounded aggregates as a unit (e.g. a user profile with embedded preferences), and the schema shape varies between records or evolves frequently without needing a migration each time.

## Key-value strengths — use when
Access is purely by key, workload needs very fast simple operations, and the use case is inherently specialized (caching, session state, rate limiting) rather than general application data.

## Graph strengths — use when
Relationship *traversal* is the dominant query pattern — not just "does a relationship exist" but "find paths/connections through many relationships" (recommendation engines, fraud-ring detection, social graphs).

## Search strengths — use when
Full-text analysis and relevance ranking are central to the feature, not just exact-match lookups (see `search_architecture.md` for how this typically pairs with, rather than replaces, a primary database).

## Hybrid architecture (polyglot persistence)
A system can combine technologies when each has a clearly distinct, justified role:
```
MySQL      -> transaction truth (source of truth)
Redis      -> cache (derived, disposable)
OpenSearch -> search projection (derived, disposable)
```
This works well when the source-of-truth boundary is clear (see `consistency_deep.md`) — it breaks down when multiple systems each believe they own the same fact.

## Complexity cost
Every additional database technology adds deployment, monitoring, synchronization, backup, and failure-handling responsibility. This cost is real and should be weighed explicitly against the specific capability gained — adding a second or third database "because it's a common modern stack" without a distinct justified role is a real cost with no matching benefit.

## Decision rule
Don't ask "SQL or NoSQL?" as a single binary choice in isolation. Ask, for the actual workload:
- What is the dominant data model (relational, document-shaped, key-value, graph, search)?
- What consistency model does the critical invariant require?
- What is the dominant access pattern?
- Does the added operational complexity of a second/third technology have a specific, justified role?

## Common mistakes
- Choosing a database technology by popularity/trend rather than by matching data model and access pattern.
- Adding a NoSQL component "for scale" without a workload number that actually justifies it (see `workload_capacity_deep.md`).
- Losing referential integrity by moving relational data into a document store without a compensating strategy.
- Running multiple databases with no clear, single source of truth for shared facts.

## Review questions
- What is the dominant data model this application actually needs?
- Does any specific requirement justify a technology beyond the primary relational/document store?
- Is there a single, clear source of truth for every important fact, even across multiple technologies?
- Does the operational cost of an additional database component have a specific, named justification?

## Source / grounding
Curated database modeling knowledge.
