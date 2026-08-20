import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO

import asyncpg
from PIL import Image, ImageDraw

from app.services.background_removal import download_image, process_image_bytes
from app.storage.minio_storage import MinioAssetStorage, StoredObject


LOGGER = logging.getLogger("tavaura.worker.ingestion")
POLL_INTERVAL_SECONDS = 1
PROCESSING_DELAY_SECONDS = 2
PLACEHOLDER_PROCESSING_MODEL = "ingestion-skeleton-v1"
PLACEHOLDER_CONTENT_TYPE = "image/png"
PROCESSED_IMAGE_CONTENT_TYPE = "image/png"


@dataclass(frozen=True)
class ClaimedIngestionJob:
    id: uuid.UUID
    tenant_id: uuid.UUID
    external_product_id: str


async def run_ingestion_worker(pool: asyncpg.Pool) -> None:
    storage = MinioAssetStorage.from_environment()

    while True:
        job: ClaimedIngestionJob | None = None

        try:
            job = await _claim_pending_ingestion_job(pool)
            if job is None:
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                continue

            LOGGER.info("Processing ingestion job %s", job.id)
            await _process_ingestion_job(pool, job, storage)
            LOGGER.info("Completed ingestion job %s", job.id)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if job is not None:
                await _fail_ingestion_job(pool, job.id, str(exc))

            LOGGER.exception("Ingestion worker loop failed")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def _claim_pending_ingestion_job(pool: asyncpg.Pool) -> ClaimedIngestionJob | None:
    async with pool.acquire() as connection:
        async with connection.transaction():
            row = await connection.fetchrow(
                """
                SELECT "Id", "TenantId", "ExternalProductId"
                FROM "IngestionJobs"
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
                UPDATE "IngestionJobs"
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

            return ClaimedIngestionJob(
                id=row["Id"],
                tenant_id=row["TenantId"],
                external_product_id=row["ExternalProductId"],
            )


async def _process_ingestion_job(
    pool: asyncpg.Pool,
    job: ClaimedIngestionJob,
    storage: MinioAssetStorage,
) -> None:
    if job.tenant_id is None:
        raise ValueError("Ingestion job is missing TenantId.")

    if not job.external_product_id or not job.external_product_id.strip():
        raise ValueError("Ingestion job is missing ExternalProductId.")

    await asyncio.sleep(PROCESSING_DELAY_SECONDS)

    garment = await _get_garment_for_ingestion(pool, job)
    source_image_url = garment["SourceImageUrl"]
    if not source_image_url or not str(source_image_url).strip():
        raise ValueError("Garment is missing SourceImageUrl.")

    downloaded_source_image = await download_image(source_image_url)
    downloaded_image_bytes = downloaded_source_image.content
    print(f"[INGESTION] Downloaded image size: {len(downloaded_image_bytes)} bytes")
    processed_bytes = process_image_bytes(downloaded_image_bytes)
    print(f"[INGESTION] Processed image size: {len(processed_bytes)} bytes")

    processed_image_object, mask_object, texture_object = await _upload_ingestion_assets(
        storage,
        job,
        garment["Id"],
        source_image_url,
        processed_bytes,
    )

    async with pool.acquire() as connection:
        async with connection.transaction():
            garment_asset = await connection.fetchrow(
                """
                SELECT "Id", "ProcessedImageUrl"
                FROM "GarmentAssets"
                WHERE "TenantId" = $1 AND "GarmentId" = $2
                ORDER BY "CreatedAt"
                LIMIT 1
                """,
                job.tenant_id,
                garment["Id"],
            )

            now = datetime.now(UTC)
            if garment_asset is None:
                garment_asset_id = uuid.uuid4()
                processed_image_url = processed_image_object.url if processed_image_object is not None else None
                await connection.execute(
                    """
                    INSERT INTO "GarmentAssets"
                        ("Id", "TenantId", "GarmentId", "AssetType", "SourceImageUrl",
                         "ProcessedImageUrl", "ProcessedMaskUrl", "ProcessedTextureUrl",
                         "ConfidenceScore", "CreatedAt")
                    VALUES
                        ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                    garment_asset_id,
                    job.tenant_id,
                    garment["Id"],
                    "front",
                    source_image_url,
                    processed_image_url,
                    mask_object.url,
                    texture_object.url,
                    0.5,
                    now,
                )
                if processed_image_url:
                    LOGGER.info("Saved ProcessedImageUrl: %s", processed_image_url)
            else:
                garment_asset_id = garment_asset["Id"]
                processed_image_url = (
                    processed_image_object.url
                    if processed_image_object is not None
                    else garment_asset["ProcessedImageUrl"]
                )
                await connection.execute(
                    """
                    UPDATE "GarmentAssets"
                    SET "SourceImageUrl" = $2,
                        "ProcessedImageUrl" = $3,
                        "ProcessedMaskUrl" = $4,
                        "ProcessedTextureUrl" = $5,
                        "ConfidenceScore" = $6
                    WHERE "Id" = $1
                    """,
                    garment_asset_id,
                    source_image_url,
                    processed_image_url,
                    mask_object.url,
                    texture_object.url,
                    0.5,
                )
                if processed_image_url:
                    LOGGER.info("Saved ProcessedImageUrl: %s", processed_image_url)

            next_version_number = await connection.fetchval(
                """
                SELECT COALESCE(MAX("VersionNumber"), 0) + 1
                FROM "AssetVersions"
                WHERE "TenantId" = $1 AND "GarmentAssetId" = $2
                """,
                job.tenant_id,
                garment_asset_id,
            )

            await connection.execute(
                """
                INSERT INTO "AssetVersions"
                    ("Id", "TenantId", "GarmentAssetId", "VersionNumber", "ProcessingModel", "CreatedAt")
                VALUES
                    ($1, $2, $3, $4, $5, $6)
                """,
                uuid.uuid4(),
                job.tenant_id,
                garment_asset_id,
                next_version_number,
                PLACEHOLDER_PROCESSING_MODEL,
                now,
            )

            await connection.execute(
                """
                UPDATE "IngestionJobs"
                SET "Status" = 'completed',
                    "CompletedAt" = $2,
                    "UpdatedAt" = $2
                WHERE "Id" = $1
                """,
                job.id,
                now,
            )


