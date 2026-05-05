import asyncio
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlparse

import asyncpg

from app.rendering.base import RenderProvider, RenderProviderResult, RenderRequest
from app.rendering.mock_provider import MockRenderProvider
from app.storage.minio_storage import MinioAssetStorage, StoredObject


LOGGER = logging.getLogger("tavaura.worker.render")
POLL_INTERVAL_SECONDS = 1
SIMULATED_WORK_SECONDS = 2
RENDER_PROVIDER_ENV = "RENDER_PROVIDER"
DEFAULT_RENDER_PROVIDER = "mock"


@dataclass(frozen=True)
class ClaimedRenderJob:
    id: uuid.UUID
    tenant_id: uuid.UUID
    avatar_id: uuid.UUID
    garment_asset_id: uuid.UUID
    asset_version_id: uuid.UUID


@dataclass(frozen=True)
class AvatarRenderInput:
    id: uuid.UUID
    user_id: uuid.UUID
    tenant_id: uuid.UUID | None
    source: str
    person_image_url: str | None
    height_cm: float
    weight_kg: float
    gender: str
    skin_tone: str
    display_name: str | None


@dataclass(frozen=True)
class GarmentRenderInput:
    id: uuid.UUID
    tenant_id: uuid.UUID
    garment_id: uuid.UUID
    external_product_id: str
    name: str
    source_image_url: str
    processed_image_url: str
    processed_mask_url: str
    processed_texture_url: str
    latest_asset_version_id: uuid.UUID
    latest_version_number: int


@dataclass(frozen=True)
class RenderInputs:
    avatar: AvatarRenderInput
    garment: GarmentRenderInput


async def run_render_worker(pool: asyncpg.Pool) -> None:
    storage = MinioAssetStorage.from_environment()
    render_provider = _create_render_provider()

    while True:
        job: ClaimedRenderJob | None = None

        try:
            job = await _claim_pending_render_job(pool)
            if job is None:
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                continue

            LOGGER.info("Processing render job %s", job.id)
            await _process_render_job(pool, job, storage, render_provider)
            LOGGER.info("Completed render job %s", job.id)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if job is not None:
                await _fail_render_job(pool, job.id, str(exc))

            LOGGER.exception("Render worker loop failed")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def _claim_pending_render_job(pool: asyncpg.Pool) -> ClaimedRenderJob | None:
    async with pool.acquire() as connection:
        async with connection.transaction():
            row = await connection.fetchrow(
                """
                SELECT "Id", "TenantId", "AvatarId", "GarmentAssetId", "AssetVersionId"
                FROM "RenderJobs"
                WHERE "Status" = 'pending'
                ORDER BY "CreatedAt"
                FOR UPDATE SKIP LOCKED
                LIMIT 1
                """
            )

            if row is None:
                return None

            now = datetime.now(UTC)

            await connection.execute(
                """
                UPDATE "RenderJobs"
                SET "Status" = 'processing',
                    "StartedAt" = COALESCE("StartedAt", $2),
                    "UpdatedAt" = $2,
                    "AttemptCount" = "AttemptCount" + 1,
                    "ErrorMessage" = NULL
                WHERE "Id" = $1
                """,
                row["Id"],
                now,
            )

            return ClaimedRenderJob(
                id=row["Id"],
                tenant_id=row["TenantId"],
                avatar_id=row["AvatarId"],
                garment_asset_id=row["GarmentAssetId"],
                asset_version_id=row["AssetVersionId"],
            )


async def _process_render_job(
    pool: asyncpg.Pool,
    job: ClaimedRenderJob,
    storage: MinioAssetStorage,
    render_provider: RenderProvider,
) -> None:
    _validate_render_job(job)
    await asyncio.sleep(SIMULATED_WORK_SECONDS)

    render_inputs = await _load_render_inputs(pool, job)
    render_result = await render_provider.render(_build_render_request(job, render_inputs))
    output_object, preview_object = await _upload_render_outputs(
        storage,
        job,
        render_result,
    )

    await _store_render_result_and_complete_job(
        pool,
        job.id,
        output_object.url,
        preview_object.url,
    )


def _create_render_provider() -> RenderProvider:
    provider_name = os.getenv(RENDER_PROVIDER_ENV, DEFAULT_RENDER_PROVIDER).strip().lower()
    if provider_name == "mock":
        return MockRenderProvider()

    raise ValueError(f"Unsupported {RENDER_PROVIDER_ENV}: {provider_name}")


