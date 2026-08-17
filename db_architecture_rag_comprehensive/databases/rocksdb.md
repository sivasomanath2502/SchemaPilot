# RocksDB — Full Selection Profile


## Role
Embedded persistent key-value storage library, not a typical client/server application database.

## Strong selection signals
- Embedded local persistence.
- Key/value access.
- Point lookups.
- Ordered/range scans.
- Building a storage engine or infrastructure component.

## Architecture distinction
The application or surrounding system must provide higher-level capabilities such as networking, replication, distributed consistency, query semantics and secondary indexing.

## Weak-fit signals
- Normal web CRUD
- SQL joins
- Foreign-key integrity
- Payment/order/booking schemas
- General reporting

## Decision rule
RocksDB should rarely win an ordinary "which database should I use?" question unless the requirement explicitly asks for embedded KV storage.


## Source / grounding
https://rocksdb.org/docs/
