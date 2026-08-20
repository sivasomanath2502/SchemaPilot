Database Selection Signals

Purpose

This document provides RAG-safe database selection signals for the Database Selection Agent.

It is a candidate-selection guide, not an automatic database-selection table. A signal narrows the candidate set; it does not by itself determine the final database.

Final selection must also evaluate:

business invariants

query patterns

read/write workload

concurrency

data size and growth

latency requirements

availability requirements

operational constraints

failure and recovery requirements

team skills and cost

The agent should prefer the simplest architecture that satisfies the actual requirements.

MySQL

Definition

MySQL is a relational SQL database and a strong default candidate for transactional application systems.

Strong Selection Signals

Prefer MySQL when the workload is dominated by:

structured relational entities

transactional OLTP

foreign-key and relational integrity

multi-row transactional invariants

SQL joins and aggregations

predictable CRUD workloads

Why It Fits

MySQL provides transactions, constraints, joins, indexes, and a mature relational model. It is a strong candidate when correctness-sensitive business operations naturally map to relational transactions.

Do Not Select MySQL Solely Because

the team is already familiar with it

the data is structured

the application has many users

it is a common default

Familiarity is an operational consideration, not sufficient technical evidence by itself.

Consider Alternatives When

document-shaped access patterns dominate → evaluate MongoDB

complex SQL, rich data types, recursive queries, or useful PostgreSQL-specific extensions are important → evaluate PostgreSQL

variable-depth relationship traversal dominates → evaluate Neo4j

full-text relevance is central → evaluate OpenSearch

low-latency cache or ephemeral key-oriented access dominates → evaluate Redis

embedded local KV storage is required → evaluate RocksDB

Important Boundary

MySQL being a strong relational default does not mean it is automatically the winner. The final choice must be based on the workload and requirements.

PostgreSQL

Definition

PostgreSQL is an advanced relational SQL database with strong transactional semantics, constraints, indexes, rich data types, and extensibility.

Strong Selection Signals

Prefer PostgreSQL when the workload materially benefits from:

complex relational SQL

CTEs and window functions

recursive queries

rich data types

multiple index types

PostgreSQL-specific extensions

specialized relational or analytical capabilities

Why It Fits

PostgreSQL is a strong candidate when the application needs relational integrity together with capabilities that materially benefit from PostgreSQL's richer SQL, data types, or extension ecosystem.

Do Not Select PostgreSQL Solely Because

it has more features than another relational database

it supports JSON

it is considered more advanced

it has a large feature set that the workload does not actually need

Consider Alternatives When

ordinary relational OLTP satisfies the workload without a PostgreSQL-specific requirement → compare MySQL as a strong alternative

document boundaries and document-oriented access dominate → evaluate MongoDB

variable-depth traversal dominates → evaluate Neo4j

dedicated search/relevance dominates → evaluate OpenSearch

cache/ephemeral key-oriented access dominates → evaluate Redis

embedded local KV storage is required → evaluate RocksDB

Important Boundary

Do not treat PostgreSQL as universally better than MySQL. A PostgreSQL capability is a strong selection signal only when the workload actually requires or materially benefits from it.

MongoDB

Definition

MongoDB is a document-oriented database in which application data is represented as BSON documents organized in collections.

Strong Selection Signals

Prefer MongoDB when the workload benefits from:

document-shaped aggregates

bounded nested data

related data that is commonly read together

variable document attributes

frequent schema evolution

document-oriented access patterns

horizontal scaling compatible with the chosen shard-key strategy

Why It Fits

MongoDB is a strong fit when the application's natural data boundaries are document-shaped and the access pattern maps cleanly to those boundaries.

Embedding is useful when related data is bounded and commonly accessed together. References are useful when data is shared, independently updated, or unbounded.

Do Not Select MongoDB Solely Because

the API uses JSON

the data has flexible fields

the schema changes frequently

the application does not have a fixed relational schema

Flexible schema alone is not sufficient evidence.

Consider Alternatives When

strong relational joins and referential integrity dominate → evaluate MySQL/PostgreSQL

variable-depth relationship traversal dominates → evaluate Neo4j

dedicated full-text/relevance search dominates → evaluate OpenSearch

low-latency cache or ephemeral state dominates → evaluate Redis

embedded local KV storage is the actual requirement → evaluate RocksDB

Important Boundaries

A document-shaped model is a selection signal, not an automatic selection.

A single-document write provides document-level atomicity when the required state is correctly modeled inside that document. It does not automatically solve invariants that span multiple documents or independently owned entities.

A unique key or index protects the constraint it represents; it does not automatically establish unrelated business invariants.

