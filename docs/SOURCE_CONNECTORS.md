# Source Connector Requirements

## Connector principles

Every connector must expose a common interface for discovery, collection, pagination, rate limiting, normalization, health, and provenance.

## Source classes

### Social
Reddit, X, YouTube, TikTok, Instagram, Facebook, LinkedIn, Threads, and other platforms where public/authorized access is available.

### News/media
Global and regional newspapers, magazines, wire services, trade publications, financial media, and licensed news feeds.

### Web/community
Public forums, product communities, developer communities, review sites, blogs, comments, and other accessible public pages.

## Connector contract

Each connector should provide:

- source_type
- source_name
- capabilities
- authentication requirements
- licensing restrictions
- rate limits
- supported date ranges
- pagination method
- source-native ID
- canonical URL generation from source data
- collection timestamp
- raw payload
- normalized mapping
- deletion/update handling
- health status

## URL integrity

The connector is the authoritative owner of the original URL. The AI layer must never invent or fabricate a source link. If a source does not provide a stable URL, the result must be labeled accordingly rather than constructing a potentially invalid link.

## Compliance

Each connector must document whether access is through an official API, licensed feed, public web page, or authorized crawling mechanism. It must honor applicable terms, authentication, rate limits, robots/access restrictions where applicable, and data-retention rules.

## Coverage metadata

The product must show connector coverage and limitations. A missing platform or region must not be represented as evidence that no discussion exists.

## Failure handling

Use exponential backoff, retry budgets, circuit breakers, dead-letter queues, and connector health metrics. Deleted or inaccessible source records should be represented with an appropriate availability status rather than silently disappearing from historical analytics.
