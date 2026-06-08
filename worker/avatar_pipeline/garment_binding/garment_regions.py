from __future__ import annotations

import numpy as np


# Thresholds are normalized against garment height so the classifier works across
# archetypes. These semantic regions let future deformation rules preserve
# collars, hems, sleeves, and underarms instead of treating the shirt as one blob.
SLEEVE_X_THRESHOLD = 0.17
COLLAR_X_THRESHOLD = 0.32
COLLAR_Y_PERCENTILE = 86.0
HEM_Y_PERCENTILE = 11.0
UNDERARM_Y_RANGE = (0.57, 0.70)
UNDERARM_X_THRESHOLD = 0.145
TORSO_X_THRESHOLD = 0.19

REGION_NAMES = (
    "torso",
    "left_sleeve",
    "right_sleeve",
    "underarm",
    "collar",
    "hem",
)


def classify_garment_regions(vertices) -> dict[str, list[int]]:
    """Classify proxy garment vertices into semantic regions.

    This MVP classifier uses simple geometry instead of ML segmentation. The
    resulting regions are metadata only for now; future passes can use them for
    region-specific deformation constraints and collision handling.
    """
    garment_vertices = _as_vertices(vertices)
    if len(garment_vertices) == 0:
        return {region_name: [] for region_name in REGION_NAMES}

    x = garment_vertices[:, 0]
    y = garment_vertices[:, 1]
    center_x = float(np.median(x))
    y_min = float(y.min())
    y_max = float(y.max())
    height = max(y_max - y_min, 1e-9)

    relative_x = x - center_x
    x_ratio = relative_x / height
    abs_x_ratio = np.abs(x_ratio)
    y_ratio = (y - y_min) / height

    collar_y = float(np.percentile(y, COLLAR_Y_PERCENTILE))
    hem_y = float(np.percentile(y, HEM_Y_PERCENTILE))

    collar_mask = (
        (y >= collar_y)
        & (y_ratio >= 0.70)
        & (abs_x_ratio <= COLLAR_X_THRESHOLD)
    )
    hem_mask = y <= hem_y
    underarm_mask = (
        (y_ratio >= UNDERARM_Y_RANGE[0])
        & (y_ratio <= UNDERARM_Y_RANGE[1])
        & (abs_x_ratio >= UNDERARM_X_THRESHOLD)
        & ~collar_mask
        & ~hem_mask
    )
    left_sleeve_mask = (
        (x_ratio <= -SLEEVE_X_THRESHOLD)
        & (y_ratio >= UNDERARM_Y_RANGE[0])
        & ~underarm_mask
        & ~collar_mask
        & ~hem_mask
    )
    right_sleeve_mask = (
        (x_ratio >= SLEEVE_X_THRESHOLD)
        & (y_ratio >= UNDERARM_Y_RANGE[0])
        & ~underarm_mask
        & ~collar_mask
        & ~hem_mask
    )

    used_mask = (
        collar_mask
        | hem_mask
        | underarm_mask
        | left_sleeve_mask
        | right_sleeve_mask
    )
    torso_mask = ~used_mask & (abs_x_ratio <= max(TORSO_X_THRESHOLD, SLEEVE_X_THRESHOLD))
    torso_mask |= ~used_mask & ~left_sleeve_mask & ~right_sleeve_mask

    return {
        "torso": _indices_from_mask(torso_mask),
        "left_sleeve": _indices_from_mask(left_sleeve_mask),
        "right_sleeve": _indices_from_mask(right_sleeve_mask),
        "underarm": _indices_from_mask(underarm_mask),
        "collar": _indices_from_mask(collar_mask),
        "hem": _indices_from_mask(hem_mask),
    }


def _indices_from_mask(mask: np.ndarray) -> list[int]:
    return [int(index) for index in np.nonzero(mask)[0]]


def _as_vertices(vertices) -> np.ndarray:
    array = np.asarray(vertices, dtype=np.float64)
    if array.ndim != 2 or array.shape[1] != 3:
        raise ValueError("vertices must be an Nx3 array")

    return array
