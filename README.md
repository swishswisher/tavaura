# Tavaura — giving aura to your avatar

Tavaura is a virtual try-on platform for apparel and cosmetics that brings photorealistic garment and makeup previews to any brand experience. Brands can embed Tavaura inside their storefronts to let shoppers visualize outfits, accessories, and looks on personalized avatars generated from photos. The platform is designed to be flexible enough for enterprise retailers while still easy to integrate for boutiques and marketplace sellers.

## Repository structure

- rontend/: Next.js marketing site and interactive viewer UI
- ackend/: Multi-tenant .NET 8 Web API handling sessions, catalog, and integrations
- worker/: Python FastAPI services for ML processing and media pipelines
- sdk/: Lightweight embeddable JavaScript loader and integration helpers for client sites
- shared/: Common DTOs, validation schemas, and configuration contracts
- 	ests/: End-to-end and integration test harnesses
- docs/: Architecture decision records, diagrams, and other documentation

