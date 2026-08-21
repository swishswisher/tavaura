# Tavaura Implementation Roadmap

Status: **canonical execution order**

Accepted: **2026-08-20**

This roadmap preserves the decisions reconciled from the project history while
responding to the actual current code. Work should be completed as small,
reviewable vertical increments with tests added alongside behavior.

## Phase 0 — Decision and state lock

Goal: remove dependence on chat memory and prevent architecture drift.

Deliverables:

- canonical current-state document
- canonical MVP definition of done
- canonical implementation roadmap
- accepted architecture decision records
- corrected root and architecture documentation

Exit criteria:

- documents agree on product scope, pipeline separation and delivery order
- intended state is separated from implemented state
- old contradictory statements are explicitly superseded
- all new documents are linked from the root README

## Phase 1 — Repository and security stabilization

Status: **completed and public-launch security gate verified 2026-08-21**

This phase precedes public deployment. Canonical-garment design may continue as
an isolated manual R&D activity.

### 1.1 Repair repository ownership

- convert `frontend` from the broken gitlink into ordinary monorepo source
- remove obsolete nested-repository assumptions
- commit frontend and SDK lockfiles
- stop ignoring dependency lockfiles
- remove generated binaries and routine R&D output from ordinary source control
- define artifact/model download instructions
- verify a clean clone builds all services

### 1.2 Patch supported runtimes and dependencies

- patch Next.js immediately, then migrate to the current Active LTS line
- update vulnerable Python HTTP dependencies
- pin infrastructure container versions
- define separate locked worker-runtime and SMPL-X/R&D environments
- plan and execute the .NET 10 LTS upgrade
- add automated dependency/security checks

### 1.3 Secure identity and privileged routes

- make authenticated access the ASP.NET default policy
- replace merchant self-registration with expiring invitations
- create a platform-authorized tenant/account onboarding flow
- remove or development-gate legacy mock endpoints
- add normalized unique email persistence
- adopt ASP.NET Core Identity password hashing or a documented compatible
  migration path
- add rate limiting, login lockout and token/session lifecycle controls
- hash, scope and display API keys only once

### 1.4 Protect remote media intake

- route every production remote fetch through the worker safe-download policy;
  the .NET API must not fetch remote media
- restrict schemes, addresses, redirects, bytes, pixels, MIME types and timeouts
- prefer direct upload or signed known-storage URLs
- restrict worker outbound networking
- add malicious/invalid media tests

### 1.5 Harden tenant boundaries

- codify Account -> Store -> Tenant ownership
- map each Store one-to-one to the existing Tenant security partition
- validate memberships before issuing tenant-scoped sessions
- accept tenant headers only for authorized platform/development flows
- inject tenant context into EF global query filters
- add composite tenant keys/foreign keys
- add PostgreSQL row-level security for production
- build Tenant A/B isolation integration tests

Phase 1 exit criteria:

- no critical dependency finding in the production dependency graph
- no unauthenticated privileged route; intended anonymous writes are explicit,
  bounded and rate-limited
- arbitrary URLs cannot reach private/internal networks
- fresh clone includes the real frontend and reproducible dependencies
- automated tenant-isolation tests pass

Verification checkpoint:

- frontend, SDK and backend Release builds pass
- backend unit and PostgreSQL integration suite: 29 passed with zero skips
- frontend public-route security suite: 2 passed
- worker remote-media security suite: 8 passed
- frontend, SDK, NuGet and worker production dependency audits: zero known
  vulnerabilities
- full migration chain applied to disposable PostgreSQL 16.14
- representative pre-Phase-1 users, ownership, assets, avatars, jobs and
  results upgraded with every tenant/membership/email backfill asserted
- non-owner PostgreSQL role verified Tenant A/B RLS, default-deny behavior and
  platform system context
- cross-tenant composite foreign-key insertion was rejected
- invitation creation authorization, expiry, email matching, concurrent replay
  rejection and rollback are HTTP integration-tested
- every privileged controller route is enumerated and verified to return
  `401`/`403` anonymously; the production-only bootstrap behavior is tested
- Tenant A/B list, detail, create, update and delete behavior is API-tested
- login lockout, both rate-limit policies, token revocation and one-time API-key
  storage/response behavior are API-tested
- the public process-local signup mutation was removed and is guarded by a
  frontend regression test plus browser verification

## Phase 2 — Known-good canonical T-shirt

Goal: remove garment quality as an uncontrolled variable before automating
catalog ingestion.

### 2.1 Complete Marvelous Designer reference garment

- open `worker/avatar_pipeline/smplx/assets/tvra.zprj`
- arrange front, back and sleeve panels around the reference avatar
- verify sewing orientation and seam pairing
- simulate and resolve intersections/explosions
- standardize units, axes, avatar pose and particle distance
- create UV/material zones and stable export settings
- preserve the source project and export a versioned reference asset

### 2.2 Create a canonical garment contract

Record in a machine-readable manifest:

- archetype ID and semantic version
- source project and export hashes
- scale, axes and units
- body/pose reference
- panel and semantic-region identifiers
- seams and attachment landmarks
- UV/material zones
- licence/provenance
- QC thresholds

### 2.3 Validate across the bounded matrix

- bodies: slim, athletic, curvy and plus-size
- poses: neutral, relaxed and slight walk or selected equivalents
- views: front, side, three-quarter and targeted closeups
- regions: neckline, shoulder, sleeve, underarm, side seam and hem
- calculate topology and clipping/silhouette metrics
- record human review using a stable rubric

