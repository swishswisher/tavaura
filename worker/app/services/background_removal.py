import asyncio
import logging
from dataclasses import dataclass
from io import BytesIO

import requests
from PIL import Image, features


DEFAULT_DOWNLOAD_TIMEOUT_SECONDS = 30
VALID_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png"}
if features.check("webp"):
    VALID_IMAGE_CONTENT_TYPES.add("image/webp")
INVALID_SOURCE_IMAGE_MESSAGE = (
    "Downloaded source is not a valid image. Please use a direct JPG, PNG, or WebP image URL."
)
LOGGER = logging.getLogger("tavaura.worker.background_removal")


class BackgroundRemovalError(RuntimeError):
    """Raised when garment background removal cannot complete."""


@dataclass(frozen=True)
class DownloadedImage:
    content: bytes
    content_type: str


async def download_image(image_url: str) -> DownloadedImage:
    return await asyncio.to_thread(_download_image_sync, image_url)


def process_image_bytes(image_bytes: bytes) -> bytes:
    try:
        input_stream = BytesIO(image_bytes)

        img = Image.open(input_stream)
        img = img.convert("RGBA")

        output_stream = BytesIO()
        img.save(output_stream, format="PNG")

        return output_stream.getvalue()
    except Exception as exc:
        raise BackgroundRemovalError(
            "Image processing failed because the source file is not a readable image."
        ) from exc


def _download_image_sync(image_url: str) -> DownloadedImage:
    LOGGER.info("Downloading source garment image: %s", image_url)

    try:
        response = requests.get(
            image_url,
            timeout=DEFAULT_DOWNLOAD_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise BackgroundRemovalError(f"Failed to download garment image: {exc}") from exc

    raw_content_type = response.headers.get("Content-Type", "")
    content_type = raw_content_type.split(";", 1)[0].strip().lower()
    content = response.content

    LOGGER.info(
        "Downloaded source image response: url=%s status=%s content_type=%s byte_size=%s",
        image_url,
        response.status_code,
        raw_content_type or "missing",
        len(content),
    )

    if response.status_code != requests.codes.ok:
        raise BackgroundRemovalError(
            f"Failed to download garment image: HTTP {response.status_code}."
        )

    if not content:
        raise BackgroundRemovalError(INVALID_SOURCE_IMAGE_MESSAGE)

    if content_type not in VALID_IMAGE_CONTENT_TYPES:
        raise BackgroundRemovalError(INVALID_SOURCE_IMAGE_MESSAGE)

    _validate_image_content(content)
    return DownloadedImage(content=content, content_type=content_type)


def _validate_image_content(content: bytes) -> None:
    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
    except Exception as exc:
        raise BackgroundRemovalError(INVALID_SOURCE_IMAGE_MESSAGE) from exc
