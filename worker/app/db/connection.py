import asyncpg


POSTGRES_DSN = (
    "postgresql://tavaura:tavaura_password@localhost:5433/tavaura_dev"
)


async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=POSTGRES_DSN,
        min_size=1,
        max_size=5,
    )
