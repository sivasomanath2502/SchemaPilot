Schema Design — Deep Explanation

Core Reasoning Summary

Definition: Schema design models durable business objects, their identity, relationships, constraints, lifecycle, and the data needed to support important queries.

Why it exists: A schema should represent the domain's durable facts rather than mirroring UI screens or API payloads, while making relationships, ownership, historical facts, and contextual state explicit.

When to use: Use this reasoning whenever creating or reviewing entities, relationships, keys, constraints, temporal data, denormalization, or contextual resource state.

When NOT to use: Do not create entities merely because a UI feature or API endpoint exists, and do not collapse contextual state into a global flag when the state depends on another entity or context.

Primary rule: Model the durable business fact first; then design the access path, constraints, and lifecycle around the actual requirements.

Advantages: Clear ownership, correct cardinality, explicit integrity, and schemas aligned with durable business concepts.

Disadvantages: A domain-accurate schema can require additional relationship/context entities and may need separate read/search structures for specialized access patterns.

Review questions:

Is each entity a durable business object?

Who owns each fact?

Is the cardinality correct?

Are contextual states modeled with their context?

Are current and historical facts distinct?

Are important invariants protected?

Does the schema support important queries?

What lifecycle does each entity require?

Entity identification

An entity is a durable business object with identity and attributes that the system needs to store — extract these from the actual domain, not from UI screens or API payload shapes, which often don't map 1:1 to entities.

Feature vs entity

Entity-Selection Boundary

A feature can motivate an entity or access path, but the feature name alone does not determine the schema.

Create an entity when the domain contains a durable business object or independently meaningful fact that must be stored and managed. A feature can instead be implemented through an existing entity plus an index, search projection, or other access path.

"Search products" is a feature, not necessarily its own entity. The schema should model the underlying Product data and whatever access path (index, search projection) is needed to implement search — features motivate design decisions, but the entity list should reflect durable business objects, not UI capabilities.

Keys

Primary key — stable row/entity identity. Prefer a surrogate key (auto-increment or UUID) over a natural key unless the natural key is genuinely immutable.

Foreign key — a relationship/reference to another entity, enforced at the database level (see schema_constraints.md).

Unique constraint — enforces business uniqueness (email, external reference, or a composite uniqueness rule).

Relationships and cardinality

Cardinality Boundary

Cardinality describes the business relationship between entities; it is not chosen merely for convenient implementation.

A relationship that is currently one-to-many should not be modeled as one-to-one simply because the UI currently shows one child. Validate edge cases and future-valid domain states before fixing the cardinality.

One-to-one — one entity corresponds to at most one entity on the other side.

One-to-many — one parent entity has many related child entities (e.g. one User has many Orders).

Many-to-many — both sides can relate to many on the other side; relational systems typically implement this via a junction/associative table (e.g. Student ↔ Course via an Enrollment table).

Normalization and denormalization

Duplication Boundary

Normalization is the default for independent authoritative facts. Denormalization is an intentional optimization and requires a clear source of truth and synchronization strategy.

Do not treat duplicated data as independently authoritative unless the architecture explicitly defines separate ownership of those facts.

See normalization_denormalization.md for the full treatment — in summary, separate independent facts to avoid duplication and update anomalies by default, and denormalize deliberately only when a specific, justified read pattern needs it, with a clear source of truth and sync strategy.

Temporal modeling

Historical-Fact Boundary

A current-state column is sufficient only when the application needs the current value and not the value that existed at a previous point in time.

If historical accuracy is a requirement, model the historical fact explicitly rather than assuming the current row can reconstruct it later.

If the business needs to answer both "what is true now" and "what was true at a specific point in time" (e.g. "what was the price of this item when the order was placed"), these are different facts and must be modeled accordingly — don't assume the current-state value can stand in for a historical fact. See temporal_audit_data.md for history/audit modeling options.

Constraints

Constraint Boundary

A database constraint should protect an invariant that the database can actually express.

Simple uniqueness, referential integrity, and domain checks can often be enforced directly. Multi-row aggregate invariants may require an additional transaction/concurrency strategy; see schema_constraints.md.

Important business invariants should be protected by database constraints where practical, not only by application-level validation — see schema_constraints.md for the concurrency argument behind this.

Contextual availability — a common modeling trap

Contextual-State Boundary

If a resource's state depends on a context such as show, time slot, tenant, or version, that context is part of the state being modeled.

A global flag is sufficient only when the state is genuinely global to the resource. Do not move contextual state onto the physical resource merely because the current UI exposes it as a simple boolean.

A resource's availability is often contextual, not global. For example, in a ticket-booking system, a physical Seat is not itself "booked" — its availability is contextual to a specific Show. Modeling Seat.is_booked as a global flag would incorrectly prevent the same physical seat from being booked for a different show. The correct model introduces a join entity representing availability in context — e.g. ShowSeat(show_id, seat_id, status, price) — rather than attaching booking state directly to the physical resource.

This generalizes: whenever a resource's state or availability depends on which context (show, time slot, tenant, version) it's being considered in, that context needs to be part of the entity or relationship, not collapsed away.

Schema review checklist

Review Boundary

The checklist is a reasoning aid, not a requirement that every schema contain every possible feature.

History, soft delete, denormalization, and special indexes should be introduced only when the corresponding business or workload requirement exists.

Check, for every entity and relationship:

Ownership — is there a clear, single entity that owns this data?

Cardinality — is the relationship type (1:1, 1, N) actually correct for the domain, not just convenient?

Keys — are primary/foreign/unique keys correctly identified?

Constraints — are concurrency-sensitive invariants protected at the database level?

Duplication — is any denormalization deliberate and justified, or accidental?

Query patterns — does the schema actually support the important queries efficiently (see query_aware_design.md)?

Lifecycle — does this entity need history/audit tracking or soft-delete handling (see temporal_audit_data.md, soft_delete_and_lifecycle.md)?

Contextual state — is any "global" flag actually context-dependent and modeled incorrectly as a result?

Common mistakes

Modeling API payload shapes or UI screens as entities instead of actual durable business objects.

Missing a join/context entity for a resource whose state is contextual, not global (the seat/show example above).

Choosing a natural key that can legitimately change over time as the primary key.

Skipping temporal modeling when the business explicitly needs historical accuracy ("what was true at order time").

Review questions

Is each proposed entity a genuine durable business object, or actually a feature/UI concept?

Is any entity's state actually contextual to another entity, requiring a join/context entity instead of a direct flag?

Does the cardinality of each relationship match the real business rule, including edge cases?

Does the schema distinguish "current state" from "historical fact" wherever the business requires it?

Source / grounding

Curated relational design knowledge.

Common Review Mistakes

Modeling UI screens or API payloads as entities.

Treating a feature as automatically requiring a new table.

Choosing cardinality from the current UI instead of the domain rule.

Modeling contextual availability as a global flag.

Using a mutable natural identifier as the primary key without justification.

Assuming the current value can reconstruct historical facts.

Adding denormalized copies without identifying the authoritative owner.

Assuming a database constraint can express an arbitrary multi-row business invariant.

Adding lifecycle features such as soft delete without a concrete requirement.