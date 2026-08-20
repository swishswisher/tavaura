from io import BytesIO

from PIL import Image

from app.services.safe_image_download import (
    DownloadedImage,
    SafeImageDownloadError,
    download_image as safe_download_image,
)

class BackgroundRemovalError(RuntimeError):
    """Raised when garment background removal cannot complete."""


async def download_image(image_url: str) -> DownloadedImage:
    try:
        return await safe_download_image(image_url)
    except SafeImageDownloadError as exc:
        raise BackgroundRemovalError(str(exc)) from exc


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
