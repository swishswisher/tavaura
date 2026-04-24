import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.connection import create_pool
from app.jobs.ingestion_worker import run_ingestion_worker
from app.jobs.render_worker import run_render_worker


logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    pool = await create_pool()
    ingestion_task = asyncio.create_task(run_ingestion_worker(pool))
    render_task = asyncio.create_task(run_render_worker(pool))

    try:
        yield
    finally:
        ingestion_task.cancel()
        render_task.cancel()
        await asyncio.gather(ingestion_task, render_task, return_exceptions=True)
        await pool.close()


app = FastAPI(
    title="Tavaura Worker",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "tavaura-worker",
    }

