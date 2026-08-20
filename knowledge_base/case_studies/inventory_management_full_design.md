Case Study: Inventory Management System — Full 23-Section Design

1. Requirements / Scope

Track products, warehouses, stock levels, stock movements, reservations, purchase receipts and fulfillment. Multiple users/services may update stock concurrently.

Core Reasoning Summary

Definition: This architecture treats the relational database as the authoritative source for inventory quantity, reservations, and stock movements.

Why it exists: Inventory requires correct quantity updates under concurrency and an auditable history of stock changes.

When to use: Use this pattern when multiple users or services can concurrently reserve, receive, release, or otherwise modify stock.

When NOT to use: Do not require strong consistency for derived dashboards, search, or reporting views when their product semantics allow eventual consistency.

Primary architectural rule: Authoritative quantity and reservation state must be decided by the transactional database. Cache and search may support reads but must not authorize reservations.

Advantages: Strong integrity, clear inventory ownership, and auditable stock movement history.

Disadvantages: Concurrent writes require careful transaction design, and high-scale distribution may introduce partitioning or sharding complexity.

Review questions:

What is the authoritative quantity?

What prevents two reservations from consuming the same stock?

What does the unique inventory key actually guarantee?

Which operations must be atomic?

Which reports can tolerate stale data?

2. Scale

Illustrative assumptions: 100K products, 100 warehouses, 10M inventory movements/year, 5K read requests/sec, 1K write requests/sec, periodic bulk receiving.

3. Features & Roles

Warehouse operator, procurement, fulfillment service, administrator, reporting user.

4. Read vs Write

Stock availability is read-heavy. Receipts, allocations and shipments are write-sensitive.

5. Concurrency

Two orders may reserve the same last unit. Conditional atomic updates or transactions must protect available quantity.

6. Entities

Product, Warehouse, Inventory, InventoryReservation, StockMovement, PurchaseOrder, Receipt, Shipment, User.

7. Relationships / Cardinality

Product 1 Inventory by warehouse. Inventory 1 reservations and stock movements. Purchase order 1 lines. Shipment references reservations/order allocations.

8. Schema

A strong core includes:
products
warehouses
inventory
inventory_reservations
stock_movements
purchase_orders
purchase_order_items
shipments

Inventory can have a unique (warehouse_id, product_id).

Uniqueness Boundary

A unique (warehouse_id, product_id) constraint is sufficient to ensure that the authoritative inventory table has at most one inventory row for a given product in a given warehouse.

It is not sufficient to prevent concurrent reservations from exceeding available quantity.

The uniqueness constraint protects row identity; the transactional or conditional quantity update protects the stock-quantity invariant. These solve different problems and must not be treated as interchangeable.

9. SQL vs NoSQL + Trade-offs

Relational DB fits inventory because quantity, reservations and movements require strong integrity. NoSQL may support high-volume event history but should not be introduced without a distinct requirement.

10. Important Queries

Available stock by warehouse, reserve stock, release reservation, receive stock, stock movement history, low-stock report.

11. Indexes

Inventory (warehouse_id, product_id) unique. Reservations by (product_id, warehouse_id, status). Movements by (product_id, created_at).

12. Cache

Cache product metadata and possibly read-only availability snapshots. Do not use stale cache to authorize reservations.

Cache Boundary

A cached availability snapshot is sufficient only for displaying or accelerating availability information when its staleness is acceptable.

It is not sufficient to authorize a reservation or decrement.

The authoritative transactional inventory update must make the final decision.

13. Replication

Read replicas can serve reports and historical reads. Reservation writes remain on the primary.

14. Search

Search engine is optional for product discovery. Ordinary SKU/category lookup may be handled by database indexes.

15. Partitioning

Stock movement history is a good candidate for time-based partitioning when volume grows.

16. Sharding

Avoid initially. If inventory becomes globally distributed, warehouse/region ownership could be evaluated as a shard key, but cross-warehouse operations must be considered.

17. Pagination

Keyset pagination for movement history. Offset may be acceptable for small administrative reports.

18. Transactions

Reservation/decrement operations need atomicity and concurrency protection. Receiving stock and recording the corresponding movement should be consistent.

19. Failure Handling

Retries must not duplicate receipts or stock movements. Deadlocks and transient database errors may require bounded retries.

20. Idempotency

Receiving, reservation commands and external fulfillment callbacks should use idempotency keys or unique external references.

Idempotency Boundary

An idempotency key or unique external reference prevents the same logical receiving, reservation, or callback command from being processed repeatedly within its defined scope.

It does not replace the transaction or concurrency mechanism required to protect inventory quantity.

Duplicate-command protection and quantity correctness are separate invariants.

21. Consistency

Strong consistency for authoritative quantity/reservation state. Eventual consistency is acceptable for dashboards and search.

22. Final Architecture

MySQL/PostgreSQL transactional core, optional Redis cache, optional search/reporting projections.

23. Trade-offs

Prefer a simple relational core. Add partitioning, replicas and sharding only as measured workload demands them.

Common Mistakes

Assuming a unique (warehouse_id, product_id) prevents overselling.

Using cached availability to authorize reservations.

Treating idempotency as a substitute for concurrency control.

Updating quantity without protecting the reservation/decrement invariant.

Treating stock movement history as interchangeable with the current authoritative quantity.

Introducing sharding before defining warehouse/region ownership and cross-warehouse semantics.