# Repository setup

This document defines what a clean Tavaura checkout needs and which files belong in Git.

## Prerequisites

- .NET SDK matching the repository-root `global.json`
- Node.js and npm versions compatible with the frontend and SDK package manifests
- Python matching the worker container/runtime
- Docker with Compose for PostgreSQL, MinIO, the API, and the worker

Use committed lockfiles for JavaScript installs:

```powershell
Set-Location frontend
npm ci

Set-Location ..\sdk
npm ci
```

Restore and build the API from the repository root:

```powershell
dotnet restore backend/Tavaura.sln
dotnet build backend/Tavaura.sln --no-restore
```

Install Python dependencies into a project-specific virtual environment. The current dependency split is documented in `worker/requirements.txt`; Phase 1 will separate runtime dependencies from research and calibration tooling.

## Runtime services

The local stack is defined in `docker-compose.yml`. Environment-specific secrets belong in local environment files or a secret manager and must not be committed.

## Models and licensed assets

Large model files and third-party licensed assets are deliberately not stored in Git. In particular, SMPL-X body-model files must be obtained under the upstream licence and placed in the configured local model directory. Production distribution remains blocked until the commercial-use licences for every model and dataset have been recorded and approved.

The Marvelous Designer source project at `worker/avatar_pipeline/smplx/assets/tvra.zprj` is project source and remains tracked.

## Generated files

The following are reproducible outputs and are ignored:

- `.next`, `node_modules`, `bin`, `obj`, and `.buildcheck` build directories
- `worker/avatar_pipeline/**/output*` research, calibration, render, and fitting results
- local model directories, caches, logs, and environment files

R&D scripts and fixtures remain tracked; their generated outputs do not. Removing generated files from the Git index does not erase them from an existing working copy and does not rewrite prior Git history.

## Clean-checkout verification

Before accepting a Phase 1 checkpoint, verify:

```powershell
dotnet build backend/Tavaura.sln
npm --prefix frontend ci
npm --prefix frontend run build
npm --prefix sdk ci
npm --prefix sdk run build
python -m compileall worker/app
```

Worker topology and calibration tests may require separately provisioned licensed model assets. Those tests must report a clear skip or provisioning error when assets are absent rather than silently substituting a different production pipeline.
