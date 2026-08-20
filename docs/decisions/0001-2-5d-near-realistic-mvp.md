# ADR-0001: 2.5D Near-Realistic MVP

Status: **Accepted**

Date: **2026-08-20**

## Context

Earlier project conversations alternated between static layered images, a
realtime browser 3D viewer and full photo-to-3D reconstruction. The later work
established a more coherent target: use true 3D structure internally while
optimizing the shopper-visible result for realism, speed and ecommerce use.

## Decision

The MVP produces **2.5D near-realistic images and short motion clips backed by
true 3D human and garment infrastructure**.

It supports:

- reusable parameter-based avatars
- a bounded photo-based try-on path
- body and pose consistency from SMPL-X
- canonical garment fitting
- a fast structured preview
- optional progressive realism enhancement

The MVP does not require a publicly exposed realtime 3D viewer. Three.js may be
used for internal inspection or a deliberately approved viewer feature, but it
is not the definition of the try-on engine and realtime cloth physics is out of
scope.

## Rationale

- Near-real rendered output is more persuasive for fashion ecommerce than raw
  avatar geometry.
- True 3D structure improves repeatability across bodies, garments and poses.
- 2.5D delivery is more compatible with mobile devices and embedded storefronts.
- Precomputation and progressive output reduce latency and GPU cost.
- The approach preserves a path to richer 3D without blocking the MVP on full
  reconstruction or physics research.

## Consequences

- Marketing must not claim perfect digital twins or exact fit.
- Visual quality must be measured on rendered output, not only mesh topology.
- The frontend may present images/clips even though the underlying system is 3D.
- Static Pillow overlays remain development mocks, not the final engine.

## Supersedes

This decision supersedes older chat statements that either static pre-rendered
asset lookup alone or a fully interactive realtime 3D viewer defines the MVP.