def _validate_render_job(job: ClaimedRenderJob) -> None:
    if job.tenant_id is None:
        raise ValueError("Render job is missing TenantId.")

    if job.avatar_id is None:
        raise ValueError("Render job is missing AvatarId.")

    if job.garment_asset_id is None:
        raise ValueError("Render job is missing GarmentAssetId.")

    if job.asset_version_id is None:
        raise ValueError("Render job is missing AssetVersionId.")


async def _load_render_inputs(
    pool: asyncpg.Pool,
    job: ClaimedRenderJob,
) -> RenderInputs:
    async with pool.acquire() as connection:
        avatar = await _load_avatar_input(connection, job)
        garment = await _load_garment_input(connection, job)

    return RenderInputs(avatar=avatar, garment=garment)


async def _load_avatar_input(
    connection: asyncpg.Connection,
    job: ClaimedRenderJob,
) -> AvatarRenderInput:
    row = await connection.fetchrow(
        """
        SELECT a."Id",
               a."UserId",
               a."TenantId",
               a."Source",
               a."HeightCm",
               a."WeightKg",
               a."Gender",
               a."SkinTone",
               u."DisplayName"
        FROM "Avatars" a
        LEFT JOIN "Users" u ON u."Id" = a."UserId"
        WHERE a."Id" = $1
        LIMIT 1
        """,
        job.avatar_id,
    )

    if row is None:
        raise ValueError("Avatar does not exist for render job.")

    if row["TenantId"] is not None and row["TenantId"] != job.tenant_id:
        raise ValueError("Avatar does not belong to the render job tenant.")

    source = row["Source"] or ""
    person_image_url = source if _looks_like_url(source) else None

    return AvatarRenderInput(
        id=row["Id"],
        user_id=row["UserId"],
        tenant_id=row["TenantId"],
        source=source,
        person_image_url=person_image_url,
        height_cm=float(row["HeightCm"]),
        weight_kg=float(row["WeightKg"]),
        gender=row["Gender"] or "",
        skin_tone=row["SkinTone"] or "",
        display_name=row["DisplayName"],
    )


async def _load_garment_input(
    connection: asyncpg.Connection,
    job: ClaimedRenderJob,
) -> GarmentRenderInput:
    row = await connection.fetchrow(
        """
        SELECT ga."Id",
               ga."TenantId",
               ga."GarmentId",
               ga."SourceImageUrl",
               ga."ProcessedImageUrl",
               ga."ProcessedMaskUrl",
               ga."ProcessedTextureUrl",
               g."ExternalProductId",
               g."Name",
               requested_av."Id" AS "RequestedAssetVersionId",
               latest_av."Id" AS "LatestAssetVersionId",
               latest_av."VersionNumber" AS "LatestVersionNumber"
        FROM "GarmentAssets" ga
        JOIN "Garments" g ON g."Id" = ga."GarmentId"
        LEFT JOIN "AssetVersions" requested_av
          ON requested_av."Id" = $3
         AND requested_av."GarmentAssetId" = ga."Id"
        JOIN LATERAL (
            SELECT "Id", "VersionNumber"
            FROM "AssetVersions"
            WHERE "GarmentAssetId" = ga."Id"
            ORDER BY "VersionNumber" DESC
            LIMIT 1
        ) latest_av ON true
        WHERE ga."Id" = $1
          AND ga."TenantId" = $2
        LIMIT 1
        """,
        job.garment_asset_id,
        job.tenant_id,
        job.asset_version_id,
    )

    if row is None:
        raise ValueError("Garment asset or asset version does not exist for render job.")

    if row["RequestedAssetVersionId"] is None:
        raise ValueError("Render job AssetVersionId is not linked to the garment asset.")

    if not row["ProcessedImageUrl"] or not str(row["ProcessedImageUrl"]).strip():
        raise ValueError("Garment asset is missing ProcessedImageUrl.")

    if not row["ProcessedMaskUrl"] or not str(row["ProcessedMaskUrl"]).strip():
        raise ValueError("Garment asset is missing ProcessedMaskUrl.")

    if not row["ProcessedTextureUrl"] or not str(row["ProcessedTextureUrl"]).strip():
        raise ValueError("Garment asset is missing ProcessedTextureUrl.")

    return GarmentRenderInput(
        id=row["Id"],
        tenant_id=row["TenantId"],
        garment_id=row["GarmentId"],
        external_product_id=row["ExternalProductId"] or "",
        name=row["Name"] or "",
        source_image_url=row["SourceImageUrl"] or "",
        processed_image_url=row["ProcessedImageUrl"],
        processed_mask_url=row["ProcessedMaskUrl"],
        processed_texture_url=row["ProcessedTextureUrl"],
        latest_asset_version_id=row["LatestAssetVersionId"],
        latest_version_number=int(row["LatestVersionNumber"]),
    )


