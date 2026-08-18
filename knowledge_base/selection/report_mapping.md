# 23-Section Report Mapping

## Required report
1. Requirements / scope
2. Scale
3. Features & roles
4. Read vs write
5. Concurrency
6. Entities
7. Relationships/cardinality
8. Schema
9. SQL vs NoSQL + trade-offs
10. Important queries
11. Indexes
12. Cache
13. Replication
14. Search
15. Partitioning
16. Sharding
17. Pagination
18. Transactions
19. Failure handling
20. Idempotency
21. Consistency
22. Final architecture
23. Trade-offs

## Knowledge mapping
1 -> Requirement Agent + user input
2 -> workload_capacity_deep
3 -> roles_and_access + Requirement Agent
4 -> read_write_workload + workload_capacity_deep
5 -> transactions_concurrency_deep + isolation_levels
6 -> schema_deep
7 -> schema_deep
8 -> schema_deep + constraints
9 -> sql_vs_nosql_deep + database profiles
10 -> query_design
11 -> indexing_deep
12 -> caching
13 -> replication_deep
14 -> search
15 -> partitioning
16 -> sharding_deep
17 -> pagination_deep
18 -> transactions_concurrency_deep
19 -> failure_handling_deep
20 -> idempotency_deep
21 -> consistency_deep
22 -> synthesized agent state
23 -> tradeoffs + anti-patterns

The report generator should synthesize these topics from the current application rather than copy generic paragraphs into every report.
