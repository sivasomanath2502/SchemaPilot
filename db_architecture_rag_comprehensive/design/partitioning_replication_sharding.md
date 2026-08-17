# Partitioning, Replication and Sharding


## Partitioning
Divide a logical dataset into partitions. Useful when access patterns or data lifecycle naturally isolate subsets.

## Replication
Copies data for availability and/or read scaling. Replication does not inherently increase write capacity.

## Sharding
Distributes ownership of data across nodes.

Evaluate:
- shard key
- cardinality
- distribution
- hotspots
- cross-shard queries
- transactions
- rebalancing
- operational recovery

## Progression
Optimize -> index -> scale vertically -> replicate/cache -> partition -> shard.

Do not use sharding simply because a user count sounds large.


## Source / grounding
https://dev.mysql.com/doc/refman/8.4/en/partitioning.html
