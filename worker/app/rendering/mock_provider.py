import asyncio
import logging
from collections import deque
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageFilter

from app.rendering.base import RenderArtifact, RenderProviderResult, RenderRequest
from app.services.safe_image_download import SafeImageDownloadError, download_image_sync


PNG_CONTENT_TYPE = "image/png"
NEAR_WHITE_THRESHOLD = 235
NEAR_WHITE_CHROMA_LIMIT = 30
LAYER_ORDER = {
    "innerwear": 10,
    "inner": 10,
    "base": 20,
    "top": 20,
    "upper": 20,
    "shirt": 20,
    "tshirt": 20,
    "t-shirt": 20,
    "hoodie": 28,
    "full-body": 30,
    "dress": 30,
    "outerwear": 40,
    "outer": 40,
    "jacket": 40,
    "coat": 40,
    "accessory": 50,
}
OUTER_LAYER_KEYS = {"outerwear", "outer", "jacket", "coat"}
AVATAR_COMPONENT_DIR = Path(__file__).resolve().parents[2] / "assets" / "avatar-components"
AVATAR_COMPONENT_ORDER = ("legs", "arms", "torsos", "heads", "hair")
AVATAR_ASSET_DIR = Path(__file__).resolve().parents[2] / "assets" / "avatars"
DEFAULT_AVATAR_ASSETS = {
    "male": "male.png",
    "female": "female.png",
    "neutral": "neutral.png",
}
LOGGER = logging.getLogger("tavaura.worker.render")


@dataclass(frozen=True)
class RenderGarmentLayer:
    image: Image.Image
    layer: str
    name: str = ""


@dataclass(frozen=True)
class AvatarAssemblyParameters:
    gender: str = "neutral"
    body_type: str = "standard"
    skin_tone: str = "default"
    hairstyle: str = "default"
    height_scale: float = 1.0
    weight_scale: float = 1.0


class MockRenderProvider:
    async def render(self, request: RenderRequest) -> RenderProviderResult:
        return await asyncio.to_thread(_render_sync, request)


def _render_sync(request: RenderRequest) -> RenderProviderResult:
    LOGGER.info("Using NEW render pipeline (Pillow PNG)")
    avatar = _load_avatar_image(request)
    garment = download_render_image(request.garment_processed_image_url, "garment")
    output = composite_multiple_garments(
        avatar,
        (
            RenderGarmentLayer(
                image=preprocess_garment_image(garment),
                layer=request.garment_layer,
                name=request.garment_name,
            ),
        ),
    )
    output_bytes = _save_png(output)
    preview_bytes = generate_preview(output)

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


def _load_avatar_image(request: RenderRequest) -> Image.Image:
    if request.person_image_url:
        return download_render_image(request.person_image_url, "avatar")

    parameters = _build_avatar_parameters(request)
    return assemble_avatar_from_parameters(parameters)


def assemble_avatar_from_parameters(parameters: AvatarAssemblyParameters) -> Image.Image:
    LOGGER.info(
        "Assembling default avatar from components: gender=%s body_type=%s skin_tone=%s hairstyle=%s height_scale=%.3f weight_scale=%.3f",
        parameters.gender,
        parameters.body_type,
        parameters.skin_tone,
        parameters.hairstyle,
        parameters.height_scale,
        parameters.weight_scale,
    )

    try:
        canvas = Image.new("RGBA", (800, 1200), (0, 0, 0, 0))
        for component in AVATAR_COMPONENT_ORDER:
            canvas.alpha_composite(load_avatar_component(parameters, component))

        return _apply_avatar_body_scaling(canvas, parameters)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError("Failed to assemble default avatar from components.") from exc


def load_avatar_component(
    parameters: AvatarAssemblyParameters,
    component: str,
) -> Image.Image:
    component_path = resolve_avatar_component_path(parameters, component)

    try:
        image = Image.open(component_path).convert("RGBA")
    except FileNotFoundError as exc:
        raise RuntimeError(f"Avatar component is missing: {component_path}") from exc
    except Exception as exc:
        raise RuntimeError(f"Avatar component is not a readable PNG: {component_path}") from exc

    if image.size != (800, 1200):
        raise RuntimeError(f"Avatar component must be 800x1200: {component_path}")

    return image


