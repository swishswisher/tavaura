import asyncio
from dataclasses import dataclass
from io import BytesIO

import requests
from PIL import Image


DEFAULT_DOWNLOAD_TIMEOUT_SECONDS = 30


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
    except Exception as e:
        raise Exception(f"Image processing failed: {str(e)}")


def _download_image_sync(image_url: str) -> DownloadedImage:
    try:
        response = requests.get(
            image_url,
            timeout=DEFAULT_DOWNLOAD_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise BackgroundRemovalError(f"Failed to download garment image: {exc}") from exc

    if response.status_code != requests.codes.ok:
        raise BackgroundRemovalError(
            f"Failed to download garment image: HTTP {response.status_code}."
        )

    content = response.content
    if not content:
        raise BackgroundRemovalError("Downloaded garment image is empty.")

    content_type = response.headers.get("Content-Type", "application/octet-stream").strip()
    return DownloadedImage(content=content, content_type=content_type)
