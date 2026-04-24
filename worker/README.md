# Tavaura Worker

This service is the Python background worker for Tavaura.

It preserves the two-pipeline architecture:

- ingestion jobs are polled and processed separately
- render jobs are polled and processed separately

No ML or real image processing is implemented in this scaffold.

## Folder structure

```text
worker/
  app/
    main.py
    db/
      connection.py
    jobs/
      ingestion_worker.py
      render_worker.py
  requirements.txt
  README.md
```

## Local run

1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Start the worker:
   - `uvicorn app.main:app --reload --port 8001`

## Runtime behavior

- `GET /health` returns worker health.
- On startup, the service starts:
  - an ingestion polling loop for `"IngestionJobs"`
  - a render polling loop for `"RenderJobs"`

Each loop:
- fetches one `pending` job
- marks it `processing`
- simulates work for 2 seconds
- marks it `completed`
