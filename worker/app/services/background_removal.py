import asyncio
import os
from dataclasses import dataclass

import requests


DEFAULT_REMOVE_BG_API_URL = "https://api.remove.bg/v1.0/removebg"
DEFAULT_DOWNLOAD_TIMEOUT_SECONDS = 30
DEFAULT_REMOVE_BG_TIMEOUT_SECONDS = 60


class BackgroundRemovalError(RuntimeError):
    """Raised when garment background removal cannot complete."""


@dataclass(frozen=True)
class DownloadedImage:
    content: bytes
    content_type: str


async def download_image(image_url: str) -> DownloadedImage:
    return await asyncio.to_thread(_download_image_sync, image_url)


async def removeBackground(imageBuffer: bytes) -> bytes:
    # TODO: Replace this temporary external API integration with a local background removal model.
    return await asyncio.to_thread(_remove_background_sync, imageBuffer)


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


def _remove_background_sync(image_buffer: bytes) -> bytes:
    api_key = _read_remove_bg_api_key()
    api_url = os.getenv("REMOVE_BG_API_URL", DEFAULT_REMOVE_BG_API_URL).strip()

    if not api_key:
        raise BackgroundRemovalError(
            "Remove.bg API key is required. Set REMOVE_BG_API_KEY, RemoveBg__ApiKey, or RemoveBg:ApiKey."
        )

    if not image_buffer:
        raise BackgroundRemovalError("Background removal input image is empty.")

    files = {
        "image_file": ("garment-source.png", image_buffer, "application/octet-stream"),
    }
    data = {
        "size": "auto",
        "format": "png",
    }
    headers = {
        "X-Api-Key": api_key,
    }

    try:
        response = requests.post(
            api_url,
            files=files,
            data=data,
            headers=headers,
            timeout=DEFAULT_REMOVE_BG_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise BackgroundRemovalError(f"Background removal API request failed: {exc}") from exc

    if response.status_code != requests.codes.ok:
        body = response.text.strip()
        detail = body[:500] if body else "No response body."
        raise BackgroundRemovalError(
            f"Background removal API failed: HTTP {response.status_code}. {detail}"
        )

    if not response.content:
        raise BackgroundRemovalError("Background removal API returned an empty image.")

    return response.content


def _read_remove_bg_api_key() -> str:
    return (
        os.getenv("REMOVE_BG_API_KEY", "").strip()
        or os.getenv("RemoveBg__ApiKey", "").strip()
        or os.getenv("RemoveBg:ApiKey", "").strip()
    )
