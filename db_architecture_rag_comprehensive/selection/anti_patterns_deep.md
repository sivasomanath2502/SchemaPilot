# Database Architecture Anti-Patterns — Deep Review Guide

## Premature sharding
Adding sharding before demonstrating a single-node capacity problem.

## Technology shopping
Adding MySQL + MongoDB + Redis + OpenSearch simply to make an architecture look advanced.

## Cache as source of truth
Using Redis as authoritative transactional state without understanding durability and consistency requirements.

## Search as transaction store
Using OpenSearch as the authoritative payment, booking or inventory system.

## Index everything
Adding indexes without identifying the queries they support.

## Graph because relationships exist
Every relational application has relationships. Graph databases are for relationship-centric traversal.

## MongoDB because schema is flexible
Flexibility is useful only when it matches access patterns and data ownership.

## Replica solves writes
Read replicas primarily help reads/availability; they do not automatically increase primary write capacity.

## User count means sharding
User count must be translated into traffic, data size, concurrency and capacity requirements.

## Strong consistency everywhere
Not every derived value requires immediate consistency. Search and cache can often tolerate staleness.

## Soft delete everywhere
Soft delete introduces query, uniqueness and storage complexity and should be a requirement-driven choice.

## Agent-specific anti-pattern
Do not create an agent for every tiny task. Four well-defined agents are easier to reason about than ten loosely defined agents.
