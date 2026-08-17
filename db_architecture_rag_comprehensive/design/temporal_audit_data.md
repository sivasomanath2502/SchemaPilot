# History, Audit and Temporal Data


## Current state vs history
A table holding current status is not automatically an audit log.

If requirements include "who changed what and when", model audit/history explicitly.

## Options
- audit table
- append-only event log
- status history table
- effective_from/effective_to fields

## Review questions
- Is history mandatory?
- Can records be deleted?
- Is legal/audit traceability required?
- Is current state enough?
- How large will history become?

## Scaling
Large historical tables may require lifecycle policies, partitioning, archival or retention rules.


## Source / grounding
Curated data lifecycle knowledge.
