Case Study: Online Ticket Booking System — Full 23-Section Design

This is a worked example intended to teach the model how to derive a rich design from requirements. It is not a fixed template that must be copied for every booking application.

1. Requirements / Scope

Users search events, select a particular show, inspect seat availability, reserve seats, pay, receive a booking confirmation, view booking history, and cancel where policy permits. Administrators/organizers can create events, venues, shows, and seat layouts.

Critical invariant: two successful booking attempts must never own the same seat for the same show.

Core Reasoning Summary

Definition: This architecture uses a relational transactional database as the authoritative owner of show-seat state and booking state, with optional cache, search, and read replicas as supporting systems.

Why it exists: Ticket booking has a concentrated concurrency problem: many users can attempt to acquire the same limited seat at the same time. The architecture therefore prioritizes authoritative transactional ownership over stale availability reads.

When to use: Use this pattern when exclusive ownership of a scarce resource must be enforced under concurrent requests.

When NOT to use: Do not treat Redis, OpenSearch, or read replicas as authoritative ownership systems. Do not introduce sharding or partitioning before the workload demonstrates a need for them.

Primary architectural rule: The authoritative MySQL transaction decides show-seat ownership. Other systems may accelerate reads or provide derived views but must not make the ownership decision.

Advantages: Strong seat-ownership correctness, transactional integrity, explicit duplicate protection, and relatively simple initial deployment.

Disadvantages: The hot show-seat write path can become a bottleneck, external payment integration requires reconciliation, and high-scale distribution can introduce cross-shard complexity.

Review questions:

What exactly prevents two users from owning the same show-seat?

What does the (show_id, seat_id) uniqueness constraint guarantee?

What does it not guarantee?

Why is cached availability not authoritative?

What happens when payment succeeds but the client times out?

When would sharding become justified?

2. Scale

Illustrative assumptions:

10 million registered users

1 million daily active users

5,000 average API requests/sec

20,000 peak requests/sec during popular releases

seat inventory is much smaller than total users

high concurrency occurs around specific shows

The peak is more important than total registered users for booking contention.

3. Features & Roles

Customer:

search events

view shows

view seats

hold/book seats

pay

cancel/view history

Organizer:

create/manage events and shows

manage pricing

Administrator:

venue and platform administration

support/audit

Payment provider:

external actor whose callback/request may be retried.

4. Read vs Write

Read-heavy:

event discovery

show details

seat map

booking history

Write-sensitive:

seat hold/reservation

booking creation

payment state

cancellation

Seat availability is read-heavy but correctness-sensitive because stale availability must not result in double ownership.

5. Concurrency

The dangerous race is:

User A sees seat A1 available.
User B sees seat A1 available.
Both attempt to book A1.

The design must make the final state authoritative in MySQL. A transaction plus a uniqueness/integrity strategy around (show_id, seat_id) prevents two confirmed bookings from owning the same show-seat.

A temporary seat-hold feature, if added, needs an explicit expiration model and concurrency-safe state transition.

Seat Hold Boundary

A temporary hold is an additional business state, not a requirement for every ticket-booking system.

If the product does not offer temporary holds, the booking design does not need hold-expiration logic.

If holds are offered, expiration and ownership transitions become part of the authoritative concurrency model; a cache-based timer alone is not sufficient to establish seat ownership.

6. Entities

A richer model contains:

User

Venue

Seat

Event

Show

ShowSeat

Booking

BookingItem

Payment

Optional:

Organizer

SeatCategory

Coupon

Refund

7. Relationships / Cardinality

Venue 1 Seat.
Event 1 Show.
Show 1 ShowSeat.
Seat 1 ShowSeat across different shows.
User 1 Booking.
Booking 1 BookingItem.
BookingItem N:1 ShowSeat.
Booking 1 PaymentAttempt or 1:1 Payment depending on payment model.

ShowSeat is important because a physical seat is not globally booked. Its availability is contextual to a specific show.

8. Schema

Illustrative relational schema:

users(id, name, email, created_at)

venues(id, name, location, created_at)

seats(id, venue_id, row_label, seat_number, category_id)

events(id, organizer_id, title, description, status)

shows(id, event_id, venue_id, starts_at, ends_at, status)

show_seats(show_id, seat_id, status, price, hold_expires_at, version)

bookings(id, user_id, show_id, status, total_amount, idempotency_key, created_at)

booking_items(id, booking_id, show_seat_id, price)

payments(id, booking_id, provider_reference, status, amount, created_at)

Important constraints:

unique user email where appropriate

unique (show_id, seat_id) in show_seats

unique payment provider reference

unique idempotency key in the appropriate scope

Seat Uniqueness Boundary

The unique (show_id, seat_id) constraint is sufficient to ensure that the show_seats table contains at most one row representing a particular physical seat for a particular show.

It is not by itself a complete seat-booking workflow. The system must still define how that row changes between available, held, booked, expired, and cancelled states, and the authoritative transaction must make the ownership transition concurrency-safe.

The uniqueness constraint protects row identity; the transaction/state transition protects the booking operation.

