# Neo4j — Full Selection Profile


## Role
Graph database using nodes, relationships and properties.

## Strong selection signals
The important questions are relationship-centric:
- friends of friends
- recommendation paths
- fraud rings
- dependency traversal
- knowledge graphs
- network analysis

## Key distinction
Having relationships does not imply a graph database. Relational systems handle ordinary relationships very well.

The deciding signal is whether variable-depth traversal and relationship discovery are dominant workloads.

## Modeling
Start from important graph questions. Identify nodes, relationship types, relationship properties and traversal patterns.

## Weak-fit signals
Simple CRUD, orders, payments, inventory and ordinary reporting -> MySQL/PostgreSQL.
Dedicated search -> OpenSearch.
Key-value caching -> Redis.


## Source / grounding
https://neo4j.com/docs/getting-started/graph-database/
