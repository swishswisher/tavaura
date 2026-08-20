# ADR-0005: SMPL-X Structure and Progressive Rendering

Status: **Accepted**

Date: **2026-08-20**

## Context

Pillow-based compositing enabled an early end-to-end job demonstration but does
not provide the structural consistency or realism required by the product.
SMPL-X research now provides controllable body geometry, archetypes and poses,
but it is not connected to the runtime renderer.

## Decision

The production rendering path uses three replaceable layers:

1. SMPL-X body/pose structure.
2. Canonical garment fitting and deterministic rendering of colour, alpha,
   depth, normals and semantic masks.
3. Optional asynchronous enhancement for near-real finish.

The first believable structured preview is returned before maximum enhancement.
The existing provider interface is retained and a real SMPL-X provider replaces
the mock provider in production.

## Rationale

- SMPL-X gives repeatable morphology and pose control.
- Structured render buffers allow reliable occlusion and conditioned enhancement.
- Progressive delivery optimizes time to first believable result.
- A provider boundary permits renderer/model improvements without changing API
  or job contracts.

## Consequences

- SMPL-X is a structural model, not a complete renderer.
- Pillow may remain a utility for thumbnails but not the try-on engine.
- Avatar, pose, garment and renderer/model versions must be immutable inputs.
- Caching and precomputation are required for the target runtime latency.
