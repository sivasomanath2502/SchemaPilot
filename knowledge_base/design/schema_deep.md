# Schema Design — Deep Explanation

## Entity
An entity is a durable business object with identity and attributes that the system needs to store.

## Feature vs entity
"Search products" is a feature, not necessarily an entity. The schema should model the product data and search access path needed to implement it.

## Keys
Primary key: stable row identity.
Foreign key: relationship/reference to another entity.
Unique constraint: business uniqueness.

## Cardinality
One-to-one: one entity corresponds to at most one entity on the other side.
One-to-many: one parent has many children.
Many-to-many: both sides can have many relationships; relational systems usually use a junction table.

## Normalization
Separate independent facts and reduce inappropriate duplication.

## Denormalization
Intentionally duplicate/precompute data for a justified workload. Always identify the source of truth and synchronization mechanism.

## Temporal modeling
If the business asks "what is true now" and "what was true at the time of the order," these may be different facts and should be modeled accordingly.

## Constraints
Important business invariants should be protected by database constraints where practical, not only application validation.

## Schema review
Check entities, ownership, cardinality, keys, constraints, duplication, query patterns and lifecycle.