def resolve_avatar_component_path(
    parameters: AvatarAssemblyParameters,
    component: str,
) -> Path:
    component = component.strip().lower()
    if component not in AVATAR_COMPONENT_ORDER:
        raise RuntimeError(f"Unsupported avatar component: {component}")

    variants = _avatar_component_variants(parameters, component)
    genders = (parameters.gender, "neutral") if parameters.gender != "neutral" else ("neutral",)

    for gender in genders:
        for variant in variants:
            path = AVATAR_COMPONENT_DIR / gender / component / f"{variant}.png"
            if path.exists():
                return path

    raise RuntimeError(
        f"No avatar component found for gender={parameters.gender}, component={component}, variants={variants}."
    )


def _build_avatar_parameters(request: RenderRequest) -> AvatarAssemblyParameters:
    gender = _resolve_avatar_asset_key(
        gender=request.avatar_gender,
        avatar_source=request.avatar_source,
    )
    body_type = _infer_body_type(
        height_cm=request.avatar_height_cm,
        weight_kg=request.avatar_weight_kg,
    )

    return AvatarAssemblyParameters(
        gender=gender,
        body_type=body_type,
        skin_tone=_normalize_avatar_variant(request.avatar_skin_tone),
        hairstyle=_resolve_default_hairstyle(gender),
        height_scale=_calculate_height_scale(request.avatar_height_cm),
        weight_scale=_calculate_weight_scale(
            request.avatar_height_cm,
            request.avatar_weight_kg,
            body_type,
        ),
    )


def _avatar_component_variants(
    parameters: AvatarAssemblyParameters,
    component: str,
) -> tuple[str, ...]:
    if component == "hair":
        return _dedupe_variants((parameters.hairstyle, "default"))

    if component == "torsos":
        return _dedupe_variants((parameters.body_type, parameters.skin_tone, "default"))

    return _dedupe_variants((parameters.skin_tone, "default"))


def _dedupe_variants(values: tuple[str, ...]) -> tuple[str, ...]:
    variants: list[str] = []
    for value in values:
        variant = _normalize_avatar_variant(value)
        if variant not in variants:
            variants.append(variant)

    return tuple(variants)


def _normalize_avatar_variant(value: str | None) -> str:
    normalized = (value or "").strip().lower().replace("_", "-").replace(" ", "-")
    return normalized or "default"


def _resolve_default_hairstyle(gender: str) -> str:
    if gender == "female":
        return "long"

    if gender == "male":
        return "cropped"

    return "short"


def _infer_body_type(height_cm: float, weight_kg: float) -> str:
    if height_cm <= 0 or weight_kg <= 0:
        return "standard"

    height_m = height_cm / 100
    bmi = weight_kg / (height_m * height_m)
    if bmi < 20:
        return "slim"

    if bmi > 27:
        return "broad"

    return "standard"


def _calculate_height_scale(height_cm: float) -> float:
    if height_cm <= 0:
        return 1.0

    return _clamp_float(height_cm / 172, 0.94, 1.08)


def _calculate_weight_scale(height_cm: float, weight_kg: float, body_type: str) -> float:
    if height_cm <= 0 or weight_kg <= 0:
        base_scale = 1.0
    else:
        height_m = height_cm / 100
        bmi = weight_kg / (height_m * height_m)
        base_scale = 1.0 + ((bmi - 23.0) * 0.012)

    body_adjustment = {
        "slim": 0.94,
        "standard": 1.0,
        "broad": 1.07,
    }.get(body_type, 1.0)
    return _clamp_float(base_scale * body_adjustment, 0.90, 1.12)