Sharding is not required merely because MongoDB supports it. If sharding is needed, cardinality, distribution, hotspot risk, and query routing must be evaluated.

Redis

Definition

Redis is an in-memory data structure store used for low-latency key-oriented workloads, caching, and ephemeral or derived state.

Strong Selection Signals

Prefer Redis for:

cache

session storage

rate limiting

counters

leaderboards

queues/streams

low-latency key access

ephemeral or derived state

workloads that naturally fit Redis data structures

Why It Fits

Redis is optimized for fast key-oriented operations and provides data structures such as strings, hashes, lists, sets, sorted sets, and streams.

The data structure should be selected from the access pattern rather than convenience.

Do Not Select Redis Solely Because

it is fast

traffic is high

the application needs caching somewhere

any application data can technically be represented as a key/value pair

Consider Alternatives When

durable relational transactions and integrity dominate → evaluate MySQL/PostgreSQL

document-oriented modeling dominates → evaluate MongoDB

variable-depth relationship traversal dominates → evaluate Neo4j

dedicated search/relevance dominates → evaluate OpenSearch

embedded local persistent KV storage is required → evaluate RocksDB

Critical Boundaries

Redis is sufficient as a cache when the cached data can tolerate the defined staleness and the system has correct cache-miss and Redis-failure behavior.

Redis is not automatically sufficient as the authoritative store for payments, inventory ownership, account balances, or bookings merely because it is fast.

For correctness-sensitive state, the authoritative durable system must establish the required transactional correctness when such a requirement exists.

TTL, invalidation, memory pressure, eviction behavior, hot keys, persistence, replication, and failure recovery must be evaluated according to the workload.

RocksDB

Definition

RocksDB is an embedded persistent key-value storage library, not a typical client/server application database.

Strong Selection Signals

Prefer RocksDB when the requirement explicitly includes:

embedded local persistence

persistent key-value storage

point lookups

ordered/range scans

storage-engine or infrastructure workloads

Why It Fits

RocksDB provides local persistent key-value storage for applications or infrastructure components that need an embedded storage engine.

Do Not Select RocksDB Solely Because

key/value access is required

it provides fast local storage

the application can technically encode its data as keys and values

Consider Alternatives When

ordinary web CRUD is required → evaluate MySQL/PostgreSQL or MongoDB according to the data model

SQL joins and relational integrity are central → evaluate MySQL/PostgreSQL

variable-depth relationship traversal is central → evaluate Neo4j

dedicated search/relevance is central → evaluate OpenSearch

cache/session/ephemeral key access is the requirement → evaluate Redis

Critical Boundary

The embedded deployment model must itself be a meaningful requirement.

RocksDB is not a complete client/server database. Networking, multi-process service access, replication, distributed consistency, richer query semantics, and secondary indexing must be provided by the surrounding architecture when required.

Do not infer that RocksDB provides those higher-level database capabilities merely because it provides durable key-value storage.

Neo4j

Definition

Neo4j is a graph database that represents data as nodes, relationships, and properties.

Strong Selection Signals

Prefer Neo4j when the dominant workload requires:

variable-depth traversal

relationship discovery

path queries

graph-centric recommendations

fraud-ring or network analysis

dependency traversal

knowledge-graph style exploration

Why It Fits

Neo4j is designed for workloads where relationships and paths are central to the questions the application must answer.

Do Not Select Neo4j Solely Because

the domain contains relationships

the schema contains many-to-many relationships

entities are connected to other entities

the application has a graph-shaped conceptual model

Every relational application has relationships.

Consider Alternatives When

ordinary CRUD and direct relationships dominate → evaluate MySQL/PostgreSQL

document-oriented aggregates dominate → evaluate MongoDB

dedicated full-text/relevance dominates → evaluate OpenSearch

cache or low-latency key access dominates → evaluate Redis

embedded local KV storage is required → evaluate RocksDB

Critical Boundary

The existence of relationships is not sufficient to select a graph database.

The decisive signal is whether variable-depth traversal and relationship discovery are central workloads that materially benefit from a graph model.

If ordinary relational queries satisfy the required workload, a graph database may add unnecessary complexity.

OpenSearch

Definition

OpenSearch is a distributed search and analytics engine for full-text search, relevance, filtering, faceting, and search-oriented analytics.

Strong Selection Signals

Prefer OpenSearch when the workload requires:

full-text search

relevance ranking

fuzzy matching

autocomplete

faceting

search-oriented analytics

dedicated search retrieval behavior

Why It Fits

OpenSearch is specialized for search workloads where ordinary database indexes are not enough for the required relevance or retrieval behavior.

Do Not Select OpenSearch Solely Because

the application has a search box

text fields exist

