# ADR-0004: Validate a Canonical Garment Before Automated Ingestion

Status: **Accepted**

Date: **2026-08-20**

## Context

Testing catalog-image segmentation, garment construction, fitting and rendering
at the same time creates too many unknowns. Earlier procedural garments proved
topology and binding concepts but did not reach commercial garment quality.

## Decision

Finish one known-good canonical T-shirt in Marvelous Designer, then prove it
across the bounded SMPL-X body/pose matrix before completing automated catalog
ingestion.

The order is:

```text
known-good canonical garment
  -> fitting validation
  -> rendering validation
  -> real ingestion/classification
  -> archetype selection and deformation
```

## Rationale

- isolates garment-fitting risk from media-processing risk
- provides a trusted reference for QC and renderer development
- creates stable landmarks, semantic regions and export conventions
- avoids treating single-image 3D garment generation as an MVP dependency

## Consequences

- The current Marvelous Designer T-shirt is the immediate R&D milestone.
- Ingestion target design may be documented, but implementation must not derail
  canonical-garment validation.
- Additional garment families wait until the T-shirt vertical slice passes.
