# Keys, Constraints and Integrity


## Primary keys
Identify rows/entities reliably.

## Foreign keys
Enforce valid references where relational integrity is required.

## Unique constraints
Use for business uniqueness such as:
- email
- external payment reference
- booking reference
- seat/show combination

## Check constraints
Use where supported and appropriate for simple domain invariants.

## Application vs database validation
Important integrity rules should be protected at the database layer where practical, not only through application code.

## Review rule
The schema reviewer should ask: "Can concurrent requests violate this rule?" If yes, application-only validation may be insufficient.


## Source / grounding
Curated database integrity knowledge.
