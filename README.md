# Tavaura — giving aura to your avatar

Tavaura is a multi-tenant virtual try-on platform for fashion ecommerce.

The MVP is built around **2.5D near-realistic output backed by true 3D human
infrastructure**. SMPL-X supplies structured body geometry and pose; canonical
garments are fitted to that structure; the shopper receives fast rendered and
composited images, followed by optional progressive realism enhancement.

## Repository structure

- rontend/: Next.js marketing site and interactive viewer UI
- ackend/: Multi-tenant .NET 8 Web API handling sessions, catalog, and integrations
- worker/: Python FastAPI services for ML processing and media pipelines
- sdk/: Lightweight embeddable JavaScript loader and integration helpers for client sites
- shared/: Common DTOs, validation schemas, and configuration contracts
- 	ests/: End-to-end and integration test harnesses
- docs/: Architecture decision records, diagrams, and other documentation

