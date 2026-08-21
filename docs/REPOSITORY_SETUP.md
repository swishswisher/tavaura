# Repository setup

This document defines what a clean Tavaura checkout needs and which files belong in Git.

## Prerequisites

- .NET SDK matching the repository-root `global.json`
- Node.js and npm versions compatible with the frontend and SDK package manifests
- Python matching `.python-version`
- Docker with Compose for local PostgreSQL and MinIO infrastructure

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
dotnet test backend/Tavaura.sln --no-restore
```

Backend PostgreSQL integration tests run automatically when
`TAVAURA_TEST_ADMIN_CONNECTION` is set. The target database is reset, so always
use a disposable database and never point this variable at development or
production data. CI provisions its own PostgreSQL 16.14 service and treats a
missing connection as a failure. Without the variable, only the fast unit suite
runs locally and the PostgreSQL tests report explicit skips.

Install Python dependencies into separate project-specific virtual environments:

```powershell
python -m venv worker/.venv-runtime
worker/.venv-runtime/Scripts/python.exe -m pip install -r worker/requirements-runtime.txt

python -m venv worker/.venv-rnd
worker/.venv-rnd/Scripts/python.exe -m pip install -r worker/requirements-rnd.txt
```

The runtime environment contains only the API, queue, storage, HTTP and image-processing dependencies. The R&D environment contains the heavier SMPL-X, Torch, mesh and offline-rendering toolchain. Do not install the R&D file in the production worker image.

## Runtime services

The local infrastructure stack is defined in `docker-compose.yml`. The API and worker are run separately during development. Environment-specific secrets belong in local environment files or a secret manager and must not be committed.

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
dotnet test backend/Tavaura.sln
npm --prefix frontend ci
npm --prefix frontend test
npm --prefix frontend run lint
npm --prefix frontend run build
npm --prefix sdk ci
npm --prefix sdk run build
python -m unittest discover -s worker/tests -v
python -m compileall worker/app worker/tests
```

Worker topology and calibration tests may require separately provisioned licensed model assets. Those tests must report a clear skip or provisioning error when assets are absent rather than silently substituting a different production pipeline.