filtering is required

documents can be indexed

Exact indexed lookup may already be satisfied by the primary database.

Consider Alternatives When

ordinary exact lookup is sufficient → evaluate indexes in MySQL/PostgreSQL/MongoDB as appropriate

transactional OLTP is dominant → evaluate MySQL/PostgreSQL

document-oriented persistence is dominant → evaluate MongoDB

cache/session/ephemeral access dominates → evaluate Redis

embedded local KV storage is required → evaluate RocksDB

variable-depth traversal is dominant → evaluate Neo4j

Critical Boundaries

OpenSearch is sufficient for a search workload when the required search capabilities justify a dedicated search projection and the defined indexing latency/staleness is acceptable.

It is not required for ordinary exact lookup when the primary database can satisfy the query adequately.

When OpenSearch is used as a derived projection, indexing failure or staleness must not corrupt authoritative transactional data.

A search index containing payment, booking, or inventory documents does not automatically become the source of truth for those transactional states.

Cross-Database Selection Rules

Rule 1 — Start With the Workload

Do not select a database from technology popularity, familiarity, or a single feature.

Identify:

dominant data model

business invariants

important queries

read/write ratio

requests per second

concurrency

data size

growth

latency

availability

operational constraints

Rule 2 — Data Model Is a Candidate Signal

Use the dominant data model to narrow candidates:

structured relational → MySQL/PostgreSQL

document-shaped → MongoDB

cache/key-oriented → Redis

embedded persistent KV → RocksDB

relationship-centric traversal → Neo4j

full-text/relevance → OpenSearch

These mappings are not automatic selections.

Rule 3 — Business Invariants Come Before Optimization

Identify operations that cannot tolerate inconsistency.

The database must provide, or be part of an architecture that provides, the required correctness mechanism.

A performance feature such as a cache, search index, replica, or secondary index must not be mistaken for the mechanism that establishes an unrelated business invariant.

Rule 4 — Supporting Databases Need Distinct Requirements

Add a supporting database only when it addresses a distinct workload or capability that the primary database does not adequately satisfy.

Examples:

Redis for a concrete cache/ephemeral/low-latency requirement

OpenSearch for a concrete search/relevance requirement

Neo4j for central variable-depth traversal

RocksDB for an explicit embedded-storage requirement

Do not add technologies merely because they are available or make the architecture appear more advanced.

Rule 5 — Scaling Is Requirement-Driven

Do not infer sharding from user count alone.

Translate scale into:

traffic

concurrency

data size

growth

capacity

hotspot behavior

availability requirements

Prefer simpler scaling mechanisms when they satisfy the measured workload.

Rule 6 — Source of Truth Must Be Explicit

Determine which system is authoritative for each correctness-sensitive state.

A cache, search index, replica, or derived projection does not become authoritative merely because it contains the same data.

Rule 7 — Alternatives Must Be Requirement-Specific

When comparing candidates, state:

winner

runner-up

why the winner fits

why the runner-up loses for this requirement set

assumptions

trade-offs

Do not claim that one database is universally better than another.

Rule 8 — Uncertainty Must Be Preserved

If a missing requirement could change the database decision, ask for that requirement rather than inventing a confident answer.

If the missing information cannot change the decision, state the assumption and proceed.

Common Selection Mistakes

Treating data-model mappings as automatic database selections.

Choosing MongoDB merely because the API uses JSON.

Choosing Neo4j merely because relationships exist.

Choosing OpenSearch merely because the application has a search box.

Choosing Redis merely because low latency is desirable.

Choosing RocksDB merely because key/value access is required.

Choosing PostgreSQL merely because it has more features.

Choosing MySQL merely because it is familiar.

Treating a cache or search index as authoritative transactional state.

Treating a read replica as a solution for primary write scaling.

Inferring sharding from user count alone.

Adding multiple databases without distinct workload requirements.

Ignoring business invariants while comparing database technologies.

Making a final choice without considering workload, growth, availability, and operational constraints.

Treating one database as universally superior.

Review Questions for the Selection Agent

Before finalizing a database choice, verify:

What is the dominant data model?

What are the most important business invariants?

Which queries dominate?

What are the read/write and concurrency characteristics?

What are the data size and growth requirements?

What latency and availability requirements exist?

Is the candidate solving a core requirement or merely offering a useful feature?

What system is authoritative for correctness-sensitive state?

Are supporting databases actually necessary?

What simpler architecture was considered?

What is the strongest alternative?

What requirement makes the selected database better for this workload?

What assumption could invalidate the decision?

What operational complexity does the selected architecture introduce?

Source / Grounding

Curated synthesis of the project's database-specific selection profiles and database-selection framework.