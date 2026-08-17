# Relational Schema Design


## Entity identification
Extract durable business entities rather than UI screens or API payloads.

## Keys
Prefer stable primary keys. Add unique constraints for business uniqueness such as email or external reference where required.

## Relationships
Model cardinality:
- one-to-one
- one-to-many
- many-to-many

Many-to-many relationships generally require an associative table in a relational design.

## Normalization
Separate independent facts and avoid unnecessary duplication.

## Denormalization
Use only when a concrete workload justifies it. Identify source of truth and synchronization.

## Temporal data
For status/history requirements, decide whether the system needs:
- current state only
- audit history
- append-only events
- effective dates

## Review rule
A schema is not complete until entity ownership, cardinality, keys, constraints and important access paths are clear.


## Source / grounding
Curated relational design knowledge.
