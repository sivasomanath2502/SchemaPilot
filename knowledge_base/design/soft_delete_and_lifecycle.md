# Deletion, Soft Delete and Data Lifecycle


## Deletion decision
Do not automatically add deleted_at to every table.

Ask:
- Must the record be recoverable?
- Is hard deletion required?
- Are there retention requirements?
- Do foreign keys depend on the row?
- Should deleted records remain searchable?

## Soft delete trade-offs
Soft deletion preserves history but complicates:
- uniqueness
- queries
- indexes
- foreign keys
- storage growth

## Lifecycle
For large systems, consider archival/retention policies rather than indefinite growth.


## Source / grounding
Curated database lifecycle knowledge.
