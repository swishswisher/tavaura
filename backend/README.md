# Tavaura Backend

This directory contains the Tavaura backend, implemented as a .NET 8 Web API service (`Tavaura.Api`). The API hosts core platform capabilities and serves as the orchestrator for frontend, worker, and SDK integrations.

## Current status

- Built with ASP.NET Core targeting .NET 8
- Exposes a `GET /health` endpoint that reports `{ "status": "ok", "service": "Tavaura.Api" }`

