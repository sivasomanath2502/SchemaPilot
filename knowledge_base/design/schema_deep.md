# Schema Design — Deep Explanation

## Entity identification
An entity is a durable business object with identity and attributes that the system needs to store — extract these from the actual domain, not from UI screens or API payload shapes, which often don't map 1:1 to entities.

## Feature vs entity
"Search products" is a feature, not necessarily its own entity. The schema should model the underlying `Product` data and whatever access path (index, search projection) is needed to implement search — features motivate design decisions, but the entity list should reflect durable business objects, not UI capabilities.

## Keys
- **Primary key** — stable row/entity identity. Prefer a surrogate key (auto-increment or UUID) over a natural key unless the natural key is genuinely immutable.
- **Foreign key** — a relationship/reference to another entity, enforced at the database level (see `schema_constraints.md`).
- **Unique constraint** — enforces business uniqueness (email, external reference, or a composite uniqueness rule).

## Relationships and cardinality
- **One-to-one** — one entity corresponds to at most one entity on the other side.
- **One-to-many** — one parent entity has many related child entities (e.g. one `User` has many `Order`s).
- **Many-to-many** — both sides can relate to many on the other side; relational systems typically implement this via a junction/associative table (e.g. `Student` ↔ `Course` via an `Enrollment` table).

## Normalization and denormalization
See `normalization_denormalization.md` for the full treatment — in summary, separate independent facts to avoid duplication and update anomalies by default, and denormalize deliberately only when a specific, justified read pattern needs it, with a clear source of truth and sync strategy.

## Temporal modeling
If the business needs to answer both "what is true now" and "what was true at a specific point in time" (e.g. "what was the price of this item when the order was placed"), these are different facts and must be modeled accordingly — don't assume the current-state value can stand in for a historical fact. See `temporal_audit_data.md` for history/audit modeling options.

## Constraints
Important business invariants should be protected by database constraints where practical, not only by application-level validation — see `schema_constraints.md` for the concurrency argument behind this.

## Contextual availability — a common modeling trap
A resource's availability is often contextual, not global. For example, in a ticket-booking system, a physical `Seat` is not itself "booked" — its availability is contextual to a specific `Show`. Modeling `Seat.is_booked` as a global flag would incorrectly prevent the same physical seat from being booked for a *different* show. The correct model introduces a join entity representing availability *in context* — e.g. `ShowSeat(show_id, seat_id, status, price)` — rather than attaching booking state directly to the physical resource.

This generalizes: whenever a resource's state or availability depends on *which context* (show, time slot, tenant, version) it's being considered in, that context needs to be part of the entity or relationship, not collapsed away.

## Schema review checklist
Check, for every entity and relationship:
- Ownership — is there a clear, single entity that owns this data?
- Cardinality — is the relationship type (1:1, 1:N, N:N) actually correct for the domain, not just convenient?
- Keys — are primary/foreign/unique keys correctly identified?
- Constraints — are concurrency-sensitive invariants protected at the database level?
- Duplication — is any denormalization deliberate and justified, or accidental?
- Query patterns — does the schema actually support the important queries efficiently (see `query_aware_design.md`)?
- Lifecycle — does this entity need history/audit tracking or soft-delete handling (see `temporal_audit_data.md`, `soft_delete_and_lifecycle.md`)?
- Contextual state — is any "global" flag actually context-dependent and modeled incorrectly as a result?

## Common mistakes
- Modeling API payload shapes or UI screens as entities instead of actual durable business objects.
- Missing a join/context entity for a resource whose state is contextual, not global (the seat/show example above).
- Choosing a natural key that can legitimately change over time as the primary key.
- Skipping temporal modeling when the business explicitly needs historical accuracy ("what was true at order time").

## Review questions
- Is each proposed entity a genuine durable business object, or actually a feature/UI concept?
- Is any entity's state actually contextual to another entity, requiring a join/context entity instead of a direct flag?
- Does the cardinality of each relationship match the real business rule, including edge cases?
- Does the schema distinguish "current state" from "historical fact" wherever the business requires it?

## Source / grounding
Curated relational design knowledge.