async def _get_garment_for_ingestion(
    pool: asyncpg.Pool,
    job: ClaimedIngestionJob,
) -> asyncpg.Record:
    async with pool.acquire() as connection:
        garment = await connection.fetchrow(
            """
            SELECT "Id", "SourceImageUrl"
            FROM "Garments"
            WHERE "TenantId" = $1 AND "ExternalProductId" = $2
              AND "IsDeleted" = FALSE
            LIMIT 1
            """,
            job.tenant_id,
            job.external_product_id,
        )

    if garment is None:
        raise ValueError("No Garment found for the ingestion job tenant/product.")

    return garment


async def _upload_ingestion_assets(
    storage: MinioAssetStorage,
    job: ClaimedIngestionJob,
    garment_id: uuid.UUID,
    source_image_url: str,
    processed_image_content: bytes | None,
) -> tuple[StoredObject | None, StoredObject, StoredObject]:
    base_key = f"ingestion/{job.tenant_id}/{job.id}"
    processed_image_object: StoredObject | None = None
    if processed_image_content is not None:
        try:
            LOGGER.info("Uploading processed image...")
            LOGGER.info("Uploading processed image for garment %s", garment_id)
            processed_image_object = await storage.upload_bytes(
                key=f"processed/{garment_id}.png",
                content=processed_image_content,
                content_type=PROCESSED_IMAGE_CONTENT_TYPE,
            )
            LOGGER.info("Uploaded processed image for garment %s: %s", garment_id, processed_image_object.url)
        except Exception:
            LOGGER.exception("Processed image upload failed for garment %s", garment_id)
    mask_content = _build_placeholder_mask_png()
    texture_content = _build_placeholder_texture_png()

    mask_object = await storage.upload_bytes(
        key=f"{base_key}/mask.png",
        content=mask_content,
        content_type=PLACEHOLDER_CONTENT_TYPE,
    )
    texture_object = await storage.upload_bytes(
        key=f"{base_key}/texture.png",
        content=texture_content,
        content_type=PLACEHOLDER_CONTENT_TYPE,
    )

    return processed_image_object, mask_object, texture_object


def _build_placeholder_mask_png() -> bytes:
    image = Image.new("RGBA", (512, 512), "#050505")
    draw = ImageDraw.Draw(image)
    draw.ellipse((106, 38, 406, 462), fill="#ffffff")
    draw.rounded_rectangle((164, 366, 348, 448), radius=36, fill="#ffffff")
    return _save_png(image)


def _build_placeholder_texture_png() -> bytes:
    image = Image.new("RGBA", (512, 512), "#f8fafc")
    draw = ImageDraw.Draw(image)

    for y in range(0, 512, 64):
        for x in range(0, 512, 64):
            color = "#f4efe7" if (x + y) // 64 % 2 == 0 else "#d9c6aa"
            draw.rectangle((x, y, x + 63, y + 63), fill=color)

    draw.polygon(((118, 88), (394, 88), (350, 432), (162, 432)), fill="#ffffff99")
    return _save_png(image)


def _save_png(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


async def _fail_ingestion_job(pool: asyncpg.Pool, job_id: uuid.UUID, error_message: str) -> None:
    async with pool.acquire() as connection:
        now = datetime.now(UTC)
        await connection.execute(
            """
            UPDATE "IngestionJobs"
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
