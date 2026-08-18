# Case Study: Inventory Management System — Full 23-Section Design

## 1. Requirements / Scope
Track products, warehouses, stock levels, stock movements, reservations, purchase receipts and fulfillment. Multiple users/services may update stock concurrently.

## 2. Scale
Illustrative assumptions: 100K products, 100 warehouses, 10M inventory movements/year, 5K read requests/sec, 1K write requests/sec, periodic bulk receiving.

## 3. Features & Roles
Warehouse operator, procurement, fulfillment service, administrator, reporting user.

## 4. Read vs Write
Stock availability is read-heavy. Receipts, allocations and shipments are write-sensitive.

## 5. Concurrency
Two orders may reserve the same last unit. Conditional atomic updates or transactions must protect available quantity.

## 6. Entities
Product, Warehouse, Inventory, InventoryReservation, StockMovement, PurchaseOrder, Receipt, Shipment, User.

## 7. Relationships / Cardinality
Product 1:N Inventory by warehouse. Inventory 1:N reservations and stock movements. Purchase order 1:N lines. Shipment references reservations/order allocations.

## 8. Schema
A strong core includes:
products
warehouses
inventory
inventory_reservations
stock_movements
purchase_orders
purchase_order_items
shipments

Inventory can have a unique `(warehouse_id, product_id)`.

## 9. SQL vs NoSQL + Trade-offs
Relational DB fits inventory because quantity, reservations and movements require strong integrity. NoSQL may support high-volume event history but should not be introduced without a distinct requirement.

## 10. Important Queries
Available stock by warehouse, reserve stock, release reservation, receive stock, stock movement history, low-stock report.

## 11. Indexes
Inventory `(warehouse_id, product_id)` unique. Reservations by `(product_id, warehouse_id, status)`. Movements by `(product_id, created_at)`.

## 12. Cache
Cache product metadata and possibly read-only availability snapshots. Do not use stale cache to authorize reservations.

## 13. Replication
Read replicas can serve reports and historical reads. Reservation writes remain on the primary.

## 14. Search
Search engine is optional for product discovery. Ordinary SKU/category lookup may be handled by database indexes.

## 15. Partitioning
Stock movement history is a good candidate for time-based partitioning when volume grows.

## 16. Sharding
Avoid initially. If inventory becomes globally distributed, warehouse/region ownership could be evaluated as a shard key, but cross-warehouse operations must be considered.

## 17. Pagination
Keyset pagination for movement history. Offset may be acceptable for small administrative reports.

## 18. Transactions
Reservation/decrement operations need atomicity and concurrency protection. Receiving stock and recording the corresponding movement should be consistent.

## 19. Failure Handling
Retries must not duplicate receipts or stock movements. Deadlocks and transient database errors may require bounded retries.

## 20. Idempotency
Receiving, reservation commands and external fulfillment callbacks should use idempotency keys or unique external references.

## 21. Consistency
Strong consistency for authoritative quantity/reservation state. Eventual consistency is acceptable for dashboards and search.

## 22. Final Architecture
MySQL/PostgreSQL transactional core, optional Redis cache, optional search/reporting projections.

## 23. Trade-offs
Prefer a simple relational core. Add partitioning, replicas and sharding only as measured workload demands them.