def _apply_avatar_body_scaling(
    avatar: Image.Image,
    parameters: AvatarAssemblyParameters,
) -> Image.Image:
    bounds = avatar.getchannel("A").getbbox()
    if bounds is None:
        return avatar

    body = avatar.crop(bounds)
    body_width = max(1, int(round(body.width * parameters.weight_scale)))
    body_height = max(1, int(round(body.height * parameters.height_scale)))
    body = body.resize((body_width, body_height), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", avatar.size, (0, 0, 0, 0))
    original_center_x = (bounds[0] + bounds[2]) // 2
    original_bottom = bounds[3]
    x = _clamp(original_center_x - (body_width // 2), 0, avatar.width - body_width)
    y = _clamp(original_bottom - body_height, 0, avatar.height - body_height)
    canvas.alpha_composite(body, (x, y))
    return canvas


def load_default_avatar_asset(
    *,
    gender: str | None,
    avatar_source: str | None,
) -> Image.Image:
    asset_path = resolve_avatar_asset_path(gender=gender, avatar_source=avatar_source)
    LOGGER.info("Loading default avatar asset %s", asset_path)

    try:
        return Image.open(asset_path).convert("RGBA")
    except FileNotFoundError as exc:
        raise RuntimeError(f"Default avatar asset is missing: {asset_path}") from exc
    except Exception as exc:
        raise RuntimeError(f"Default avatar asset is not a readable PNG: {asset_path}") from exc


def resolve_avatar_asset_path(
    *,
    gender: str | None,
    avatar_source: str | None,
) -> Path:
    avatar_key = _resolve_avatar_asset_key(gender=gender, avatar_source=avatar_source)
    return AVATAR_ASSET_DIR / DEFAULT_AVATAR_ASSETS[avatar_key]


def _resolve_avatar_asset_key(
    *,
    gender: str | None,
    avatar_source: str | None,
) -> str:
    values = f"{gender or ''} {avatar_source or ''}".strip().lower()
    if "female" in values or "woman" in values:
        return "female"

    if "male" in values or "man" in values:
        return "male"

    return "neutral"


def download_render_image(image_url: str, label: str) -> Image.Image:
    if not image_url or not image_url.strip():
        raise ValueError(f"{label.title()} image URL is required.")

    try:
        downloaded = download_image_sync(image_url)
        image = Image.open(BytesIO(downloaded.content)).convert("RGBA")
    except (SafeImageDownloadError, OSError) as exc:
        raise RuntimeError(_invalid_image_message(label)) from exc

    LOGGER.info("Downloaded %s image", label)
    return image


def preprocess_garment_image(garment: Image.Image) -> Image.Image:
    cleaned = garment.convert("RGBA")
    cleaned = remove_near_white_background(cleaned)
    cleaned = suppress_hanger_region(cleaned)
    cleaned = _smooth_alpha_edges(cleaned)
    return _crop_to_visible_garment(cleaned)


def remove_near_white_background(garment: Image.Image) -> Image.Image:
    image = garment.copy()
    pixels = image.load()
    width, height = image.size
    visited = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def enqueue_if_background(x: int, y: int) -> None:
        index = y * width + x
        if visited[index]:
            return

        visited[index] = 1
        if _is_near_white_pixel(pixels[x, y]):
            queue.append((x, y))

    for x in range(width):
        enqueue_if_background(x, 0)
        enqueue_if_background(x, height - 1)

    for y in range(1, height - 1):
        enqueue_if_background(0, y)
        enqueue_if_background(width - 1, y)

    while queue:
        x, y = queue.popleft()
        r, g, b, _ = pixels[x, y]
        pixels[x, y] = (r, g, b, 0)

        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if nx < 0 or nx >= width or ny < 0 or ny >= height:
                continue

            index = ny * width + nx
            if visited[index]:
                continue

            visited[index] = 1
            if _is_near_white_pixel(pixels[nx, ny]):
                queue.append((nx, ny))

    return image


def suppress_hanger_region(garment: Image.Image) -> Image.Image:
    image = garment.copy()
    pixels = image.load()
    width, height = image.size
    top_limit = max(1, int(height * 0.16))
    min_x = int(width * 0.32)
    max_x = int(width * 0.68)
    max_component_size = max(24, int(width * height * 0.018))
    max_component_height = int(height * 0.22)
    max_component_width = int(width * 0.24)
    visited = bytearray(width * height)

    for y in range(top_limit):
        for x in range(min_x, max_x):
            index = y * width + x
            if visited[index] or not _is_hanger_candidate_pixel(pixels[x, y]):
                continue

            component = _collect_hanger_component(
                pixels,
                width,
                height,
                visited,
                x,
                y,
                max_component_size + 1,
            )
            if not component:
                continue

            xs = [point[0] for point in component]
            ys = [point[1] for point in component]
            touches_top = min(ys) <= int(height * 0.05)
            component_width = max(xs) - min(xs) + 1
            component_height = max(ys) - min(ys) + 1

            if (
                touches_top
                and len(component) <= max_component_size
                and component_width <= max_component_width
                and component_height <= max_component_height
            ):
                for px, py in component:
                    r, g, b, _ = pixels[px, py]
                    pixels[px, py] = (r, g, b, 0)

    return image


def _collect_hanger_component(
    pixels,
    width: int,
    height: int,
    visited: bytearray,
    start_x: int,
    start_y: int,
    limit: int,
) -> list[tuple[int, int]]:
    component: list[tuple[int, int]] = []
    queue: deque[tuple[int, int]] = deque([(start_x, start_y)])
    visited[start_y * width + start_x] = 1

    while queue:
        x, y = queue.popleft()
        if not _is_hanger_candidate_pixel(pixels[x, y]):
            continue

        component.append((x, y))
        if len(component) > limit:
            return component

        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if nx < 0 or nx >= width or ny < 0 or ny >= height:
                continue

            index = ny * width + nx
            if visited[index]:
                continue

            visited[index] = 1
            if _is_hanger_candidate_pixel(pixels[nx, ny]):
                queue.append((nx, ny))

    return component


def _smooth_alpha_edges(garment: Image.Image) -> Image.Image:
    red, green, blue, alpha = garment.split()
    alpha = alpha.filter(ImageFilter.MedianFilter(size=3))
    alpha = alpha.filter(ImageFilter.GaussianBlur(radius=0.45))
    return Image.merge("RGBA", (red, green, blue, alpha))


def _crop_to_visible_garment(garment: Image.Image, padding: int = 8) -> Image.Image:
    left, top, right, bottom = get_visible_garment_bounds(garment)
    crop_box = (
        max(0, left - padding),
        max(0, top - padding),
        min(garment.width, right + padding),
        min(garment.height, bottom + padding),
    )
    return garment.crop(crop_box)


def _is_near_white_pixel(pixel: tuple[int, int, int, int]) -> bool:
    r, g, b, alpha = pixel
    if alpha <= 8:
        return False

    return (
        r >= NEAR_WHITE_THRESHOLD
        and g >= NEAR_WHITE_THRESHOLD
        and b >= NEAR_WHITE_THRESHOLD
        and max(r, g, b) - min(r, g, b) <= NEAR_WHITE_CHROMA_LIMIT
    )


def _is_hanger_candidate_pixel(pixel: tuple[int, int, int, int]) -> bool:
    r, g, b, alpha = pixel
    if alpha <= 24:
        return False

    brightness = (r + g + b) / 3
    chroma = max(r, g, b) - min(r, g, b)
    return chroma <= 42 and brightness <= 230


def composite_garment_on_avatar(avatar: Image.Image, garment: Image.Image) -> Image.Image:
    return composite_multiple_garments(
        avatar,
        (RenderGarmentLayer(image=garment, layer="upper"),),
    )


def composite_multiple_garments(
    avatar: Image.Image,
    garments: tuple[RenderGarmentLayer, ...] | list[RenderGarmentLayer],
) -> Image.Image:
    base = _flatten_on_neutral_background(avatar)
    sorted_garments = sort_garments_by_layer(garments)
    if not sorted_garments:
        return base

    torso_region = estimate_avatar_torso_region(base)

    for index, garment_layer in enumerate(sorted_garments):
        fitted_garment, position = fit_layered_garment(
            garment_layer,
            base,
            torso_region,
            garment_count=len(sorted_garments),
            layer_index=index,
        )
        _composite_garment_shadow(base, fitted_garment, position)
        _alpha_composite_clipped(base, fitted_garment, position)

    return base


def sort_garments_by_layer(
    garments: tuple[RenderGarmentLayer, ...] | list[RenderGarmentLayer],
) -> list[RenderGarmentLayer]:
    return sorted(
        garments,
        key=lambda garment: (
            _get_layer_order(garment.layer, garment.name),
            garment.name.lower(),
        ),
    )


def fit_layered_garment(
    garment_layer: RenderGarmentLayer,
    avatar: Image.Image,
    torso_region: tuple[int, int, int, int],
    *,
    garment_count: int,
    layer_index: int,
) -> tuple[Image.Image, tuple[int, int]]:
    layer_kind = _normalize_layer_key(garment_layer.layer, garment_layer.name)
    is_outer_layer = garment_count > 1 and layer_kind in OUTER_LAYER_KEYS
    scale_multiplier = 1.07 if is_outer_layer else 1.0
    vertical_offset = int(avatar.height * 0.012 * layer_index)

    fitted_garment = resize_garment_to_avatar(
        garment_layer.image,
        avatar,
        torso_region,
        scale_multiplier=scale_multiplier,
    )
    x, y = calculate_body_fit_position(fitted_garment, avatar, torso_region)
    left, top, right, bottom = get_visible_garment_bounds(fitted_garment)
    y = _clamp(y + vertical_offset, -top, avatar.height - bottom)
    x = _clamp(x, -left, avatar.width - right)
    return fitted_garment, (x, y)


def get_visible_garment_bounds(garment: Image.Image) -> tuple[int, int, int, int]:
    alpha = garment.getchannel("A")
    mask = alpha.point(lambda value: 255 if value > 24 else 0)
    return mask.getbbox() or (0, 0, garment.width, garment.height)


def estimate_avatar_torso_region(avatar: Image.Image) -> tuple[int, int, int, int]:
    width, height = avatar.size
    return (
        int(width * 0.23),
        int(height * 0.265),
        int(width * 0.77),
        int(height * 0.715),
    )


def calculate_body_fit_position(
    garment: Image.Image,
    avatar: Image.Image,
    torso_region: tuple[int, int, int, int],
) -> tuple[int, int]:
    left, top, right, bottom = get_visible_garment_bounds(garment)
    visible_height = bottom - top
    torso_left, torso_top, torso_right, torso_bottom = torso_region
    torso_height = torso_bottom - torso_top

    torso_center_x = (torso_left + torso_right) / 2
    garment_center_x = _estimate_garment_alpha_center_x(garment, (left, top, right, bottom))
    garment_neckline_y = _estimate_garment_neckline_y(garment, (left, top, right, bottom))
    target_neckline_y = torso_top + int(torso_height * 0.035)
    target_neckline_y = _clamp(
        target_neckline_y,
        int(avatar.height * 0.24),
        int(avatar.height * 0.34),
    )

    x = int(round(torso_center_x - garment_center_x))
    y = int(round(target_neckline_y - garment_neckline_y))

    lower_limit = min(avatar.height - 1, torso_bottom + int(avatar.height * 0.10))
    visible_bottom = y + bottom
    if visible_bottom > lower_limit:
        y -= visible_bottom - lower_limit

    upper_limit = int(avatar.height * 0.18)
    visible_top = y + top
    if visible_top < upper_limit:
        y += upper_limit - visible_top

    x = _clamp(x, -left, avatar.width - right)
    y = _clamp(y, -top, avatar.height - bottom)
    return x, y


def resize_garment_to_avatar(
    garment: Image.Image,
    avatar: Image.Image,
    torso_region: tuple[int, int, int, int] | None = None,
    *,
    scale_multiplier: float = 1.0,
) -> Image.Image:
    torso_region = torso_region or estimate_avatar_torso_region(avatar)
    left, top, right, bottom = get_visible_garment_bounds(garment)
    visible_width = max(1, right - left)
    visible_height = max(1, bottom - top)
    shoulder_width = max(1, torso_region[2] - torso_region[0])

    target_visible_width = _calculate_target_garment_width(
        avatar,
        shoulder_width,
        visible_width,
        visible_height,
    )
    target_visible_width = int(target_visible_width * max(0.8, scale_multiplier))
    target_visible_width = min(target_visible_width, int(avatar.width * 0.74))
    max_visible_height = int((torso_region[3] - torso_region[1]) * 1.22)
    scale = min(
        target_visible_width / visible_width,
        max_visible_height / visible_height,
    )
    scale = max(0.05, scale)

    width = max(1, int(round(garment.width * scale)))
    height = max(1, int(round(garment.height * scale)))
    if width <= 0 or height <= 0:
        raise ValueError("Target garment width must be greater than zero.")

    return garment.resize((width, height), Image.Resampling.LANCZOS)


def _estimate_garment_alpha_center_x(
    garment: Image.Image,
    bounds: tuple[int, int, int, int],
) -> float:
    left, top, right, bottom = bounds
    alpha = garment.getchannel("A")
    weighted_sum = 0
    total_weight = 0

    for y in range(top, bottom):
        for x in range(left, right):
            weight = alpha.getpixel((x, y))
            if weight <= 24:
                continue

            weighted_sum += x * weight
            total_weight += weight

    if total_weight == 0:
        return left + ((right - left) / 2)

    return weighted_sum / total_weight


def _estimate_garment_neckline_y(
    garment: Image.Image,
    bounds: tuple[int, int, int, int],
) -> int:
    left, top, right, bottom = bounds
    visible_height = max(1, bottom - top)
    scan_bottom = min(bottom, top + int(visible_height * 0.42))
    alpha = garment.getchannel("A")
    row_widths: list[tuple[int, int]] = []
    max_row_width = 0

    for y in range(top, scan_bottom):
        row_width = 0
        for x in range(left, right):
            if alpha.getpixel((x, y)) > 48:
                row_width += 1

        row_widths.append((y, row_width))
        max_row_width = max(max_row_width, row_width)

    if max_row_width == 0:
        return top + int(visible_height * 0.10)

    shoulder_threshold = max(8, int(max_row_width * 0.46))
    for y, row_width in row_widths:
        if row_width >= shoulder_threshold:
            return y

    return top + int(visible_height * 0.10)


def _calculate_target_garment_width(
    avatar: Image.Image,
    shoulder_width: int,
    visible_width: int,
    visible_height: int,
) -> int:
    aspect_ratio = visible_width / max(1, visible_height)
    shoulder_scale = 1.10
    if aspect_ratio > 0.88:
        shoulder_scale = 1.02
    elif aspect_ratio < 0.52:
        shoulder_scale = 1.14

    target_width = int(shoulder_width * shoulder_scale)
    target_width = min(target_width, int(avatar.width * 0.70))
    return max(int(avatar.width * 0.34), target_width)


def _get_layer_order(layer: str, name: str) -> int:
    return LAYER_ORDER.get(_normalize_layer_key(layer, name), 30)


def _normalize_layer_key(layer: str, name: str) -> str:
    value = f"{layer} {name}".strip().lower()
    for key in LAYER_ORDER:
        if key in value:
            return key

    return layer.strip().lower() or name.strip().lower()


def _composite_garment_shadow(
    base: Image.Image,
    garment: Image.Image,
    position: tuple[int, int],
) -> None:
    alpha = garment.getchannel("A").filter(ImageFilter.GaussianBlur(radius=5))
    shadow_alpha = alpha.point(lambda value: min(42, int(value * 0.18)))
    shadow = Image.new("RGBA", garment.size, (24, 20, 17, 0))
    shadow.putalpha(shadow_alpha)
    _alpha_composite_clipped(base, shadow, (position[0] + 2, position[1] + 5))


def _alpha_composite_clipped(
    base: Image.Image,
    overlay: Image.Image,
    position: tuple[int, int],
) -> None:
    x, y = position
    left = max(0, x)
    top = max(0, y)
    right = min(base.width, x + overlay.width)
    bottom = min(base.height, y + overlay.height)

    if left >= right or top >= bottom:
        return

    crop_box = (left - x, top - y, right - x, bottom - y)
    base.alpha_composite(overlay.crop(crop_box), (left, top))


def _clamp(value: int, minimum: int, maximum: int) -> int:
    if minimum > maximum:
        return minimum

    return max(minimum, min(maximum, value))


def _clamp_float(value: float, minimum: float, maximum: float) -> float:
    if minimum > maximum:
        return minimum

    return max(minimum, min(maximum, value))


def _flatten_on_neutral_background(image: Image.Image) -> Image.Image:
    background = Image.new("RGBA", image.size, "#f8f5f0")
    background.alpha_composite(image.convert("RGBA"))
    return background


def generate_preview(output: Image.Image) -> bytes:
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


def _invalid_image_message(label: str) -> str:
    if label == "avatar":
        return "Avatar image is not a valid image. Please use a direct JPG, PNG, or WebP image URL."

    return "Garment image is not a valid image. Rebuild ingestion with a direct JPG, PNG, or WebP image URL."
