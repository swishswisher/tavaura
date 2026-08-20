# Tavaura Current State

Status: **canonical implementation snapshot**

Reconciled: **2026-08-20**

Checkout reviewed: **`007bb3e` on `master`**

Working tree at verification: **clean before Phase 0 documentation edits**

## How to read this document

This file records what exists in the local repository, not what an older plan
said should exist.

Evidence labels:

- **Code verified** — inspected in the current checkout.
- **Test verified** — a relevant build or test was run on 2026-08-20.
- **Conversation checkpoint** — established in the project history but not
  independently reproducible from source code alone.
- **Planned** — accepted direction that is not implemented.

The seven linked project histories were reconciled in full at the text level:
1,019 turns. Attached-image pixels and omitted attachment bodies are not
available through the conversation reader, so screenshot-only observations are
never represented as code-verified facts.

## Locked product state

- Tavaura is an SDK-first multi-tenant virtual try-on SaaS.
- The MVP output is 2.5D near-realism.
- True 3D SMPL-X infrastructure supplies body geometry, proportions and pose.
- Heavy garment preparation happens during ingestion, not at shopper runtime.
- Runtime returns a fast structured preview before optional realism enhancement.
- Both reusable generated avatars and a bounded photo-based path are in scope.
- The MVP optimizes for believable commercial output, not perfect digital twins.
- A known-good canonical garment is validated before catalog automation is built.

These decisions are detailed in [the ADR index](decisions/README.md).

## Repository integrity

| Area | State | Evidence |
|---|---|---|
| Root repository | Active Git repository with Phase 0 and Phase 1.1 checkpoints | Code verified |
| Frontend ownership | Tracked as ordinary monorepo source; broken gitlink removed | Code verified |
| Submodule configuration | No submodule is required | Code verified |
| Frontend local files | Tracked and reconstructable from a clean checkout | Code verified |
| Lockfiles | Frontend and SDK npm lockfiles are tracked | Code verified |
| Generated outputs | Routine build and R&D output paths are ignored | Code verified |
| Backend build artifacts | Removed from the active index; old history is unchanged | Code verified |
| CI/CD | CI and Dependabot definitions added; first remote run pending | Code verified |
| App containers | Compose provides infrastructure only | Code verified |

The fresh-checkout source-ownership blocker is resolved. Rewriting old Git
history to remove historical binary weight is optional and has not been done.

## Verification performed

### Passed on 2026-08-20

- `dotnet build backend/Tavaura.sln --no-restore`
  - zero warnings
  - zero errors
- backend security and tenant-isolation suite
  - 13 tests passed
- `npm run lint` and `npm run build` in `frontend/`
  - successful Next.js 16.3 production build
  - clean ESLint run after React 19 rule fixes
- `npm run build` in `sdk/`
  - TypeScript build successful
- Python compilation for `worker/app`
- worker safe-image intake suite
  - 8 tests passed
- body-estimation tests
- canonical T-shirt topology test
  - one connected component
  - zero boundary edges
  - zero non-manifold edges
  - 5,936 vertices
  - 11,868 faces

### Known quality gaps

- There are no frontend, SDK, full API integration or end-to-end tests.
- Full recursive Python compilation includes legacy Python 2 SMPL research code
  and is not clean.
- Visual R&D outputs are not governed by measurable commercial-quality gates.
- No production deployment or recovery test exists.

## Component status

### Frontend

**Implemented — code/test verified**

- marketing site and product/audience pages
- merchant admin pages for garments, ingestion, renders and settings
- admin login flow and authenticated API client utilities
- shopper widget and SDK demo page
- photo upload preview and sample garment-selection UI
- signup route and page

**Partial or simulated**

- widget garment previews use missing or demo assets
- homepage photo processing calls a backend route that is not implemented
- shopper try-on is not connected to the SMPL-X pipeline
- signup lead storage is process-local
- JWT storage uses browser local storage

**Missing**

- production storefront session flow
- product/variant-aware SDK invocation
- render progress and progressive-result UX
- privacy consent/deletion flow
- automated tests and telemetry
- Three.js or another 3D viewer dependency

### Backend

**Implemented — code/build verified**

- ASP.NET Core API and EF Core/PostgreSQL configuration
- JWT issuance and validation with token-version revocation
- authenticated-by-default controllers with explicit anonymous routes
- expiring merchant invitations and platform-authorized workspace onboarding
- login rate limiting, lockout and legacy password-hash upgrade
- tenants, users, avatars, garments, garment assets and job/result entities
- one-to-one Account -> Store -> Tenant ownership and membership validation
- ingestion/render job and result APIs
- merchant admin dashboard/settings APIs
- migrations and basic database constraints/indexes
- default-deny tenant query filters, composite pipeline keys and PostgreSQL RLS
- hashed one-time-display API keys

**Partial**

- asset versions are numbered but do not contain immutable artifact manifests
- plan usage is displayed but not enforced
- API keys and webhook settings are not yet operational storefront integrations
- production must provision separate non-owner runtime database roles for RLS

**Remaining launch gaps**

- MFA and a refresh-token/device-session lifecycle are not implemented
- storefront session issuance and allowed-origin enforcement are not implemented
- production runtime roles and network policy still need deployment validation

