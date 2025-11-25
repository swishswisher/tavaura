# Contributing to Tavaura

Tavaura is organized as a monorepo with dedicated workspaces for the frontend (Next.js marketing site and viewer), backend (.NET Web API), worker (Python ML services), sdk (JavaScript loader and client tools), shared (types, schemas, and configuration), and tests (end-to-end and integration flows). Each workspace owns its tooling but shares conventions documented below.

## Coding style

- **Frontend**: TypeScript + React with Next.js 15, Tailwind, and modern linting/prettier defaults.
- **Backend**: C# targeting .NET 8, following async-first patterns, nullable reference types, and analyzers.
- **Worker**: Python with FastAPI, type hints, and Black/ruff formatting standards.
- **SDK**: Lightweight TypeScript targeting evergreen browsers, published as ES modules.

## Staged delivery

All new work must align with the staged build plan (Stage A, Stage B, etc.), ensuring every stage remains small, testable, and reviewable before advancing. Please reference docs/stage-plan.md when planning features or submitting pull requests.

