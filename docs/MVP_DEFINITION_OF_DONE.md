# Tavaura MVP Definition of Done

Status: **canonical launch contract**

Accepted: **2026-08-20**

The MVP is complete only when one bounded merchant-to-shopper vertical slice is
commercially usable, secure and measurable. A large feature count is not a
substitute for a reliable vertical slice.

## Product promise

For the supported garment family, a merchant can prepare and publish a product
and a shopper can receive a believable 2.5D near-realistic try-on using either
a reusable generated avatar or the bounded photo path.

The MVP does not claim exact fit, a perfect body clone or realtime cloth
physics.

## Bounded launch scope

- one initial garment family: canonical T-shirt/top
- four validated body archetypes: slim, athletic, curvy and plus-size
- three validated poses: neutral, relaxed and slight walk or equivalent
- one controlled camera/lighting specification for primary output
- parameter-based reusable SMPL-X avatars
- one explicitly bounded photo-based try-on flow
- one canonical storefront SDK integration
- one merchant administration workflow
- one production deployment environment plus staging

Additional garment families are accepted only after this vertical slice meets
the quality and operational gates below.

## Merchant journey

- [ ] A merchant organization, store and tenant are created through an
      authorized onboarding flow.
- [ ] Merchant users join through expiring one-time invitations.
- [ ] Merchant uploads or imports a supported product/variant and source image.
- [ ] The source is safely fetched or uploaded and retained immutably.
- [ ] Ingestion classifies, segments and maps the garment to the canonical
      T-shirt archetype.
- [ ] A versioned asset manifest is generated with hashes, model versions,
      parameters and artifact URLs.
- [ ] Automated QC either publishes the version or requests merchant review.
- [ ] Merchant can review, approve, replace or reject the processed asset.
- [ ] The published product can be mapped to a storefront product/variant.

## Shopper journey

- [ ] The SDK initializes with a stable public API.
- [ ] The backend issues a short-lived tenant/product/origin-scoped session.
- [ ] The shopper can select/create a reusable avatar or use the bounded photo
      flow with explicit consent.
- [ ] A render request references immutable avatar/photo and garment versions.
- [ ] The first believable preview is returned progressively.
- [ ] Enhancement can improve the result without changing garment identity.
- [ ] Failure, retry, cancellation and expired-session states are understandable.
- [ ] Shopper media can be deleted immediately and is automatically expired by
      policy.

## Visual-quality gates

- [ ] No catastrophic clipping, disconnected garment regions or missing panels.
- [ ] Neckline, shoulder, sleeve, underarm and hem regions pass documented QC.
- [ ] Garment colour, pattern and recognizable design identity are preserved.
- [ ] Results pass the agreed reference set for all supported body/pose pairs.
- [ ] A repeatable benchmark set and reviewer rubric are stored outside mutable
      production data.
- [ ] Structured and enhanced outputs are compared so enhancement regressions
      are detectable.
- [ ] Marketing claims match measured capability.

Numerical thresholds for clipping, silhouette deviation, identity preservation
and reviewer acceptance must be established during Phases 2–4 before this gate
can be checked.

## Performance gates

- [ ] Widget interaction is immediate and opening is targeted below 500 ms on
      the supported test conditions.
- [ ] Cached avatar/base preview is targeted at 1–2 seconds.
- [ ] First believable try-on is targeted at 2–5 seconds and must remain below
      the agreed launch ceiling under load.
- [ ] Enhancement is progressive and does not block the first preview.
- [ ] Render caching uses immutable input/model hashes.
- [ ] Load and cost tests document p50, p95, failure rate and cost per render.

## Security and tenant gates

- [ ] Authentication is required by default; anonymous routes are explicit.
- [ ] Merchant onboarding cannot assign privileges without an invitation or
      platform-authorized bootstrap.
- [ ] Every tenant-owned query is protected by default isolation.
- [ ] Composite constraints prevent cross-tenant relationships.
- [ ] PostgreSQL row-level security is enabled for public production tenancy.
- [ ] Tenant A/B integration tests cover every CRUD and job/result endpoint.
- [ ] Remote fetches are protected against SSRF and oversized/decompression
      attacks.
- [ ] Storefront sessions validate allowed origins and product/tenant scope.
- [ ] API keys are hashed, scoped, revocable and shown only once.
- [ ] Rate limits and abuse controls cover auth, upload and rendering.
- [ ] Secrets are absent from source and supplied by a production secret store.

## Reliability gates

- [ ] Jobs have lease expiry, heartbeat, bounded retries and attempt records.
- [ ] Abandoned jobs are automatically recovered.
- [ ] Poison jobs reach a review/dead-letter state with actionable diagnostics.
- [ ] Job creation and events use idempotency and a transactional outbox.
- [ ] Object uploads and database commits have orphan detection/cleanup.
- [ ] Asset and render outputs are immutable and reproducible by version.
- [ ] Backup and restore are tested.
- [ ] Database migrations have a controlled deployment and rollback procedure.

## Engineering-quality gates

- [ ] Frontend is tracked correctly in the root repository.
- [ ] Dependency lockfiles are committed.
- [ ] All services build from a clean clone.
- [ ] CI runs backend, frontend, SDK, worker and migration checks.
- [ ] Backend unit/integration tests cover auth, tenancy and job transitions.
- [ ] Frontend and SDK tests cover their public contracts and critical flows.
- [ ] End-to-end tests cover merchant ingestion through shopper result.
- [ ] Dependency and secret scanning run in CI.
- [ ] Logs are structured and correlated by tenant, request and job IDs without
      leaking sensitive media or tokens.
- [ ] Metrics, tracing, error reporting and launch alerts are configured.

## Privacy and legal gates

- [ ] Explicit consent is recorded for shopper photo/body processing.
- [ ] Retention and deletion policies are enforced in storage and database.
- [ ] Privacy notice and data-subject request process match actual behavior.
- [ ] Production storage and transport are encrypted.
- [ ] Model, dataset, font, image and garment-asset licences are documented.
- [ ] Commercial SMPL-X rights or an approved commercially usable replacement
      are confirmed in writing.
- [ ] DeepFashion or other research-only data is not used as commercial product
      data without compatible rights.

## Launch acceptance

Launch requires:

1. every security, tenant, privacy and legal checkbox;
2. every engineering/reliability checkbox that protects customer data or
   recoverability;
3. measured visual and performance results on the bounded reference set;
4. a successful staging pilot with at least one merchant/store configuration;
5. explicit sign-off that public claims do not exceed demonstrated capability.
