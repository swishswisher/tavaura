import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape

import asyncpg

from app.services.background_removal import download_image, process_image_bytes
from app.storage.minio_storage import MinioAssetStorage, StoredObject


LOGGER = logging.getLogger("tavaura.worker.ingestion")
POLL_INTERVAL_SECONDS = 1
PROCESSING_DELAY_SECONDS = 2
PLACEHOLDER_PROCESSING_MODEL = "ingestion-skeleton-v1"
PLACEHOLDER_CONTENT_TYPE = "image/svg+xml"
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
                WHERE "GarmentAssetId" = $1
                """,
                garment_asset_id,
            )

            await connection.execute(
                """
                INSERT INTO "AssetVersions"
                    ("Id", "GarmentAssetId", "VersionNumber", "ProcessingModel", "CreatedAt")
                VALUES
                    ($1, $2, $3, $4, $5)
                """,
                uuid.uuid4(),
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
    mask_content = _build_placeholder_mask_svg(job, garment_id, source_image_url)
    texture_content = _build_placeholder_texture_svg(job, garment_id, source_image_url)

    mask_object = await storage.upload_bytes(
        key=f"{base_key}/mask.svg",
        content=mask_content,
        content_type=PLACEHOLDER_CONTENT_TYPE,
    )
    texture_object = await storage.upload_bytes(
        key=f"{base_key}/texture.svg",
        content=texture_content,
        content_type=PLACEHOLDER_CONTENT_TYPE,
    )

    return processed_image_object, mask_object, texture_object


def _build_placeholder_mask_svg(
    job: ClaimedIngestionJob,
    garment_id: uuid.UUID,
    source_image_url: str,
) -> bytes:
    metadata = _build_svg_metadata(job, garment_id, source_image_url)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <title>Tavaura placeholder garment mask</title>
  <desc>{metadata}</desc>
  <rect width="512" height="512" fill="#050505"/>
  <ellipse cx="256" cy="250" rx="150" ry="212" fill="#ffffff"/>
  <rect x="164" y="366" width="184" height="82" rx="36" fill="#ffffff"/>
  <text x="256" y="486" text-anchor="middle" font-family="Arial, sans-serif" font-size="26" fill="#ffffff">placeholder mask</text>
</svg>
""".encode("utf-8")


def _build_placeholder_texture_svg(
    job: ClaimedIngestionJob,
    garment_id: uuid.UUID,
    source_image_url: str,
) -> bytes:
    metadata = _build_svg_metadata(job, garment_id, source_image_url)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <title>Tavaura placeholder garment texture</title>
  <desc>{metadata}</desc>
  <defs>
    <pattern id="checker" width="64" height="64" patternUnits="userSpaceOnUse">
      <rect width="64" height="64" fill="#d8c7ff"/>
      <rect width="32" height="32" fill="#7c3aed"/>
      <rect x="32" y="32" width="32" height="32" fill="#7c3aed"/>
    </pattern>
  </defs>
  <rect width="512" height="512" fill="url(#checker)"/>
  <path d="M118 88h276l-44 344H162L118 88Z" fill="#f8fafc" fill-opacity="0.58"/>
  <text x="256" y="486" text-anchor="middle" font-family="Arial, sans-serif" font-size="26" fill="#111827">placeholder texture</text>
</svg>
""".encode("utf-8")


def _build_svg_metadata(
    job: ClaimedIngestionJob,
    garment_id: uuid.UUID,
    source_image_url: str,
) -> str:
    return escape(
        (
            f"job_id={job.id}; tenant_id={job.tenant_id}; "
            f"garment_id={garment_id}; source_image_url={source_image_url}"
        ),
        quote=True,
    )


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
