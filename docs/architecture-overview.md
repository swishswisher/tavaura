# Tavaura Architecture Overview

Status: **canonical target architecture**

Last reconciled: **2026-08-20**

Verified checkout: **`007bb3e`**

This document describes the architecture Tavaura is building toward. It does
not imply that every component is already implemented. See
[CURRENT_STATE.md](CURRENT_STATE.md) for the evidence-backed implementation
status.

## Product architecture

Tavaura is an SDK-first, multi-tenant virtual try-on SaaS for fashion
ecommerce. The locked MVP direction is:

- output: 2.5D near-realistic images and short motion clips
- structural foundation: true 3D SMPL-X bodies, poses and garment geometry
- heavy work: asynchronous ingestion, avatar creation and precomputation
- shopper runtime: cached, deterministic and progressively enhanced
- product modes: reusable generated avatars and a bounded photo-based path
- integration: an embeddable storefront SDK backed by a merchant control plane

The MVP does not promise a perfect digital twin, realtime cloth physics or a
complete 3D garment reconstructed from one catalog image.

## Component ownership

### Frontend

Technology: Next.js and React.

Responsibilities:

- marketing pages
- merchant administration
- shopper/widget user experience
- authenticated API consumption
- render progress and result presentation

The frontend must not contain persistence, ML processing or the distributable
storefront SDK implementation.

### Backend

Technology: ASP.NET Core, Entity Framework Core and PostgreSQL.

Responsibilities:

- authentication and authorization
- account, store and tenant ownership
- merchant/catalog metadata
- immutable asset-version metadata
- ingestion and render job orchestration
- usage, audit, webhook and administration APIs
- serving as the system of record

The backend must not perform image segmentation, SMPL-X generation or garment
rendering.

### Worker

Technology: Python.

Responsibilities:

- safe media intake and validation
- garment segmentation and classification
- canonical-garment selection and deformation
- SMPL-X avatar/body processing
- structured 3D-to-2.5D rendering
- optional progressive AI enhancement
- upload of immutable artifacts and job completion data

HTTP serving and queue consumption must be deployable as separate processes.

### SDK

Technology: TypeScript compiled to browser JavaScript.

Responsibilities:

- one canonical public initialization API
- product/variant and storefront-session context
- safe widget/iframe mounting
- origin-checked events and lifecycle management
- versioned release artifacts for merchant installation

### PostgreSQL

PostgreSQL is the system of record and may remain the MVP job queue using
`FOR UPDATE SKIP LOCKED`, provided leases, heartbeats, retries and recovery are
implemented. A managed queue can replace job transport later without changing
domain contracts.

### Object storage

MinIO is for local S3-compatible development. Production uses managed
S3-compatible object storage, signed access, lifecycle rules and CDN delivery.
Artifact keys and asset manifests are immutable and version-addressed.

## The two mandatory pipelines

### 1. Garment ingestion pipeline

Ingestion happens before a shopper requests a try-on.

```text
catalog connector or merchant upload
              |
              v
safe intake, validation and immutable raw asset
              |
              v
classification and segmentation
              |
              v
canonical garment archetype selection
              |
              v
measurements, deformation parameters and texture preparation
              |
              v
automated QC and optional merchant review
              |
              v
published immutable GarmentAssetVersion manifest
```

The pipeline is automation-first. Merchant correction is a fallback for low
confidence or failed QC, not the default workflow.

### 2. Try-on rendering pipeline

Runtime consumes only published, prepared assets.

```text
signed storefront session + product/variant + avatar/photo version
              |
              v
render request referencing immutable input versions
              |
              v
load cached SMPL-X/avatar and canonical garment artifacts
              |
              v
pose-aware fitting and structured render
              |
              v
first believable 2.5D preview
              |
              v
optional asynchronous realism enhancement
              |
              v
immutable result + signed/CDN URL + usage event
```

Runtime must not repeat garment classification, segmentation or canonical
asset construction.

## Rendering layers

1. **SMPL-X structural layer** — body geometry, proportions, skeleton and pose.
2. **Garment/render layer** — canonical garment fitting, camera, depth,
   occlusion, materials, lighting, masks and image rendering.
3. **Enhancement layer** — optional skin, face, fabric and compositing polish
   that does not alter product identity.

The first believable render must not wait for maximum enhancement.

## Tenant model

The migration-safe MVP model is:

```text
Account (merchant organization)
  -> Store (commerce installation)
      -> Tenant (security/data partition)
```

Existing `TenantId` columns remain the security boundary. Each Store maps to
one Tenant. Account and store membership determines which tenant-scoped session
a user may obtain. Tenant isolation is enforced with authorization, EF query
filters, composite tenant foreign keys, integration tests and PostgreSQL row
level security before public multi-tenant launch.

## Non-goals for the MVP

- perfect photo-to-3D identity reconstruction
- medical or measurement-grade body scanning
- realtime browser cloth simulation
- full catalog-category coverage
- generating a production 3D garment mesh from every single image
- blocking every interaction on a full diffusion generation
- game-level avatar movement

## Architecture invariants

Before new work is accepted, ask:

1. Is this garment-preparation work or shopper-runtime work?
2. Does it preserve immutable input and output versions?
3. Is every data access tenant-safe by default?
4. Can the first believable result be returned without maximum enhancement?
5. Does the implementation preserve a replaceable provider boundary?
6. Does the feature make the bounded MVP vertical slice more complete?
