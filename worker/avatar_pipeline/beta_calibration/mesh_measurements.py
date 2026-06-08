from __future__ import annotations

import numpy as np


def measure_height(vertices) -> float:
    """Approximate full body height from the vertical SMPL-X Y-axis extent."""

    vertices = _as_vertices(vertices)
    y_values = vertices[:, 1]
    return _rounded(float(y_values.max() - y_values.min()))


def measure_shoulder_width(vertices) -> float:
    """Approximate shoulder width from the upper torso band, normalized by height."""

    return _normalized_band_width(vertices, lower_ratio=0.68, upper_ratio=0.78)


def measure_hip_width(vertices) -> float:
    """Approximate hip width from the pelvis band, normalized by height."""

    return _normalized_band_width(vertices, lower_ratio=0.45, upper_ratio=0.55)


def measure_waist_width(vertices) -> float:
    """Approximate waist width from the mid-torso band, normalized by height."""

    return _normalized_band_width(vertices, lower_ratio=0.55, upper_ratio=0.64)


def measure_leg_length(vertices) -> float:
    """Approximate lower-body length as floor-to-hip height, normalized by height."""

    vertices = _as_vertices(vertices)
    y_min, y_max, height = _vertical_bounds(vertices)
    if height <= 0:
        return 0.0

    # Without semantic landmarks, use the widest pelvis band as a stable hip proxy.
    hip_y = _widest_band_center_y(vertices, lower_ratio=0.42, upper_ratio=0.57)
    return _rounded((hip_y - y_min) / height)


def _normalized_band_width(vertices, *, lower_ratio: float, upper_ratio: float) -> float:
    vertices = _as_vertices(vertices)
    _, _, height = _vertical_bounds(vertices)
    if height <= 0:
        return 0.0

    band = _vertical_band(vertices, lower_ratio=lower_ratio, upper_ratio=upper_ratio)
    if len(band) == 0:
        return 0.0

    # Percentiles avoid fingers/outlier vertices dominating simple silhouette width.
    width = float(np.percentile(band[:, 0], 95) - np.percentile(band[:, 0], 5))
    return _rounded(width / height)


def _widest_band_center_y(
    vertices: np.ndarray,
    *,
    lower_ratio: float,
    upper_ratio: float,
) -> float:
    y_min, _, height = _vertical_bounds(vertices)
    sample_count = 24
    best_width = -1.0
    best_y = y_min + (height * ((lower_ratio + upper_ratio) / 2))

    for center_ratio in np.linspace(lower_ratio, upper_ratio, sample_count):
        band_half_height = height * 0.012
        center_y = y_min + (height * center_ratio)
        band = vertices[
            (vertices[:, 1] >= center_y - band_half_height)
            & (vertices[:, 1] <= center_y + band_half_height)
        ]
        if len(band) < 8:
            continue

        width = float(np.percentile(band[:, 0], 95) - np.percentile(band[:, 0], 5))
        if width > best_width:
            best_width = width
            best_y = center_y

    return best_y


def _vertical_band(
    vertices: np.ndarray,
    *,
    lower_ratio: float,
    upper_ratio: float,
) -> np.ndarray:
    y_min, _, height = _vertical_bounds(vertices)
    lower_y = y_min + (height * lower_ratio)
    upper_y = y_min + (height * upper_ratio)
    return vertices[(vertices[:, 1] >= lower_y) & (vertices[:, 1] <= upper_y)]


def _vertical_bounds(vertices: np.ndarray) -> tuple[float, float, float]:
    y_values = vertices[:, 1]
    y_min = float(y_values.min())
    y_max = float(y_values.max())
    return y_min, y_max, y_max - y_min


def _as_vertices(vertices) -> np.ndarray:
    array = np.asarray(vertices, dtype=np.float64)
    if array.ndim != 2 or array.shape[1] != 3:
        raise ValueError("vertices must be an Nx3 array")

    return array


def _rounded(value: float) -> float:
    return round(value, 5)
