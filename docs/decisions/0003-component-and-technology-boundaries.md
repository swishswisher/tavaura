# ADR-0003: Component and Technology Boundaries

Status: **Accepted**

Date: **2026-08-20**

## Decision

Retain the current primary technology split:

- Next.js/React for marketing, merchant and shopper web interfaces
- ASP.NET Core for the authenticated control plane and system of record
- Python for ingestion, ML, image processing and 3D rendering workers
- PostgreSQL for relational state and initial durable job claiming
- S3-compatible object storage for media and processing artifacts
- TypeScript for one standalone embeddable SDK

The versions may be upgraded, and operational services may be replaced behind
interfaces, without changing these ownership boundaries casually.

## Rationale

The technologies fit their responsibilities and substantial working code
already exists. A language rewrite would delay the MVP without solving the
current product-quality, security or integration gaps.

## Consequences

- Cross-component contracts must be explicit and versioned.
- The worker and backend may not become two competing systems of record.
- Python queue consumers must be deployable independently from FastAPI HTTP.
- Redis is not required until assigned a measured caching/rate-limit role.
- Kubernetes or large event infrastructure is deferred until operational need
  is demonstrated.