9. SQL vs NoSQL + Trade-offs

MySQL is the primary recommendation because booking, payment state, seat ownership, foreign-key relationships, and transactions are central.

PostgreSQL is a strong alternative with similar relational suitability.

MongoDB can model some aggregates naturally but does not remove the need to solve concurrent seat ownership and transactional invariants.

Redis is not the authoritative booking database.

OpenSearch can support event discovery if text relevance/fuzzy search becomes important.

10. Important Queries

Examples:

find shows for an event and date

list available seats for a show

retrieve a user's bookings

retrieve booking details and payment state

search events by title/category/location

reserve a specific show-seat

cancel a booking

The seat availability query is likely to be hot and should be designed with the show-specific access path in mind.

11. Indexes

Candidate indexes:

shows(event_id, starts_at)

show_seats(show_id, status)

bookings(user_id, created_at)

bookings(show_id, created_at)

payments(provider_reference) unique

search-specific indexes based on the actual database query

Do not create an index on every column.

12. Cache

Redis is optional.

Good cache candidates:

event metadata

venue/seat layout

show metadata

non-authoritative availability snapshots

Do not trust a cached availability snapshot to grant ownership. The transactional MySQL path must make the final decision.

13. Replication

Read replicas may help event discovery and booking-history reads once the primary becomes read-bound.

Critical post-booking reads may need primary reads or a consistency-aware strategy because replicas can lag.

Replication does not solve the seat-allocation write bottleneck.

14. Search

For simple title/category/location filters, MySQL indexes may be sufficient.

OpenSearch becomes useful for:

full-text event search

typo tolerance

relevance ranking

autocomplete

faceted search

OpenSearch should remain a derived search projection, not the source of truth for bookings.

15. Partitioning

Partitioning is not required for the initial design.

If booking/history tables become very large, time-based partitioning can help lifecycle management and pruning of historical queries.

The decision should follow measured size and query behavior.

16. Sharding

Do not shard initially.

First optimize indexes, transactions, caching, replicas, and possibly partitioning.

If global scale eventually exceeds one MySQL primary's write/storage capacity, a shard key such as venue/region or another carefully chosen ownership key could be considered. The choice must avoid concentrating popular events on one shard.

Cross-shard booking and payment transactions should be minimized.

17. Pagination

Use cursor/keyset pagination for event feeds and booking history at high scale.

Example:
WHERE (created_at, id) < (?, ?) ORDER BY created_at DESC, id DESC LIMIT 20

An index matching the user filter and ordering supports this.

Offset pagination is acceptable for small admin result sets.

18. Transactions

A booking transaction should atomically create/confirm the booking and claim the relevant show-seats according to the chosen hold/booking model.

Payment integration should not assume an external payment API participates in the MySQL transaction. Payment status should be modeled as its own state machine and reconciled safely.

Payment Boundary

The MySQL transaction is sufficient to atomically update authoritative booking and show-seat state within the database.

It is not sufficient to make an external payment provider participate atomically in that transaction.

Payment therefore requires its own state machine, idempotency handling, and reconciliation. Do not infer that a database rollback can automatically undo an external payment.

19. Failure Handling

If the client times out after booking, the retry must not create a second booking.

If Redis fails, the system may fall back to MySQL if capacity permits.

If OpenSearch fails, transactional booking should continue; search indexing can retry.

Deadlocks or transient database failures may require bounded retries.

20. Idempotency

Booking and payment commands should accept an idempotency key.

Idempotency Boundary

Idempotency prevents a retry of the same logical booking command from creating a second logical result.

It does not replace the concurrency mechanism that prevents two different users or different logical requests from claiming the same show-seat.

Therefore idempotency and seat-ownership concurrency control solve different problems and are both required when both failure modes are possible.

Store:

key

user/client scope

request hash

processing status

resulting booking/reference

timestamps

Same key + same request -> return/reuse the existing result.
Same key + different request -> reject.

21. Consistency

Strong transactional consistency:

seat ownership

booking status

payment state transitions

Eventual consistency is acceptable:

search index

cache

analytics

MySQL is the source of truth for booking state.

22. Final Architecture

React/UI -> FastAPI/application service -> MySQL.

Optional:

Redis for cache

OpenSearch for search

read replicas for read scaling

Critical booking path:
application -> MySQL transaction -> authoritative show-seat state.

Search path:
MySQL -> indexing pipeline -> OpenSearch.

23. Trade-offs

Chosen:

relational integrity

strong correctness for booking

simpler initial deployment

optional supporting systems

Rejected initially:

sharding

graph database

Redis as source of truth

OpenSearch for transactional state

The architecture intentionally favors correctness and operational simplicity over premature horizontal distribution.

Common Mistakes

Assuming the unique (show_id, seat_id) constraint alone is the complete booking workflow.

Treating cached availability as authoritative seat ownership.

Assuming a database transaction includes an external payment provider.

Treating idempotency as a substitute for seat-ownership concurrency control.

Adding temporary hold logic when the product does not actually require holds.

Introducing sharding before measuring