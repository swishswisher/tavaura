from __future__ import annotations

from dataclasses import dataclass


MIN_BETA = -4.0
MAX_BETA = 4.0
BETA_COUNT = 10


@dataclass(frozen=True)
class AvatarArchetype:
    name: str
    description: str
    betas: list[float]


def create_archetype(
    *,
    name: str,
    description: str,
    betas: list[float],
) -> AvatarArchetype:
    if len(betas) != BETA_COUNT:
        raise ValueError(f"{name} must define exactly {BETA_COUNT} betas.")

    return AvatarArchetype(
        name=name,
        description=description,
        betas=[_clamp_beta(value) for value in betas],
    )


def _clamp_beta(value: float) -> float:
    return max(MIN_BETA, min(MAX_BETA, round(float(value), 4)))


ARCHETYPES: dict[str, AvatarArchetype] = {
    "slim": create_archetype(
        name="slim",
        description="Lean commercial silhouette with reduced mass and narrower upper body.",
        betas=[-1.65, -1.35, -0.80, -0.30, -0.22, -0.30, 0.00, 0.08, -0.18, -0.42],
    ),
    "athletic": create_archetype(
        name="athletic",
        description="Strong shoulder structure with controlled V-taper and defined body mass.",
        betas=[0.72, -0.18, 1.95, 0.12, -0.10, 1.25, 0.00, 0.03, -0.16, -0.34],
    ),
    "soft": create_archetype(
        name="soft",
        description="Softer midsection and moderate fullness while preserving balanced proportions.",
        betas=[0.82, 0.95, -0.22, 0.95, 0.28, -0.18, 0.00, -0.02, 0.58, 0.24],
    ),
    "curvy": create_archetype(
        name="curvy",
        description="Curvier commercial silhouette with fuller hips and balanced upper body.",
        betas=[1.25, 0.78, 0.18, 1.08, 0.58, 0.06, 0.00, -0.03, 0.74, 0.34],
    ),
    "broad": create_archetype(
        name="broad",
        description="Wider torso and shoulder frame with believable horizontal body structure.",
        betas=[1.35, 0.35, 1.75, 0.55, 0.62, 0.70, 0.00, 0.00, 0.24, 0.08],
    ),
    "plus_size": create_archetype(
        name="plus_size",
        description="Fuller commercial silhouette with stronger mass, waist, and hip presence.",
        betas=[2.15, 1.45, 0.70, 1.35, 0.95, 0.20, 0.00, -0.04, 0.88, 0.42],
    ),
    "petite": create_archetype(
        name="petite",
        description="Compact smaller-frame silhouette with lighter body mass.",
        betas=[-0.80, -1.85, -0.45, -0.18, -0.16, -0.12, -0.25, -0.32, -0.12, -0.20],
    ),
    "tall": create_archetype(
        name="tall",
        description="Elongated vertical silhouette with lean mass and balanced shoulder width.",
        betas=[-0.55, 1.85, 0.15, -0.12, -0.05, 0.10, 0.28, 0.42, -0.08, -0.20],
    ),
}
