import uuid
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RenderRequest:
    job_id: uuid.UUID
    tenant_id: uuid.UUID
    avatar_id: uuid.UUID
    user_id: uuid.UUID
    person_image_url: str | None
    avatar_source: str
    avatar_height_cm: float
    avatar_weight_kg: float
    avatar_gender: str
    avatar_skin_tone: str
    avatar_display_name: str
    garment_asset_id: uuid.UUID
    garment_id: uuid.UUID
    external_product_id: str
    garment_name: str
    garment_source_image_url: str
    garment_processed_image_url: str
    requested_asset_version_id: uuid.UUID
    latest_asset_version_id: uuid.UUID
    latest_version_number: int
    mask_url: str
    texture_url: str


@dataclass(frozen=True)
class RenderArtifact:
    filename: str
    content: bytes
    content_type: str


@dataclass(frozen=True)
class RenderProviderResult:
    output: RenderArtifact
    preview: RenderArtifact


class RenderProvider(Protocol):
    async def render(self, request: RenderRequest) -> RenderProviderResult:
        ...
