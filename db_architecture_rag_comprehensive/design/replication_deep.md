# Replication — Deep Explanation

## Definition
Replication creates additional database copies. It is mainly used for availability, failover and read scaling.

## Primary/replica
A primary accepts writes. Replicas receive changes and may serve reads.

## Asynchronous replication
The primary does not wait for every replica before acknowledging. This can reduce write latency but introduces replication lag and a potential loss window during failure.

## Synchronous replication
The write waits for required replica acknowledgement according to the configured protocol. This can improve durability characteristics but may increase latency and sensitivity to network/replica failures.

## Read-after-write problem
A write reaches the primary. The next read goes to a lagging replica. The client sees stale data.

Possible strategies:
- read critical paths from primary
- session stickiness
- consistency-aware routing
- wait for an appropriate replication position where supported

## Failover
A replica can be promoted after primary failure. Automated failover improves availability but must handle stale replicas, split-brain risks and recovery procedures.

## What replication does NOT solve
Replication does not automatically increase write capacity. It does not replace backups. It does not remove consistency concerns.
