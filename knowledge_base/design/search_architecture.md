# Search Architecture


## Transactional DB vs search engine
A relational/document DB can remain the source of truth while a search engine maintains a derived index.

## Use a search engine when
- relevance ranking matters
- fuzzy matching matters
- full-text queries are central
- faceting/autocomplete/search analytics justify it

## Required design
- source of truth
- indexing pipeline
- update latency
- retry/dead-letter behavior if asynchronous
- index rebuild strategy
- stale result tolerance

## Review rule
A search requirement does not automatically mean replacing the primary database.


## Source / grounding
https://docs.opensearch.org/latest/
