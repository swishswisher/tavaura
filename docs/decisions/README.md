# Tavaura Architecture Decision Records

These records are the canonical decisions for continued development. They were
reconciled from the complete seven-conversation project history and the local
checkout on 2026-08-20.

## Decision precedence

1. A newer **Accepted** ADR supersedes an older conflicting ADR or chat answer.
2. ADRs describe intended direction.
3. [CURRENT_STATE.md](../CURRENT_STATE.md) describes actual implementation.
4. Code and tests are evidence of implementation, not automatic evidence that
   an experimental or legacy behavior is still the desired architecture.

## Status meanings

- **Accepted** — binding unless deliberately superseded by a new ADR.
- **Proposed** — under consideration and not binding.
- **Superseded** — retained as history but no longer controlling.

## Accepted records

- [ADR-0001: 2.5D near-realistic MVP](0001-2-5d-near-realistic-mvp.md)
- [ADR-0002: Separate ingestion and runtime pipelines](0002-separate-ingestion-and-runtime.md)
- [ADR-0003: Component and technology boundaries](0003-component-and-technology-boundaries.md)
- [ADR-0004: Canonical garment before automated ingestion](0004-canonical-garment-first.md)
- [ADR-0005: SMPL-X structure and progressive rendering](0005-smplx-and-progressive-rendering.md)
- [ADR-0006: Tenant and merchant ownership boundary](0006-tenant-and-ownership-boundary.md)
- [ADR-0007: MVP jobs, storage and immutable versions](0007-jobs-storage-and-versioning.md)
- [ADR-0008: One SDK-first storefront integration](0008-sdk-first-storefront-integration.md)
- [ADR-0009: Commercial model and dataset rights](0009-commercial-model-and-data-rights.md)

## Required ADR practice

Create a new ADR before making a change that alters any of the following:

- the 2.5D versus realtime-3D product direction
- the ingestion/runtime boundary
- the system-of-record or queue strategy
- the tenant security boundary
- the canonical SDK public contract
- model/dataset licensing assumptions
- MVP scope or launch gates

Do not edit an accepted ADR to conceal a changed decision. Add a new ADR that
states what it supersedes and why.
