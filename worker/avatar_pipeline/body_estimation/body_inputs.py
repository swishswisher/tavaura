from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BodyInputProfile:
    height_cm: float | None = None
    weight_kg: float | None = None

    # Allowed values: slim, average, athletic, soft, broad
    body_shape: str | None = None

    # Allowed values: narrow, average, broad
    shoulder_width: str | None = None

    # Allowed values: short, average, long
    torso_length: str | None = None

    # Allowed values: narrow, average, broad
    hip_width: str | None = None

    # Allowed values: light, medium, strong
    build: str | None = None
