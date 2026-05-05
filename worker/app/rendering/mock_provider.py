import asyncio
import logging
from io import BytesIO

import requests
from PIL import Image, ImageDraw

from app.rendering.base import RenderArtifact, RenderProviderResult, RenderRequest


PNG_CONTENT_TYPE = "image/png"
DOWNLOAD_TIMEOUT_SECONDS = 30
LOGGER = logging.getLogger("tavaura.worker.render")


class MockRenderProvider:
    async def render(self, request: RenderRequest) -> RenderProviderResult:
        return await asyncio.to_thread(_render_sync, request)


def _render_sync(request: RenderRequest) -> RenderProviderResult:
    avatar = _load_avatar_image(request.person_image_url)
    garment = _download_image(request.garment_processed_image_url, "garment")
    output = _compose_try_on(avatar, garment)
    output_bytes = _save_png(output)
    preview_bytes = _build_preview(output)

    return RenderProviderResult(
        output=RenderArtifact(
            filename="output.png",
            content=output_bytes,
            content_type=PNG_CONTENT_TYPE,
        ),
        preview=RenderArtifact(
            filename="preview.png",
            content=preview_bytes,
            content_type=PNG_CONTENT_TYPE,
        ),
    )


def _load_avatar_image(person_image_url: str | None) -> Image.Image:
    if person_image_url:
        return _download_image(person_image_url, "avatar")

    LOGGER.info("Using generated default avatar image")
    LOGGER.info("Downloaded avatar image")
    return _build_default_avatar()


def _download_image(image_url: str, label: str) -> Image.Image:
    if not image_url or not image_url.strip():
        raise ValueError(f"{label.title()} image URL is required.")

    try:
        response = requests.get(image_url, timeout=DOWNLOAD_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to download {label} image: {exc}") from exc

    if response.status_code != requests.codes.ok:
        raise RuntimeError(f"Failed to download {label} image: HTTP {response.status_code}.")

    if not response.content:
        raise RuntimeError(f"Downloaded {label} image is empty.")

    try:
        image = Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception as exc:
        raise RuntimeError(f"Downloaded {label} image is not a valid image: {exc}") from exc

    LOGGER.info("Downloaded %s image", label)
    return image


def _build_default_avatar() -> Image.Image:
    image = Image.new("RGBA", (800, 1200), "#f6f1eb")
    draw = ImageDraw.Draw(image)

    draw.ellipse((330, 120, 470, 260), fill="#d8ad8d")
    draw.rounded_rectangle((275, 270, 525, 710), radius=105, fill="#d8ad8d")
    draw.polygon(((300, 690), (500, 690), (575, 1100), (225, 1100)), fill="#c79879")
    draw.rounded_rectangle((210, 320, 310, 760), radius=50, fill="#d8ad8d")
    draw.rounded_rectangle((490, 320, 590, 760), radius=50, fill="#d8ad8d")
    draw.rounded_rectangle((245, 1080, 380, 1180), radius=45, fill="#bd8f72")
    draw.rounded_rectangle((420, 1080, 555, 1180), radius=45, fill="#bd8f72")

    return image


def _compose_try_on(avatar: Image.Image, garment: Image.Image) -> Image.Image:
    base = _flatten_on_neutral_background(avatar)
    garment_width = int(base.width * 0.62)
    garment = _resize_to_width(garment, garment_width)

    max_garment_height = int(base.height * 0.56)
    if garment.height > max_garment_height:
        garment.thumbnail((garment.width, max_garment_height), Image.Resampling.LANCZOS)

    x = (base.width - garment.width) // 2
    y = int(base.height * 0.28)
    base.alpha_composite(garment, (x, y))
    return base


def _resize_to_width(image: Image.Image, width: int) -> Image.Image:
    if width <= 0:
        raise ValueError("Target garment width must be greater than zero.")

    ratio = width / image.width
    height = max(1, int(image.height * ratio))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def _flatten_on_neutral_background(image: Image.Image) -> Image.Image:
    background = Image.new("RGBA", image.size, "#f8f5f0")
    background.alpha_composite(image.convert("RGBA"))
    return background


def _build_preview(output: Image.Image) -> bytes:
    preview = output.copy()
    preview.thumbnail((512, 512), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (512, 512), "#f8f5f0")
    x = (canvas.width - preview.width) // 2
    y = (canvas.height - preview.height) // 2
    canvas.alpha_composite(preview, (x, y))
    return _save_png(canvas)


def _save_png(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
