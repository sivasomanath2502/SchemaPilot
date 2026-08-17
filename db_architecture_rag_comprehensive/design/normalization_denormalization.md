# Normalization and Denormalization


## Normalization
Reduce unnecessary duplication and update anomalies by separating independent facts.

## Denormalization
Intentionally duplicate/reshape data to optimize a specific read path.

## Safe denormalization requires
- clear owner of the authoritative value
- update propagation strategy
- failure/retry behavior
- acceptable staleness
- reason for the performance gain

## Common mistake
"Denormalize because joins are slow" is insufficient. Measure or identify the actual high-value query and its bottleneck.


## Source / grounding
Curated relational modeling knowledge.
