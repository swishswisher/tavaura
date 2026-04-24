from html import escape

from app.rendering.base import RenderArtifact, RenderProviderResult, RenderRequest


PLACEHOLDER_CONTENT_TYPE = "image/svg+xml"
PLACEHOLDER_RENDER_MODEL = "render-skeleton-v1"


class MockRenderProvider:
    async def render(self, request: RenderRequest) -> RenderProviderResult:
        return RenderProviderResult(
            output=RenderArtifact(
                filename="output.svg",
                content=_build_placeholder_output_svg(request),
                content_type=PLACEHOLDER_CONTENT_TYPE,
            ),
            preview=RenderArtifact(
                filename="preview.svg",
                content=_build_placeholder_preview_svg(request),
                content_type=PLACEHOLDER_CONTENT_TYPE,
            ),
        )


def _build_placeholder_output_svg(request: RenderRequest) -> bytes:
    metadata = _build_svg_metadata(request)
    label = escape(request.garment_name or request.external_product_id)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="768" height="1024" viewBox="0 0 768 1024">
  <title>Tavaura placeholder try-on output</title>
  <desc>{metadata}</desc>
  <rect width="768" height="1024" fill="#f8fafc"/>
  <rect x="96" y="80" width="576" height="864" rx="44" fill="#ffffff" stroke="#d1d5db" stroke-width="4"/>
  <circle cx="384" cy="206" r="74" fill="#f4c7a1"/>
  <path d="M278 346c28-54 184-54 212 0l58 362c8 50-30 96-82 96H302c-52 0-90-46-82-96l58-362Z" fill="#7c3aed" fill-opacity="0.88"/>
  <path d="M296 374c44 36 132 36 176 0" fill="none" stroke="#f8fafc" stroke-width="16" stroke-linecap="round"/>
  <rect x="230" y="836" width="308" height="38" rx="19" fill="#111827" fill-opacity="0.16"/>
  <text x="384" y="924" text-anchor="middle" font-family="Arial, sans-serif" font-size="30" fill="#111827">placeholder try-on render</text>
  <text x="384" y="966" text-anchor="middle" font-family="Arial, sans-serif" font-size="20" fill="#4b5563">{label}</text>
</svg>
""".encode("utf-8")


def _build_placeholder_preview_svg(request: RenderRequest) -> bytes:
    metadata = _build_svg_metadata(request)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <title>Tavaura placeholder try-on preview</title>
  <desc>{metadata}</desc>
  <rect width="512" height="512" fill="#111827"/>
  <circle cx="256" cy="138" r="52" fill="#f4c7a1"/>
  <path d="M170 246c22-42 150-42 172 0l38 168H132l38-168Z" fill="#7c3aed"/>
  <path d="M190 268c32 24 100 24 132 0" fill="none" stroke="#ffffff" stroke-width="12" stroke-linecap="round" opacity="0.78"/>
  <text x="256" y="462" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" fill="#ffffff">preview</text>
</svg>
""".encode("utf-8")


def _build_svg_metadata(request: RenderRequest) -> str:
    fields = (
        ("job_id", request.job_id),
        ("tenant_id", request.tenant_id),
        ("avatar_id", request.avatar_id),
        ("user_id", request.user_id),
        ("person_image_url", request.person_image_url or "not_provided"),
        ("avatar_source", request.avatar_source),
        ("avatar_height_cm", request.avatar_height_cm),
        ("avatar_weight_kg", request.avatar_weight_kg),
        ("avatar_gender", request.avatar_gender),
        ("avatar_skin_tone", request.avatar_skin_tone),
        ("avatar_display_name", request.avatar_display_name),
        ("garment_asset_id", request.garment_asset_id),
        ("garment_id", request.garment_id),
        ("external_product_id", request.external_product_id),
        ("garment_name", request.garment_name),
        ("garment_source_image_url", request.garment_source_image_url),
        ("requested_asset_version_id", request.requested_asset_version_id),
        ("latest_asset_version_id", request.latest_asset_version_id),
        ("latest_version_number", request.latest_version_number),
        ("render_model", PLACEHOLDER_RENDER_MODEL),
        ("mask_url", request.mask_url),
        ("texture_url", request.texture_url),
    )

    return _format_svg_metadata(fields)


def _format_svg_metadata(fields: tuple[tuple[str, object], ...]) -> str:
    seen_keys: set[str] = set()
    parts: list[str] = []

    for key, value in fields:
        if key in seen_keys:
            raise ValueError(f"Duplicate render metadata key: {key}")

        seen_keys.add(key)
        parts.append(f"{key}={value}")

    escaped_metadata = escape("; ".join(parts), quote=True)
    return escaped_metadata

