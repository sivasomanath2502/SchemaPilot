RocksDB — Full Selection Profile

Role

Embedded persistent key-value storage library, not a typical client/server application database.

Core Selection Summary

Definition: RocksDB is an embedded persistent key-value storage library, not a typical client/server application database.

Why it exists: It provides local persistent key-value storage with point lookups and ordered/range scans for applications or infrastructure components that need an embedded storage engine.

When to use: Prefer RocksDB when the requirement explicitly calls for embedded local persistence, key/value access, point lookups, ordered/range scans, or building a storage engine/infrastructure component.

When NOT to use: Do not choose RocksDB for ordinary web CRUD, SQL joins, foreign-key integrity, payment/order/booking schemas, or general reporting.

Primary selection rule: RocksDB should rarely win an ordinary "which database should I use?" decision unless embedded key-value storage is itself an explicit requirement.

Advantages: Embedded deployment, persistent local key-value storage, efficient point lookups, and ordered/range scans.

Disadvantages: The surrounding application must provide higher-level capabilities such as networking, replication, distributed consistency, query semantics, and secondary indexing when those are required.

Review questions:

Is embedded local storage explicitly required?

Is the dominant access pattern key/value lookup or ordered/range scanning?

Who provides networking and distributed access?

Who provides replication and distributed consistency?

Are SQL joins, foreign keys, or general reporting required?

Would a client/server database be a better fit?

Strong selection signals

Embedded local persistence.

Key/value access.

Point lookups.

Ordered/range scans.

Building a storage engine or infrastructure component.

Architecture distinction

The application or surrounding system must provide higher-level capabilities such as networking, replication, distributed consistency, query semantics and secondary indexing.

Embedded-Storage Boundary

RocksDB is sufficient for the local persistent key-value storage layer when the application needs embedded storage and can operate directly against the library.

It is not a complete replacement for a client/server database. Networking, multi-process service access, replication, distributed consistency, richer query semantics, and secondary indexing must be provided by the surrounding architecture when required.

Do not infer that RocksDB provides those higher-level database capabilities merely because it provides durable key-value storage.

Weak-fit signals

Normal web CRUD

SQL joins

Foreign-key integrity

Payment/order/booking schemas

General reporting

Decision rule

RocksDB should rarely win an ordinary "which database should I use?" question unless the requirement explicitly asks for embedded KV storage.

Decision Boundary

Embedded KV storage is the decisive selection signal. If the application instead requires a general-purpose client/server database with SQL, joins, foreign-key integrity, or built-in distributed service capabilities, RocksDB is not the appropriate default.

Do not select RocksDB simply because key/value access is fast; the embedded deployment model must itself be a meaningful requirement.

Source / grounding

https://rocksdb.org/docs/

Common Mistakes

Treating RocksDB as a typical client/server database.

Choosing RocksDB merely because the workload contains key/value lookups.

Forgetting that networking and distributed access belong to the surrounding application.

Assuming RocksDB automatically provides replication or distributed consistency.

Using RocksDB for SQL joins, foreign-key integrity, payment/order/booking schemas, or general reporting.

Selecting RocksDB without an explicit embedded-storage requirement.