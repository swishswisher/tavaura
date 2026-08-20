# Tavaura — giving aura to your avatar

Tavaura is a multi-tenant virtual try-on platform for fashion ecommerce.

The MVP is built around **2.5D near-realistic output backed by true 3D human
infrastructure**. SMPL-X supplies structured body geometry and pose; canonical
garments are fitted to that structure; the shopper receives fast rendered and
composited images, followed by optional progressive realism enhancement.

## Repository structure

- `frontend/`: Next.js marketing site, merchant administration and shopper UI
- `backend/`: multi-tenant ASP.NET Core control plane and system of record
- `worker/`: Python ingestion, rendering and offline SMPL-X/garment research
- `sdk/`: standalone embeddable storefront SDK
- `shared/`: reserved for stable cross-language contracts
- `tests/`: reserved for cross-service integration and end-to-end tests
- `docs/`: canonical product, architecture and delivery documentation

## Canonical project documents

These files supersede conflicting or outdated plans from earlier development
conversations:

- [Current implementation state](docs/CURRENT_STATE.md)
- [Repository setup and clean-checkout contract](docs/REPOSITORY_SETUP.md)
- [MVP definition of done](docs/MVP_DEFINITION_OF_DONE.md)
- [Implementation roadmap](docs/IMPLEMENTATION_ROADMAP.md)
- [Architecture overview](docs/architecture-overview.md)
- [Decision records](docs/decisions/README.md)

When code, an old document and a decision record disagree, treat the newest
accepted decision record as the intended direction and `CURRENT_STATE.md` as
the description of what is actually implemented.
