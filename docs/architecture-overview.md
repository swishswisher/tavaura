# Tavaura Architecture Overview

Tavaura is organized as a modular platform so each surface can independently evolve while sharing a common contract layer. The frontend app is built on Next.js 15 with Tailwind CSS to power both the marketing site and a high-fidelity viewer experience that runs in the browser. It consumes shared DTOs for catalog items, avatars, and sessions to remain closely aligned with backend capabilities.

The backend is a multi-tenant .NET 8 Web API responsible for authentication, catalog ingestion, fitting room sessions, analytics, and integrations with commerce platforms. It exposes REST and webhook endpoints to orchestrate try-on workflows and dispatch long-running jobs to the worker tier.

The worker services are Python FastAPI applications wrapping ML pipelines for background removal, 2D-to-3D garment reconstruction, photo-to-avatar generation, and cosmetics simulation. Workers run asynchronously, stream progress back to the backend, and populate asset storage for the viewer.

The sdk is a small JavaScript loader that storefronts embed on platforms like Shopify, WooCommerce, Squarespace, Wix, and bespoke sites. It mounts the viewer iframe or Web Components, handles authentication tokens, and provides hooks for commerce events.

Shared DTOs, validation schemas, and configuration live in the shared workspace to keep data contracts synchronized across languages. The tests workspace centralizes end-to-end and integration tests that span the frontend, backend, worker, and SDK workflows to guard the full try-on funnel.

