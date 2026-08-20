# ADR-0007: MVP Jobs, Storage and Immutable Versions

Status: **Accepted**

Date: **2026-08-20**

## Decision

PostgreSQL may remain the MVP job transport using `FOR UPDATE SKIP LOCKED`.
Before production, jobs gain:

- lease owner and expiry
- heartbeat
- bounded retries with backoff
- immutable attempt records
- recovery/reaper behavior
- cancellation and review/dead-letter state
- idempotency
- transactional outbox events

MinIO remains local-only. Production uses managed S3-compatible storage with
signed access, lifecycle rules and a CDN.

Every raw input, garment version, avatar version and render result is immutable
and content-addressable or version-addressable. A version manifest records
hashes, provenance, model parameters and all artifact locations.

## Rationale

- PostgreSQL queueing is sufficient for initial scale and reduces infrastructure.
- Reliability semantics matter more than adding a new broker prematurely.
- Immutable assets make results reproducible, cacheable and auditable.

## Consequences

- Mutable keys such as `processed/{garment_id}.png` must be replaced.
- AssetVersion must become a real manifest, not only a version number.
- A managed queue may be adopted later behind the same job contracts.
- Redis is optional and not the source of truth.
