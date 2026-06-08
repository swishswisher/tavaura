from __future__ import annotations

from .body_inputs import BodyInputProfile


BETA_COUNT = 10
MIN_BETA = -3.0
MAX_BETA = 3.0


def estimate_betas_from_profile(profile: BodyInputProfile) -> list[float]:
    betas = [0.0] * BETA_COUNT

    _apply_height_weight_effects(betas, profile)
    _apply_body_shape_effects(betas, profile.body_shape)
    _apply_shoulder_width_effects(betas, profile.shoulder_width)
    _apply_torso_length_effects(betas, profile.torso_length)
    _apply_hip_width_effects(betas, profile.hip_width)
    _apply_build_effects(betas, profile.build)

    return [_clamp_beta(value) for value in betas]


def describe_profile_effect(profile: BodyInputProfile) -> str:
    effects: list[str] = []

    if profile.height_cm:
        effects.append("height influences vertical proportions")
    if profile.weight_kg:
        effects.append("weight influences overall mass")
    if _normalized(profile.body_shape) not in {"", "average"}:
        effects.append(f"body shape adjusts {profile.body_shape} silhouette cues")
    if _normalized(profile.shoulder_width) not in {"", "average"}:
        effects.append(f"shoulders trend {profile.shoulder_width}")
    if _normalized(profile.torso_length) not in {"", "average"}:
        effects.append(f"torso length trends {profile.torso_length}")
    if _normalized(profile.hip_width) not in {"", "average"}:
        effects.append(f"hips trend {profile.hip_width}")
    if _normalized(profile.build) not in {"", "medium"}:
        effects.append(f"build trends {profile.build}")

    if not effects:
        return "Neutral body profile; no beta adjustments applied."

    return "; ".join(effects) + "."


def _apply_height_weight_effects(
    betas: list[float],
    profile: BodyInputProfile,
) -> None:
    if profile.height_cm is not None:
        height_delta = (profile.height_cm - 170.0) / 50.0
        _add(betas, 1, height_delta * 0.45)
        _add(betas, 7, height_delta * 0.25)

    if profile.weight_kg is not None:
        weight_delta = (profile.weight_kg - 70.0) / 45.0
        _add(betas, 0, weight_delta * 0.45)
        _add(betas, 3, weight_delta * 0.25)

    if (
        profile.height_cm is not None
        and profile.height_cm > 0
        and profile.weight_kg is not None
    ):
        height_m = profile.height_cm / 100.0
        bmi = profile.weight_kg / (height_m * height_m)
        bmi_delta = (bmi - 23.0) / 12.0
        _add(betas, 0, bmi_delta * 0.35)
        _add(betas, 8, bmi_delta * 0.25)


def _apply_body_shape_effects(betas: list[float], value: str | None) -> None:
    match _normalized(value):
        case "slim":
            _add(betas, 0, -0.55)
            _add(betas, 2, -0.25)
            _add(betas, 4, -0.20)
        case "athletic":
            _add(betas, 0, 0.18)
            _add(betas, 2, 0.42)
            _add(betas, 5, 0.45)
            _add(betas, 8, -0.10)
        case "soft":
            _add(betas, 0, 0.35)
            _add(betas, 3, 0.42)
            _add(betas, 8, 0.22)
            _add(betas, 5, -0.12)
        case "broad":
            _add(betas, 0, 0.42)
            _add(betas, 2, 0.45)
            _add(betas, 4, 0.25)


def _apply_shoulder_width_effects(betas: list[float], value: str | None) -> None:
    match _normalized(value):
        case "narrow":
            _add(betas, 2, -0.35)
            _add(betas, 5, -0.10)
        case "broad":
            _add(betas, 2, 0.38)
            _add(betas, 5, 0.14)


def _apply_torso_length_effects(betas: list[float], value: str | None) -> None:
    match _normalized(value):
        case "short":
            _add(betas, 1, -0.18)
            _add(betas, 6, -0.34)
        case "long":
            _add(betas, 1, 0.18)
            _add(betas, 6, 0.34)


def _apply_hip_width_effects(betas: list[float], value: str | None) -> None:
    match _normalized(value):
        case "narrow":
            _add(betas, 4, -0.34)
            _add(betas, 8, -0.10)
        case "broad":
            _add(betas, 4, 0.38)
            _add(betas, 8, 0.12)


def _apply_build_effects(betas: list[float], value: str | None) -> None:
    match _normalized(value):
        case "light":
            _add(betas, 0, -0.30)
            _add(betas, 5, -0.12)
        case "strong":
            _add(betas, 0, 0.20)
            _add(betas, 2, 0.25)
            _add(betas, 5, 0.35)


def _add(betas: list[float], index: int, value: float) -> None:
    betas[index] += value


def _clamp_beta(value: float) -> float:
    return max(MIN_BETA, min(MAX_BETA, round(value, 4)))


def _normalized(value: str | None) -> str:
    return (value or "").strip().lower().replace("_", "-")