def _build_render_request(
    job: ClaimedRenderJob,
    render_inputs: RenderInputs,
) -> RenderRequest:
    avatar = render_inputs.avatar
    garment = render_inputs.garment

    return RenderRequest(
        job_id=job.id,
        tenant_id=job.tenant_id,
        avatar_id=avatar.id,
        user_id=avatar.user_id,
        person_image_url=avatar.person_image_url,
        avatar_source=avatar.source,
        avatar_height_cm=avatar.height_cm,
        avatar_weight_kg=avatar.weight_kg,
        avatar_gender=avatar.gender,
        avatar_skin_tone=avatar.skin_tone,
        avatar_display_name=avatar.display_name or "",
        garment_asset_id=garment.id,
        garment_id=garment.garment_id,
        external_product_id=garment.external_product_id,
        garment_name=garment.name,
        garment_source_image_url=garment.source_image_url,
        garment_processed_image_url=garment.processed_image_url,
        requested_asset_version_id=job.asset_version_id,
        latest_asset_version_id=garment.latest_asset_version_id,
        latest_version_number=garment.latest_version_number,
        mask_url=garment.processed_mask_url,
        texture_url=garment.processed_texture_url,
    )


async def _upload_render_outputs(
    storage: MinioAssetStorage,
    job: ClaimedRenderJob,
    render_result: RenderProviderResult,
) -> tuple[StoredObject, StoredObject]:
    output_object = await storage.upload_bytes(
        key=f"renders/{job.id}.png",
        content=render_result.output.content,
        content_type=render_result.output.content_type,
    )
    LOGGER.info("Uploaded render output %s", output_object.url)
    preview_object = await storage.upload_bytes(
        key=f"renders/{job.id}-preview.png",
        content=render_result.preview.content,
        content_type=render_result.preview.content_type,
    )

    return output_object, preview_object


async def _store_render_result_and_complete_job(
    pool: asyncpg.Pool,
    job_id: uuid.UUID,
    output_url: str,
    preview_url: str,
) -> None:
    async with pool.acquire() as connection:
        async with connection.transaction():
            now = datetime.now(UTC)
            existing_result_id = await connection.fetchval(
                """
                SELECT "Id"
                FROM "RenderResults"
                WHERE "RenderJobId" = $1
                ORDER BY "CreatedAt" DESC
                LIMIT 1
                """,
                job_id,
            )

            if existing_result_id is None:
                await connection.execute(
                    """
                    INSERT INTO "RenderResults"
                        ("Id", "RenderJobId", "OutputImageUrl", "PreviewImageUrl", "CreatedAt")
                    VALUES
                        ($1, $2, $3, $4, $5)
                    """,
                    uuid.uuid4(),
                    job_id,
                    output_url,
                    preview_url,
                    now,
                )
            else:
                await connection.execute(
                    """
                    UPDATE "RenderResults"
                    SET "OutputImageUrl" = $2,
                        "PreviewImageUrl" = $3,
                        "CreatedAt" = $4
                    WHERE "Id" = $1
                    """,
                    existing_result_id,
                    output_url,
                    preview_url,
                    now,
                )

            await connection.execute(
                """
                UPDATE "RenderJobs"
                SET "Status" = 'completed',
                    "CompletedAt" = $2,
                    "UpdatedAt" = $2,
                    "ErrorMessage" = NULL
                WHERE "Id" = $1
                """,
                job_id,
                now,
            )


def _looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


async def _fail_render_job(pool: asyncpg.Pool, job_id: uuid.UUID, error_message: str) -> None:
    async with pool.acquire() as connection:
        now = datetime.now(UTC)
        await connection.execute(
            """
            UPDATE "RenderJobs"
            SET "Status" = 'failed',
                "ErrorMessage" = $2,
                "CompletedAt" = $3,
                "UpdatedAt" = $3
            WHERE "Id" = $1
            """,
            job_id,
            error_message[:2000],
            now,
        )
