# Database Selection Rules and Anti-Patterns


## Rules
1. Start with the workload, not technology popularity.
2. Choose the primary data model first.
3. Identify the strongest business invariants.
4. Design around important queries.
5. Prefer one database when one is sufficient.
6. Add Redis only for a concrete cache/ephemeral requirement.
7. Add OpenSearch only for a concrete search requirement.
8. Add Neo4j only when traversal is central.
9. Treat RocksDB as infrastructure/embedded storage, not default application storage.
10. Consider sharding only after simpler scaling mechanisms are inadequate.

## Anti-patterns
- "Modern system = microservices + 4 databases."
- "10 million users = sharding."
- "Search box = OpenSearch."
- "Relationships = graph DB."
- "Flexible schema = MongoDB."
- "Fast = Redis as source of truth."
- "Every table needs an index on every foreign key and filter."
- "Every entity needs soft delete."

The Review Agent should actively flag these patterns.


## Source / grounding
Curated project decision rules.
