Neo4j — Full Selection Profile

Role

Graph database using nodes, relationships and properties.

Core Selection Summary

Definition: Neo4j is a graph database that represents data as nodes, relationships, and properties.

Why it exists: It is designed for workloads where the important questions are about relationships, paths, and traversal rather than primarily tabular aggregation or document retrieval.

When to use: Prefer Neo4j when variable-depth traversal and relationship discovery are dominant workloads, such as recommendation paths, fraud rings, dependency traversal, knowledge graphs, or network analysis.

When NOT to use: Do not select a graph database merely because the domain contains relationships. Ordinary relationships, CRUD, orders, payments, inventory, and reporting can often be handled effectively by relational databases.

Primary selection rule: The deciding signal is the dominant query workload: variable-depth traversal and relationship discovery must be central enough to justify a graph model.

Advantages: Natural representation of relationships and traversal-oriented workloads.

Disadvantages: A graph database is a poor fit when the dominant workload is ordinary relational CRUD, transactional business processing, dedicated search, or key-value caching.

Review questions:

Are the dominant queries relationship-centric?

Do they require variable-depth traversal?

Could ordinary relational queries satisfy the workload?

Is graph traversal a core requirement or merely present in the data?

Are transactional order/payment/inventory semantics actually the dominant requirement?

Strong selection signals

The important questions are relationship-centric:

friends of friends

recommendation paths

fraud rings

dependency traversal

knowledge graphs

network analysis

Key distinction

Having relationships does not imply a graph database. Relational systems handle ordinary relationships very well.

The deciding signal is whether variable-depth traversal and relationship discovery are dominant workloads.

Graph Selection Boundary

Variable-depth traversal is a strong selection signal when it is a dominant workload that the application repeatedly needs to answer.

The mere existence of nodes connected by relationships is not sufficient to justify Neo4j.

If the required queries are ordinary direct relationships, CRUD, joins, aggregation, or transactional business operations, a relational database may remain the better fit.

Modeling

Start from important graph questions. Identify nodes, relationship types, relationship properties and traversal patterns.

Modeling Boundary

Graph modeling should begin from the traversal questions the application must answer.

Defining nodes and relationships without identifying the actual traversal patterns is not sufficient to justify a graph-oriented architecture.

The model should reflect the relationship paths and discovery operations that are central to the workload.

Weak-fit signals

Simple CRUD, orders, payments, inventory and ordinary reporting -> MySQL/PostgreSQL.
Dedicated search -> OpenSearch.
Key-value caching -> Redis.

Source / grounding

https://neo4j.com/docs/getting-started/graph-database/

Common Mistakes

Choosing Neo4j simply because the domain contains relationships.

Treating every many-to-many relationship as evidence for a graph database.

Choosing Neo4j without identifying the variable-depth traversal queries it must serve.

Using a graph database for ordinary orders, payments, inventory, or CRUD when relational systems fit the workload.

Confusing graph-shaped data with a graph-dominant query workload.