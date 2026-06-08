from __future__ import annotations

from .body_inputs import BodyInputProfile


MIN_AMPLIFIED_BETA = -4.0
MAX_AMPLIFIED_BETA = 4.0


def amplify_betas(
    betas: list[float],
    profile: BodyInputProfile,
) -> list[float]:
    amplified = [float(value) for value in betas]

    _amplify_body_shape(amplified, profile.body_shape)
    _amplify_build(amplified, profile.build)
    _amplify_shoulders(amplified, profile.shoulder_width)
    _amplify_torso(amplified, profile.torso_length)
    _amplify_hips(amplified, profile.hip_width)
    _amplify_height_weight(amplified, profile)

    return [_clamp_beta(value) for value in amplified]


def describe_amplification(profile: BodyInputProfile) -> str:
    traits: list[str] = []

    body_shape = _normalized(profile.body_shape)
    build = _normalized(profile.build)
    shoulder_width = _normalized(profile.shoulder_width)
    torso_length = _normalized(profile.torso_length)
    hip_width = _normalized(profile.hip_width)

    if body_shape == "slim" or build == "light":
        traits.append("leaner torso, stronger waist taper, and lighter lower-body mass")
    if body_shape == "athletic" or build == "strong":
        traits.append("broader upper body, clearer V-taper, and stronger limb structure")
    if body_shape == "soft":
        traits.append("softer midsection and fuller lower-body silhouette")
    if body_shape == "broad":
        traits.append("wider torso, fuller hips, and stronger horizontal structure")
    if shoulder_width in {"narrow", "broad"}:
        traits.append(f"{shoulder_width} shoulder silhouette")
    if torso_length in {"short", "long"}:
        traits.append(f"{torso_length} torso proportion")
    if hip_width in {"narrow", "broad"}:
        traits.append(f"{hip_width} hip silhouette")
    if profile.height_cm is not None and profile.height_cm >= 185:
        traits.append("taller vertical body proportion")
    if profile.height_cm is not None and profile.height_cm <= 168:
        traits.append("compact vertical body proportion")
    if profile.weight_kg is not None and profile.weight_kg >= 95:
        traits.append("denser body mass")

    if not traits:
        return "No amplification traits applied."

    return "; ".join(traits) + "."


def _amplify_body_shape(betas: list[float], value: str | None) -> None:
    match _normalized(value):
        case "slim":
            _add(betas, 0, -0.40)
            _add(betas, 1, 0.08)
            _add(betas, 2, -0.25)
            _add(betas, 3, -0.18)
            _add(betas, 4, -0.18)
            _add(betas, 7, 0.06)
            _add(betas, 9, -0.35)
        case "athletic":
            _add(betas, 0, 0.12)
            _add(betas, 2, 0.42)
            _add(betas, 4, -0.08)
            _add(betas, 5, 0.38)
            _add(betas, 8, -0.08)
            _add(betas, 9, -0.28)
        case "soft":
            _add(betas, 0, 0.28)
            _add(betas, 2, -0.08)
            _add(betas, 3, 0.36)
            _add(betas, 4, 0.14)
            _add(betas, 5, -0.12)
            _add(betas, 8, 0.30)
            _add(betas, 9, 0.20)
        case "broad":
            _add(betas, 0, 0.45)
            _add(betas, 2, 0.38)
            _add(betas, 3, 0.12)
            _add(betas, 4, 0.30)
            _add(betas, 8, 0.16)
            _add(betas, 9, 0.10)


def _amplify_build(betas: list[float], value: str | None) -> None:
    match _normalized(value):
        case "light":
            _add(betas, 0, -0.25)
            _add(betas, 5, -0.12)
            _add(betas, 8, -0.12)
        case "strong":
            _add(betas, 0, 0.18)
            _add(betas, 2, 0.25)
            _add(betas, 5, 0.32)
            _add(betas, 9, -0.12)


def _amplify_shoulders(betas: list[float], value: str | None) -> None:
    match _normalized(value):
        case "narrow":
            _add(betas, 2, -0.25)
            _add(betas, 5, -0.08)
        case "broad":
            _add(betas, 2, 0.28)
            _add(betas, 5, 0.08)


def _amplify_torso(betas: list[float], value: str | None) -> None:
    match _normalized(value):
        case "short":
            _add(betas, 0, 0.12)
            _add(betas, 1, -0.12)
            _add(betas, 6, -0.25)
        case "long":
            _add(betas, 1, 0.16)
            _add(betas, 6, 0.24)
            _add(betas, 7, 0.12)


def _amplify_hips(betas: list[float], value: str | None) -> None:
    match _normalized(value):
        case "narrow":
            _add(betas, 4, -0.18)
            _add(betas, 8, -0.08)
        case "broad":
            _add(betas, 4, 0.32)
            _add(betas, 8, 0.14)


def _amplify_height_weight(betas: list[float], profile: BodyInputProfile) -> None:
    if profile.height_cm is not None and profile.height_cm >= 185:
        _add(betas, 0, -0.05)
        _add(betas, 1, 0.22)
        _add(betas, 7, 0.20)

    if profile.height_cm is not None and profile.height_cm <= 168:
        _add(betas, 0, 0.14)
        _add(betas, 1, -0.14)
        _add(betas, 3, 0.08)
        _add(betas, 7, -0.12)

    if profile.weight_kg is not None and profile.weight_kg >= 95:
        _add(betas, 0, 0.25)
        _add(betas, 3, 0.12)
        _add(betas, 4, 0.12)
        _add(betas, 8, 0.10)


def _add(betas: list[float], index: int, value: float) -> None:
    if index < len(betas):
        betas[index] += value


def _clamp_beta(value: float) -> float:
    return max(MIN_AMPLIFIED_BETA, min(MAX_AMPLIFIED_BETA, round(value, 4)))


def _normalized(value: str | None) -> str:
    return (value or "").strip().lower().replace("_", "-")
