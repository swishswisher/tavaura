# ADR-0009: Commercial Model and Dataset Rights

Status: **Accepted**

Date: **2026-08-20**

## Context

The R&D workspace includes SMPL/SMPL-X assets and legacy research code.
Project discussions also considered research datasets such as DeepFashion.
Research availability does not automatically grant commercial product rights.

## Decision

- Commercial launch requires written confirmation of rights for every model,
  dataset and bundled asset in the production pipeline.
- Full SMPL-X model/software is treated as non-commercial until an appropriate
  commercial licence is obtained or a commercially usable replacement is
  approved.
- DeepFashion and similarly restricted datasets are research/internal only
  unless a documented commercial licence permits the intended use.
- The long-term production dataset comes from merchant-consented catalogs,
  user-consented processing and properly licensed synthetic/proprietary data.
- Model weights and licensed source assets are not committed to ordinary Git or
  distributed through the public SDK.

## Consequences

- Licensing is an MVP launch gate.
- Every asset/version manifest records provenance and licence classification.
- A technically successful model cannot enter production without legal review.
- Removing model files from Git history and defining secure model provisioning
  are part of repository hardening.
