# Tavaura Backend

This directory contains the Tavaura backend, implemented as a .NET 8 Web API service (`Tavaura.Api`). The API hosts core platform capabilities and serves as the orchestrator for frontend, worker, and SDK integrations.

## Current status

- Built with ASP.NET Core targeting .NET 8
- Exposes a `GET /health` endpoint that reports `{ "status": "ok", "service": "Tavaura.Api" }`

## Pipeline Data Model

The backend schema now includes foundational pipeline tables for ingestion and rendering lifecycles:

- `IngestionJob` tracks asynchronous garment ingestion states (`pending`, `processing`, `review_required`, `completed`, `failed`).
- `GarmentAsset` stores canonical processed garment assets generated from ingestion.
- `AssetVersion` versions processed garment assets over time.
- `RenderJob` tracks shopper try-on render states (`pending`, `processing`, `completed`, `failed`).
- `RenderResult` stores generated runtime output URLs for completed render jobs.

Flow summary:

`IngestionJob` -> `GarmentAsset` -> versioned by `AssetVersion`  
`RenderJob` -> produces `RenderResult`