Phase 2 exit criteria:

- one commercially credible T-shirt archetype passes the agreed matrix
- exports are deterministic, versioned and importable by Python
- failures are measurable rather than judged only from ad-hoc screenshots

## Phase 3 — SMPL-X runtime bridge

Goal: make the production RenderJob path consume the real 3D foundation.

### 3.1 Define immutable runtime inputs

- version Avatar parameters and pose
- replace plain `SmplParametersJson` with a validated versioned schema
- expand garment asset versions into immutable manifests
- make RenderJob reference exact avatar, garment, pose and renderer versions

### 3.2 Implement `SmplxRenderProvider`

- implement the existing `RenderProvider` protocol
- load cached SMPL-X geometry from versioned parameters
- load the canonical garment version and fitting metadata
- apply the selected pose and garment fitting
- render colour/alpha, depth, normals and semantic masks
- upload immutable structured preview artifacts
- keep `MockRenderProvider` development-only

### 3.3 Separate service and consumer lifecycles

- create standalone ingestion and render worker entry points
- stop starting all queue consumers as incidental FastAPI lifespan tasks
- add health, readiness and dependency checks
- add job lease, heartbeat, attempts, recovery and cancellation

Phase 3 exit criteria:

- a normal backend RenderJob produces output from SMPL-X and the canonical
  garment without invoking the Pillow mock engine
- the same immutable inputs reproduce the same structured result
- worker failure and restart do not strand jobs permanently

## Phase 4 — 2.5D near-realism

Goal: turn structurally correct output into commercially persuasive output.

### 4.1 Controlled rendering

- production camera and crop specification
- body/head/skin/hair representation appropriate for the bounded MVP
- garment texture, colour and fabric material handling
- lighting, shadows, depth-aware occlusion and anti-aliasing
- colour management and output profiles

### 4.2 Progressive enhancement

- introduce an enhancement provider behind a replaceable interface
- condition enhancement on structured colour/depth/normal/mask outputs
- prevent garment identity, colour and pattern drift
- show structured preview before enhancement finishes
- cache by immutable input and model hashes

### 4.3 Short motion

- render a controlled pose sequence or short loop
- avoid realtime cloth physics for MVP
- verify temporal consistency and garment identity
- produce a web-appropriate clip plus poster image

Phase 4 exit criteria:

- bounded reference set meets visual acceptance thresholds
- first believable result and enhancement latency meet launch targets
- enhanced output demonstrably preserves the merchant product

## Phase 5 — Production garment ingestion

Goal: automate creation of canonical garment versions without moving heavy work
into the shopper request.

### 5.1 Data model

- Product and ProductVariant
- immutable RawMediaAsset
- GarmentAssetVersion manifest with every artifact and parameter
- JobAttempt, QualityCheck and ReviewDecision
- publication state and lineage
- OutboxEvent and WebhookDelivery

### 5.2 Processing

- safe upload/catalog intake
- validation, hashing and deduplication
- view/type classification
- real segmentation and background removal
- garment landmarks and measurement extraction
- canonical archetype selection
- archetype deformation and texture preparation
- QC scoring and review fallback

### 5.3 Reliability

- idempotent job creation and processing
- leases, heartbeat and retry backoff
- dead-letter/review state
- transactional outbox
- orphan-object cleanup and lifecycle policies

Phase 5 exit criteria:

- a supported merchant product becomes a published immutable garment version
  through the normal admin workflow
- reprocessing creates a new version and never mutates an older render input
- failed or low-confidence assets are recoverable and reviewable

## Phase 6 — Product integration

### 6.1 Canonical SDK

- choose `sdk/` as the single distributable source
- remove or reduce the frontend loader to a consumer of the built SDK
- define stable `init`, open, close, event and destroy APIs
- include store, product and variant context
- add signed storefront sessions and allowed-origin validation
- sandbox the iframe and implement origin-checked messaging
- support dynamic/SPA product pages
- publish versioned artifacts with installation documentation

### 6.2 Merchant administration

- onboarding and invitations
- products/variants and source media
- ingestion progress and failure recovery
- QC review and publish workflow
- usage, limits and audit history
- webhook delivery state

### 6.3 Shopper experience

- consent-aware avatar/photo onboarding
- render creation, progress and progressive result
- retry/cancel/error states
- save/share only where privacy and retention rules permit
- automatic and immediate deletion controls
- mobile/accessibility validation

Phase 6 exit criteria:

- the same supported product completes the full merchant-to-shopper journey in
  staging through the public SDK contract

## Phase 7 — Launch hardening

- CI/CD and controlled database migrations
- unit, integration, contract and end-to-end tests
- load, latency and cost benchmarks
- structured logs, traces, metrics, alerts and error reporting
- production secret management
- backup and restore drill
- storage retention/deletion verification
- privacy/legal review and commercial model licences
- pilot runbook and incident response
- marketing-claim review against measured output

Phase 7 exit criteria are the complete checklist in
[MVP_DEFINITION_OF_DONE.md](MVP_DEFINITION_OF_DONE.md).

## Explicitly deferred

- perfect photo-derived 3D identity
- realtime cloth physics
- all garment categories
- cosmetics beyond a separately approved vertical slice
- social challenges and broad sharing mechanics
- numerous commerce-platform connectors before one canonical SDK flow works
- high-scale queue infrastructure before measured need
