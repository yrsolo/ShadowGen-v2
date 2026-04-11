# Caching Strategy

The architecture reserves space for multi-level caching.

## Cache Levels

1. request-level deduplication
2. source image cache by checksum
3. intermediate artifact cache
4. final result cache by normalized request parameters

## First Stage

At bootstrap stage we only keep:

- cache key helpers
- integration points in the pipeline layer
- no-op or placeholder cache implementations

## Key Design

- source image key: hash(image bytes)
- request result key: hash(source hash + normalized params + pipeline version)
