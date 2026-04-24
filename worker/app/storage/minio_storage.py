import asyncio
import os
from dataclasses import dataclass
from io import BytesIO
from urllib.parse import quote, urlparse

from minio import Minio
from minio.error import S3Error


DEFAULT_MINIO_ENDPOINT = "localhost:9000"
DEFAULT_MINIO_ACCESS_KEY = "tavaura"
DEFAULT_MINIO_SECRET_KEY = "tavaura_storage_secret"
DEFAULT_MINIO_BUCKET = "tavaura-assets"
DEFAULT_MINIO_PUBLIC_BASE_URL = "http://localhost:9000"


class ObjectStorageError(RuntimeError):
    """Raised when worker artifact storage cannot complete an upload."""


@dataclass(frozen=True)
class StoredObject:
    bucket: str
    key: str
    url: str


class MinioAssetStorage:
    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool,
        public_base_url: str,
    ) -> None:
        self._bucket = bucket
        self._public_base_url = public_base_url.rstrip("/")
        self._client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

    @classmethod
    def from_environment(cls) -> "MinioAssetStorage":
        raw_endpoint = os.getenv("MINIO_ENDPOINT", DEFAULT_MINIO_ENDPOINT)
        endpoint, endpoint_secure = _normalize_endpoint(raw_endpoint)
        secure = _read_bool(os.getenv("MINIO_SECURE"), endpoint_secure)

        return cls(
            endpoint=endpoint,
            access_key=os.getenv("MINIO_ACCESS_KEY", DEFAULT_MINIO_ACCESS_KEY),
            secret_key=os.getenv("MINIO_SECRET_KEY", DEFAULT_MINIO_SECRET_KEY),
            bucket=os.getenv("MINIO_BUCKET", DEFAULT_MINIO_BUCKET),
            secure=secure,
            public_base_url=os.getenv(
                "MINIO_PUBLIC_BASE_URL",
                DEFAULT_MINIO_PUBLIC_BASE_URL,
            ),
        )

    async def upload_bytes(
        self,
        *,
        key: str,
        content: bytes,
        content_type: str,
    ) -> StoredObject:
        if not key or not key.strip():
            raise ObjectStorageError("MinIO object key is required.")

        if not content:
            raise ObjectStorageError(f"MinIO upload content is empty for {key}.")

        return await asyncio.to_thread(
            self._upload_bytes_sync,
            key,
            content,
            content_type,
        )

    def _upload_bytes_sync(
        self,
        key: str,
        content: bytes,
        content_type: str,
    ) -> StoredObject:
        try:
            self._ensure_bucket()
            self._client.put_object(
                self._bucket,
                key,
                BytesIO(content),
                length=len(content),
                content_type=content_type,
            )
        except S3Error as exc:
            raise ObjectStorageError(
                f"MinIO upload failed for {self._bucket}/{key}: {exc.code} {exc.message}"
            ) from exc
        except Exception as exc:
            raise ObjectStorageError(
                f"MinIO upload failed for {self._bucket}/{key}: {exc}"
            ) from exc

        return StoredObject(
            bucket=self._bucket,
            key=key,
            url=f"{self._public_base_url}/{self._bucket}/{quote(key, safe='/')}",
        )

    def _ensure_bucket(self) -> None:
        if self._client.bucket_exists(self._bucket):
            return

        try:
            self._client.make_bucket(self._bucket)
        except S3Error as exc:
            if exc.code in {"BucketAlreadyExists", "BucketAlreadyOwnedByYou"}:
                return

            raise


def _normalize_endpoint(raw_endpoint: str) -> tuple[str, bool]:
    parsed = urlparse(raw_endpoint)
    if parsed.scheme and parsed.netloc:
        return parsed.netloc, parsed.scheme == "https"

    return raw_endpoint, False


def _read_bool(raw_value: str | None, default: bool) -> bool:
    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "on"}

