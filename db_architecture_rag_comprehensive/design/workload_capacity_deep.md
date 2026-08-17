# Workload and Capacity Planning — Deep Explanation

## User count is not traffic
Registered users, active users, concurrent users and requests per second are different quantities.

## Important dimensions
- total users
- daily/monthly active users
- concurrent users
- average RPS
- peak RPS
- read/write ratio
- data size
- data growth
- latency target
- availability target

## Example calculation
If 1,000,000 active users each generate 10 requests per minute:
1,000,000 × 10 / 60 ≈ 166,667 requests/sec average.

This is only an estimate; real traffic depends on user behavior and request distribution.

## Read/write ratio
A 90:10 workload means approximately 90% reads and 10% writes. Read-heavy systems may benefit from caching and replicas. Write-heavy systems may be limited by indexes, transactions, locks and storage throughput.

## Peak traffic
Ticket releases, sales, promotions and batch jobs can create short peaks much larger than average traffic. The report should state the peak assumption explicitly.

## Data growth
Estimate:
records/day × average row/document size × retention period.
Then account for indexes, replicas, audit data and backups.

## Capacity dimensions
Check:
- CPU
- RAM
- storage
- IOPS
- network
- database connections
- lock contention
- query latency

## Principle
"10 million users" is not enough evidence for sharding. The agent should translate business scale into workload assumptions before making architecture decisions.
