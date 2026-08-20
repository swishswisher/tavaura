import os

import asyncpg


DEVELOPMENT_POSTGRES_DSN = (
    "postgresql://tavaura:tavaura_password@localhost:5433/tavaura_dev"
)


async def _configure_worker_connection(connection: asyncpg.Connection) -> None:
    await connection.execute(
        """
        SELECT set_config('app.is_worker', 'true', false),
               set_config('app.is_platform', 'false', false),
               set_config('app.tenant_id', '', false)
        """
    )


async def create_pool() -> asyncpg.Pool:
    dsn = os.getenv("TAVAURA_POSTGRES_DSN")
    if not dsn:
        if os.getenv("TAVAURA_ENVIRONMENT", "development").lower() != "development":
            raise RuntimeError("TAVAURA_POSTGRES_DSN is required outside development.")
        dsn = DEVELOPMENT_POSTGRES_DSN

    return await asyncpg.create_pool(
        dsn=dsn,
        min_size=1,
        max_size=5,
        setup=_configure_worker_connection,
    )
