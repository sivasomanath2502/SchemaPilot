# Indexing Strategy


## Principle
Index real access paths, not every column.

## Analyze
- WHERE
- JOIN
- ORDER BY
- range filters
- equality filters
- uniqueness
- frequency
- selectivity

## Composite indexes
Column order matters. An index should be evaluated against the actual query shape.

## Costs
Indexes consume storage and memory and increase write-maintenance work.

## Review requirement
Every important index recommendation should be traceable to a concrete query.

## Validation
Use EXPLAIN/query plans where the database supports them.


## Source / grounding
https://dev.mysql.com/doc/refman/8.4/en/optimization-indexes.html