### Worker runtime

**Implemented — code/test verified**

- FastAPI service with health endpoint
- PostgreSQL job consumers using `FOR UPDATE SKIP LOCKED`
- ingestion and render job state transitions
- MinIO-compatible object upload
- provider interface for runtime rendering
- Pillow-based mock output and preview generation

**Partial**

- attempt counts exist, but there is no retry schedule or recovery policy
- asset version rows exist, but URLs remain mutable on `GarmentAsset`
- processed uploads, placeholder masks and placeholder textures are produced
- workers run inside the FastAPI application lifespan

**Missing**

- job leases, heartbeat, abandoned-job reaper and dead-letter handling
- infrastructure-level worker egress restrictions
- real background removal, segmentation and classification
- canonical-archetype selection and deformation
- immutable raw/processed asset manifests and hashes
- automated QC and merchant review workflow
- runtime SMPL-X render provider
- progressive enhancement provider

### SMPL-X and garment R&D

**Implemented — code/test verified**

- SMPL-X model loading and mesh export scripts
- beta calibration and mesh measurement utilities
- deterministic parameter-to-beta estimation
- morphology amplification and curated body archetypes
- pose calibration and reusable pose definitions
- procedural T-shirt topology generation
- garment semantic regions and surface fitting
- render/debug outputs across bodies and poses

**Important interpretation**

This is an offline research and validation package. It is not invoked by the
runtime render worker. The production render path still defaults to
`MockRenderProvider`, which uses Pillow.

**Quality state**

- topology/connectivity checks pass
- body and pose variation works
- procedural garments are not yet commercial-quality cloth assets
- there is no cloth physics, production material/UV pipeline or runtime bridge
- body estimation is deterministic heuristic mapping, not photo inference

### Marvelous Designer canonical garment

**Conversation checkpoint plus local artifact**

- Local project: `worker/avatar_pipeline/smplx/assets/tvra.zprj`
- T-shirt front, back and sleeve panels were created with reasonable dimensions.
- The latest conversation established that scale was not the blocker.
- The immediate task was arranging the panels around the SMPL-X avatar before
  sewing/simulation validation.

The final draped garment, export settings and cross-body validation are not yet
recorded as completed.

### Garment ingestion data model

**Already present**

- tenant-aware Garment records and external product IDs
- queued IngestionJob records with status, attempts and timestamps
- GarmentAsset records
- numbered AssetVersion records
- MinIO object upload
- placeholder processed image, mask and texture locations

**Not yet present**

- products and variants as first-class catalog records
- immutable raw-media records, hashes, dimensions and provenance
- safe fetch/quarantine
- real classification and segmentation
- archetype identity, measurements and deformation metadata
- immutable version manifest containing every artifact/model parameter
- confidence gates and merchant review state
- publish/unpublish lifecycle
- catalog connectors and synchronization
- outbox events and webhook delivery records

### SDK

**Implemented — code/build verified**

- standalone TypeScript SDK package
- separate frontend loader capable of injecting a CTA and opening an iframe

**Architecture drift**

- two competing implementations
- inconsistent initialization and CDN documentation
- no product/variant identifier in the effective contract
- no signed storefront session or allowed-origin enforcement
- no secure `postMessage` protocol
- unsandboxed iframe with broad permissions
- no stable versioned release process

## Current runtime flow

### Working database-queue path

```text
Admin/API creates ingestion or render job
  -> Python worker polls PostgreSQL
  -> worker claims pending job with SKIP LOCKED
  -> mock processing/rendering
  -> MinIO upload
  -> PostgreSQL status/result update
```

### Removed legacy path

The broken synchronous mock controllers and .NET worker HTTP clients have been
removed. PostgreSQL job records are the only active API-to-worker coordination
path.

## Dependency and licensing state

- Frontend is pinned to Next.js `16.3.1` and React `19.2.8`; the npm production
  and development graphs currently audit clean.
- Backend targets `.NET 10` with SDK `10.0.302`; primary Microsoft/EF packages
  are on the current 10.0 servicing line and the NuGet graph audits clean.
- Worker pins `Pillow==12.3.0`, `FastAPI==0.141.1` and `Starlette==1.6.0`;
  remote HTTP intake now uses the standard-library safe-download policy.
- PostgreSQL and MinIO Compose images use exact release tags; unused Redis was
  removed from the local infrastructure stack.
- Production worker and SMPL-X/R&D dependency files are now separate and pinned.
- The full SMPL-X model/software is non-commercial by default; commercial
  rights must be confirmed before commercial launch.

## Immediate next phase

Phase 1 is complete: all production dependency audits are clean, the unit and
security suites pass, the full migration chain applies to PostgreSQL 16.14,
and Tenant A/B RLS plus cross-tenant constraints were verified under a
non-owner runtime role. A representative legacy dataset also upgraded cleanly;
normalized email, ownership membership, store/asset/result/avatar tenant
backfills and plaintext API-key removal were asserted after migration.

The execution frontier is now Phase 2: finish and validate the known-good
canonical T-shirt, record its machine-readable contract, and bridge the
validated SMPL-X/canonical-garment path toward the runtime provider. Public
deployment remains blocked by later MVP definition-of-done gates.
