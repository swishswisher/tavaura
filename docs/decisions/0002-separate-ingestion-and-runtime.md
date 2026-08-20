# ADR-0002: Separate Garment Ingestion and Shopper Runtime

Status: **Accepted**

Date: **2026-08-20**

## Context

Classification, segmentation, garment understanding and canonical asset
construction are expensive and failure-prone. Repeating them for every shopper
would increase latency, cost and uncertainty.

## Decision

Tavaura has two mandatory pipelines:

1. **Garment ingestion** — asynchronous, automation-first, versioned and
   reviewable. It prepares and publishes immutable garment versions.
2. **Try-on rendering** — shopper-facing and runtime-light. It consumes only
   prepared, published versions.

Every proposed feature must be classified as garment-preparation work or
shopper-runtime work before implementation.

## Rationale

- isolates failures and makes the system debuggable
- removes repeated heavy processing from shopper clicks
- enables QC and merchant review before publication
- permits deterministic caching and reproducible results
- supports incremental replacement of processing/render providers

## Consequences

- Render jobs may not classify or segment source catalog images.
- Ingestion may take longer because it is not on the critical shopper path.
- Published asset versions must contain everything runtime requires.
- The SDK never invokes the ingestion worker directly.
