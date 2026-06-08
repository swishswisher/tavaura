from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .panels import generate_panel_tshirt
from .surface_fit import (
    COLLAR,
    HEM,
    LEFT_ARMHOLE,
    LEFT_SLEEVE,
    RIGHT_ARMHOLE,
    RIGHT_SLEEVE,
    TORSO_BACK,
    TORSO_FRONT,
)


ZONE_COLLAR = "collar"
ZONE_FRONT_PANEL = "front_panel"
ZONE_BACK_PANEL = "back_panel"
ZONE_LEFT_SLEEVE = "left_sleeve"
ZONE_RIGHT_SLEEVE = "right_sleeve"
ZONE_LEFT_ARMHOLE = "left_armhole"
ZONE_RIGHT_ARMHOLE = "right_armhole"
ZONE_HEM = "hem"
ZONE_NAMES = (
    ZONE_COLLAR,
    ZONE_FRONT_PANEL,
    ZONE_BACK_PANEL,
    ZONE_LEFT_SLEEVE,
    ZONE_RIGHT_SLEEVE,
    ZONE_LEFT_ARMHOLE,
    ZONE_RIGHT_ARMHOLE,
    ZONE_HEM,
)


@dataclass(frozen=True)
class BodyDerivedTshirtMesh:
    vertices: np.ndarray
    faces: np.ndarray
    regions: dict[str, list[int]]
    region_labels: tuple[str, ...]
    zones: dict[str, list[int]]
    zone_labels: tuple[str, ...]
    curves: dict[str, list[int]]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class _ArmContext:
    side: float
    shoulder: np.ndarray
    elbow: np.ndarray
    axis: np.ndarray
    length: float
    radius: float


@dataclass(frozen=True)
class _BodyMetrics:
    y_min: float
    y_max: float
    height: float
    center_x: float
    center_z: float
    left_arm: _ArmContext
    right_arm: _ArmContext


def create_body_derived_tshirt(
    body_vertices,
    body_faces,
    *,
    body_joints=None,
    torso_offset: float = 0.010,
    sleeve_offset: float = 0.010,
    collar_offset: float = 0.005,
    hem_offset: float = 0.012,
) -> BodyDerivedTshirtMesh:
    """Create a clean panel-based T-shirt from body-derived landmarks.

    This path deliberately avoids noisy body-surface cutouts. Body measurements
    define the torso panels, collar loop, armhole loops, and sleeve tube axes;
    the output topology is explicit and stable before any fitting pass runs.
    """
    body = _as_vertices(body_vertices)
    faces = _as_faces(body_faces)
    metrics = _measure_body(body, body_joints)
    panel_mesh = generate_panel_tshirt(
        body,
        faces,
        surface_offset=min(torso_offset, sleeve_offset, collar_offset, hem_offset),
    )
    vertices = np.asarray(panel_mesh.vertices, dtype=np.float64).copy()
    labels = list(panel_mesh.region_labels)
    curves = {name: list(indices) for name, indices in panel_mesh.curves.items()}
    curves = _refresh_panel_curves(vertices, panel_mesh.faces, labels, curves, metrics)
    _apply_curve_region_labels(labels, curves)
    vertices = _apply_panel_construction(
        vertices=vertices,
        faces=panel_mesh.faces,
        labels=labels,
        curves=curves,
        body_vertices=body,
        metrics=metrics,
        torso_offset=torso_offset,
        sleeve_offset=sleeve_offset,
        collar_offset=collar_offset,
        hem_offset=hem_offset,
    )
    curves = _refresh_panel_curves(vertices, panel_mesh.faces, labels, curves, metrics)
    _apply_curve_region_labels(labels, curves)
    zones, zone_labels = _build_semantic_zones(len(vertices), labels, curves)
    regions = _regions_from_labels(labels)
    metadata = _build_metadata(
        body_vertices=body,
        garment_vertices=vertices,
        garment_faces=panel_mesh.faces,
        regions=regions,
        zones=zones,
        curves=curves,
        metrics=metrics,
    )
    _validate_topology_or_raise(metadata["topology"])

    return BodyDerivedTshirtMesh(
        vertices=vertices,
        faces=np.asarray(panel_mesh.faces, dtype=np.int32),
        regions=regions,
        region_labels=tuple(labels),
        zones=zones,
        zone_labels=tuple(zone_labels),
        curves=curves,
        metadata=metadata,
    )


def compute_shirt_body_distance_stats(
    shirt_vertices,
    body_vertices,
) -> dict[str, float]:
    shirt = _as_vertices(shirt_vertices)
    body = _as_vertices(body_vertices)
    distances = _nearest_distances(shirt, body)
    return {
        "average": float(distances.mean()) if len(distances) else 0.0,
        "max": float(distances.max()) if len(distances) else 0.0,
    }


def _apply_panel_construction(
    *,
    vertices: np.ndarray,
    faces: np.ndarray,
    labels: list[str],
    curves: dict[str, list[int]],
    body_vertices: np.ndarray,
    metrics: _BodyMetrics,
    torso_offset: float,
    sleeve_offset: float,
    collar_offset: float,
    hem_offset: float,
) -> np.ndarray:
    del torso_offset, sleeve_offset, collar_offset, hem_offset
    refined = vertices.copy()
    refined = _anchor_torso_to_body_surface(refined, labels, body_vertices, metrics)
    refined = _shape_torso_panels(refined, labels, metrics)
    refined = _rebuild_collar_loop(refined, curves.get("neckline_loop", []), metrics)
    refined = _rebuild_hem_loop(refined, curves.get("hem_loop", []), metrics)
    refined = _rebuild_sleeve_tube(
        refined,
        labels,
        curves,
        arm=metrics.left_arm,
        sleeve_region=LEFT_SLEEVE,
        armhole_curve_name="left_armhole_loop",
        cuff_curve_name="left_sleeve_cuff_loop",
        metrics=metrics,
    )
    refined = _rebuild_sleeve_tube(
        refined,
        labels,
        curves,
        arm=metrics.right_arm,
        sleeve_region=RIGHT_SLEEVE,
        armhole_curve_name="right_armhole_loop",
        cuff_curve_name="right_sleeve_cuff_loop",
        metrics=metrics,
    )
    refined = _region_aware_smoothing(refined, faces, labels, curves, iterations=2)
    refined = _rebuild_collar_loop(refined, curves.get("neckline_loop", []), metrics, blend=0.75)
    refined = _rebuild_hem_loop(refined, curves.get("hem_loop", []), metrics, blend=0.82)
    refined = _clamp_sleeve_height(refined, labels, metrics)
    return refined


def _anchor_torso_to_body_surface(
    vertices: np.ndarray,
    labels: list[str],
    body_vertices: np.ndarray,
    metrics: _BodyMetrics,
) -> np.ndarray:
    anchored = vertices.copy()
    body = _as_vertices(body_vertices)
    body_y_ratio = _y_ratio(body[:, 1], metrics)
    body_abs_x_ratio = np.abs(body[:, 0] - metrics.center_x) / metrics.height
    for index, label in enumerate(labels):
        if label not in (TORSO_FRONT, TORSO_BACK, COLLAR, HEM):
            continue

        point = anchored[index]
        point_y_ratio = float((point[1] - metrics.y_min) / metrics.height)
        y_window = metrics.height * (0.032 if label not in (COLLAR, HEM) else 0.024)
        mask = (
            (np.abs(body[:, 1] - point[1]) <= y_window)
            & (body_abs_x_ratio <= 0.36)
            & (body_y_ratio >= 0.430)
            & (body_y_ratio <= 0.805)
        )
        if label == TORSO_FRONT:
            mask &= body[:, 2] >= metrics.center_z - (metrics.height * 0.010)
        elif label == TORSO_BACK:
            mask &= body[:, 2] <= metrics.center_z + (metrics.height * 0.010)
        elif label == COLLAR:
            mask &= body_y_ratio >= 0.675
        elif label == HEM:
            mask &= body_y_ratio <= max(0.535, point_y_ratio + 0.035)

        candidates = body[mask]
        if len(candidates) == 0:
            continue

        target = _directional_surface_target(point, candidates, metrics)
        outward = _torso_outward_direction(point, metrics)
        offset = metrics.height * _region_shell_offset(label)
        blend = _region_anchor_blend(label)
        anchored[index] = (point * (1.0 - blend)) + ((target + (outward * offset)) * blend)

    return anchored


def _directional_surface_target(
    point: np.ndarray,
    candidates: np.ndarray,
    metrics: _BodyMetrics,
) -> np.ndarray:
    point_vector = np.array([point[0] - metrics.center_x, point[2] - metrics.center_z], dtype=np.float64)
    point_radius = max(float(np.linalg.norm(point_vector)), 1e-9)
    point_dir = point_vector / point_radius
    candidate_vectors = candidates[:, [0, 2]] - np.array([metrics.center_x, metrics.center_z], dtype=np.float64)
    candidate_radii = np.linalg.norm(candidate_vectors, axis=1)
    candidate_dirs = candidate_vectors / np.maximum(candidate_radii[:, None], 1e-9)
    angular_distance = 1.0 - np.clip(candidate_dirs @ point_dir, -1.0, 1.0)
    y_distance = np.abs(candidates[:, 1] - point[1]) / metrics.height
    radial_distance = np.abs(candidate_radii - point_radius) / metrics.height
    score = (angular_distance * 2.4) + (y_distance * 1.8) + (radial_distance * 0.20)
    return candidates[int(np.argmin(score))]


def _torso_outward_direction(
    point: np.ndarray,
    metrics: _BodyMetrics,
) -> np.ndarray:
    vector = np.array(
        [point[0] - metrics.center_x, 0.0, point[2] - metrics.center_z],
        dtype=np.float64,
    )
    return _normalize_vector(vector, fallback=np.array([0.0, 0.0, 1.0], dtype=np.float64))


def _region_shell_offset(region_name: str) -> float:
    if region_name == COLLAR:
        return 0.008
    if region_name == HEM:
        return 0.018
    return 0.018


def _region_anchor_blend(region_name: str) -> float:
    if region_name == COLLAR:
        return 0.58
    if region_name == HEM:
        return 0.64
    return 0.78


def _shape_torso_panels(
    vertices: np.ndarray,
    labels: list[str],
    metrics: _BodyMetrics,
) -> np.ndarray:
    shaped = vertices.copy()
    y_ratio = _y_ratio(shaped[:, 1], metrics)
    x_offset = shaped[:, 0] - metrics.center_x
    abs_x_ratio = np.abs(x_offset) / metrics.height
    side_sign = np.sign(x_offset)
    side_sign[side_sign == 0.0] = 1.0

    for index, label in enumerate(labels):
        if label == TORSO_FRONT:
            if 0.700 <= y_ratio[index] <= 0.810:
                center_weight = max(0.0, 1.0 - (abs_x_ratio[index] / 0.27) ** 1.7)
                shaped[index, 2] += metrics.height * 0.028 * center_weight
            if 0.585 <= y_ratio[index] <= 0.725:
                center_weight = max(0.0, 1.0 - (abs_x_ratio[index] / 0.25) ** 1.8)
                shaped[index, 2] += metrics.height * 0.010 * center_weight
            if 0.500 <= y_ratio[index] <= 0.610:
                center_weight = max(0.0, 1.0 - (abs_x_ratio[index] / 0.26) ** 1.6)
                shaped[index, 2] += metrics.height * 0.010 * center_weight
        elif label == TORSO_BACK and 0.540 <= y_ratio[index] <= 0.720:
            center_weight = max(0.0, 1.0 - (abs_x_ratio[index] / 0.25) ** 1.6)
            shaped[index, 2] -= metrics.height * 0.004 * center_weight

        if label in (TORSO_FRONT, TORSO_BACK, HEM) and abs_x_ratio[index] >= 0.130:
            side_ease = _smoothstep(0.130, 0.230, abs_x_ratio[index])
            shaped[index, 0] += side_sign[index] * metrics.height * (0.010 + (0.045 * side_ease))
            if 0.465 <= y_ratio[index] <= 0.600:
                shaped[index, 1] -= metrics.height * 0.002

    return shaped


def _rebuild_collar_loop(
    vertices: np.ndarray,
    collar_loop: list[int],
    metrics: _BodyMetrics,
    *,
    blend: float = 0.92,
) -> np.ndarray:
    if len(collar_loop) < 6:
        return vertices

    refined = vertices.copy()
    loop = _ordered_loop_by_axes(refined, collar_loop, axes=(0, 2), center=np.array([metrics.center_x, 0.0, metrics.center_z]))
    shoulder_half_width = abs(metrics.right_arm.shoulder[0] - metrics.left_arm.shoulder[0]) * 0.5
    half_width = float(np.clip(shoulder_half_width * 0.42, metrics.height * 0.058, metrics.height * 0.092))
    side_y = metrics.y_min + (metrics.height * 0.782)
    front_y = metrics.y_min + (metrics.height * 0.758)
    back_y = metrics.y_min + (metrics.height * 0.800)
    front_z = metrics.center_z + (metrics.height * 0.104)
    back_z = metrics.center_z - (metrics.height * 0.068)

    for index in loop:
        point = refined[index]
        side_param = float(np.clip((point[0] - metrics.center_x) / half_width, -1.0, 1.0))
        center_weight = 1.0 - (abs(side_param) ** 1.65)
        if point[2] >= metrics.center_z:
            target = np.array(
                [
                    metrics.center_x + (side_param * half_width),
                    side_y - ((side_y - front_y) * center_weight),
                    front_z - (metrics.height * 0.006 * abs(side_param)),
                ],
                dtype=np.float64,
            )
        else:
            target = np.array(
                [
                    metrics.center_x + (side_param * half_width * 0.90),
                    back_y - (metrics.height * 0.004 * center_weight),
                    back_z + (metrics.height * 0.004 * abs(side_param)),
                ],
                dtype=np.float64,
            )
        refined[index] = (point * (1.0 - blend)) + (target * blend)

    return _smooth_ordered_loop(refined, loop, strength=0.26, vertical_strength=0.06)


def _rebuild_hem_loop(
    vertices: np.ndarray,
    hem_loop: list[int],
    metrics: _BodyMetrics,
    *,
    blend: float = 0.90,
) -> np.ndarray:
    if len(hem_loop) < 8:
        return vertices

    refined = vertices.copy()
    loop = _ordered_loop_by_axes(refined, hem_loop, axes=(0, 2), center=np.array([metrics.center_x, 0.0, metrics.center_z]))
    hem_y = float(np.median(refined[loop, 1]))
    for loop_index, index in enumerate(loop):
        previous_point = refined[loop[(loop_index - 1) % len(loop)]]
        next_point = refined[loop[(loop_index + 1) % len(loop)]]
        average = (previous_point + next_point) * 0.5
        target = refined[index].copy()
        target[0] = (target[0] * 0.72) + (average[0] * 0.28)
        target[2] = (target[2] * 0.72) + (average[2] * 0.28)
        target[1] = (target[1] * 0.22) + (hem_y * 0.78)
        refined[index] = (refined[index] * (1.0 - blend)) + (target * blend)

    return refined


def _rebuild_sleeve_tube(
    vertices: np.ndarray,
    labels: list[str],
    curves: dict[str, list[int]],
    *,
    arm: _ArmContext,
    sleeve_region: str,
    armhole_curve_name: str,
    cuff_curve_name: str,
    metrics: _BodyMetrics,
) -> np.ndarray:
    sleeve_indices = np.asarray(
        [index for index, label in enumerate(labels) if label == sleeve_region],
        dtype=np.int32,
    )
    if len(sleeve_indices) == 0:
        return vertices

    refined = vertices.copy()
    armhole_loop = curves.get(armhole_curve_name, [])
    cuff_loop = curves.get(cuff_curve_name, [])
    root_axial = -metrics.height * 0.018
    sleeve_length = max(arm.length * 0.50, metrics.height * 0.100)
    root_radius = max(arm.radius + (metrics.height * 0.007), metrics.height * 0.031)
    cuff_radius = max(arm.radius + (metrics.height * 0.004), metrics.height * 0.027)
    max_y = max(metrics.left_arm.shoulder[1], metrics.right_arm.shoulder[1]) + (metrics.height * 0.006)

    if armhole_loop:
        root_center = arm.shoulder + (arm.axis * root_axial)
        for index in armhole_loop:
            point = refined[index]
            radial_dir = _normalize_vector(
                point - root_center,
                fallback=np.array([0.0, 0.0, 1.0], dtype=np.float64),
            )
            target = root_center + (radial_dir * root_radius)
            target[1] = min(target[1], max_y)
            refined[index] = (point * 0.36) + (target * 0.64)

    for index in sleeve_indices:
        point = refined[index]
        point_axial = _project_on_arm_axis(point[None, :], arm)[0]
        progress = float(np.clip((point_axial - root_axial) / sleeve_length, 0.0, 1.0))
        axis_point = arm.shoulder + (arm.axis * (root_axial + (progress * sleeve_length)))
        direction = point - axis_point
        radial_dir = _normalize_vector(direction, fallback=np.array([0.0, 0.0, 1.0], dtype=np.float64))
        radius = root_radius + ((cuff_radius - root_radius) * progress)
        target = axis_point + (radial_dir * radius)
        target[1] -= metrics.height * 0.012 * progress
        target[1] = min(target[1], max_y)
        blend = 0.46 if progress < 0.20 else 0.78
        refined[index] = (point * (1.0 - blend)) + (target * blend)

    refined = _smooth_sleeve_ring(refined, cuff_loop, arm, strength=0.62)
    refined = _smooth_sleeve_ring(refined, armhole_loop, arm, strength=0.22)
    return refined


def _smooth_sleeve_ring(
    vertices: np.ndarray,
    ring: list[int],
    arm: _ArmContext,
    *,
    strength: float,
) -> np.ndarray:
    if len(ring) < 4:
        return vertices

    refined = vertices.copy()
    ordered = _ordered_sleeve_ring(refined, ring, arm)
    for loop_index, index in enumerate(ordered):
        previous_point = refined[ordered[(loop_index - 1) % len(ordered)]]
        next_point = refined[ordered[(loop_index + 1) % len(ordered)]]
        average = (previous_point + next_point) * 0.5
        refined[index] = (refined[index] * (1.0 - strength)) + (average * strength)

    return refined


def _region_aware_smoothing(
    vertices: np.ndarray,
    faces: np.ndarray,
    labels: list[str],
    curves: dict[str, list[int]],
    *,
    iterations: int,
) -> np.ndarray:
    protected = set(curves.get("neckline_loop", [])) | set(curves.get("hem_loop", []))
    adjacency = _build_vertex_adjacency(len(vertices), faces)
    smoothed = vertices.copy()
    for _ in range(iterations):
        next_vertices = smoothed.copy()
        for index, neighbors in enumerate(adjacency):
            if not neighbors:
                continue

            if index in protected:
                weight = 0.012
            elif labels[index] in (LEFT_ARMHOLE, RIGHT_ARMHOLE):
                weight = 0.030
            elif labels[index] in (LEFT_SLEEVE, RIGHT_SLEEVE):
                weight = 0.040
            else:
                weight = 0.055

            average = smoothed[list(neighbors)].mean(axis=0)
            next_vertices[index] = smoothed[index] + ((average - smoothed[index]) * weight)
        smoothed = next_vertices

    return smoothed


def _clamp_sleeve_height(
    vertices: np.ndarray,
    labels: list[str],
    metrics: _BodyMetrics,
) -> np.ndarray:
    refined = vertices.copy()
    max_y = max(metrics.left_arm.shoulder[1], metrics.right_arm.shoulder[1]) + (metrics.height * 0.020)
    for index, label in enumerate(labels):
        if label in (LEFT_SLEEVE, RIGHT_SLEEVE, LEFT_ARMHOLE, RIGHT_ARMHOLE):
            refined[index, 1] = min(refined[index, 1], max_y)

    return refined


def _refresh_panel_curves(
    vertices: np.ndarray,
    faces: np.ndarray,
    labels: list[str],
    curves: dict[str, list[int]],
    metrics: _BodyMetrics,
) -> dict[str, list[int]]:
    refreshed = dict(curves)
    boundary_components = _boundary_vertex_components(faces)
    collar_loop = _select_neckline_boundary_component(vertices, boundary_components, metrics)
    hem_loop = _select_hem_boundary_component(vertices, boundary_components, metrics)
    collar_source = collar_loop if len(collar_loop) >= 6 else refreshed.get("neckline_loop", [])
    hem_source = hem_loop if len(hem_loop) >= 8 else refreshed.get("hem_loop", [])
    refreshed["neckline_loop"] = _ordered_loop_by_axes(
        vertices,
        collar_source,
        axes=(0, 2),
        center=np.array([metrics.center_x, 0.0, metrics.center_z]),
    ).tolist()
    refreshed["hem_loop"] = _ordered_loop_by_axes(
        vertices,
        hem_source,
        axes=(0, 2),
        center=np.array([metrics.center_x, 0.0, metrics.center_z]),
    ).tolist()
    refreshed["left_armhole_loop"] = list(refreshed.get("left_armhole_loop", []))
    refreshed["right_armhole_loop"] = list(refreshed.get("right_armhole_loop", []))
    refreshed["left_sleeve_cuff_loop"] = list(refreshed.get("left_sleeve_cuff_loop", []))
    refreshed["right_sleeve_cuff_loop"] = list(refreshed.get("right_sleeve_cuff_loop", []))
    del labels
    return refreshed


def _apply_curve_region_labels(
    labels: list[str],
    curves: dict[str, list[int]],
) -> None:
    for index in curves.get("neckline_loop", []):
        labels[int(index)] = COLLAR
    for index in curves.get("hem_loop", []):
        labels[int(index)] = HEM
    for index in curves.get("left_armhole_loop", []):
        labels[int(index)] = LEFT_ARMHOLE
    for index in curves.get("right_armhole_loop", []):
        labels[int(index)] = RIGHT_ARMHOLE


def _build_semantic_zones(
    vertex_count: int,
    labels: list[str],
    curves: dict[str, list[int]],
) -> tuple[dict[str, list[int]], list[str]]:
    zone_labels = [ZONE_FRONT_PANEL for _ in range(vertex_count)]
    for index, label in enumerate(labels):
        if label == TORSO_BACK:
            zone_labels[index] = ZONE_BACK_PANEL
        elif label == LEFT_SLEEVE:
            zone_labels[index] = ZONE_LEFT_SLEEVE
        elif label == RIGHT_SLEEVE:
            zone_labels[index] = ZONE_RIGHT_SLEEVE
        elif label == LEFT_ARMHOLE:
            zone_labels[index] = ZONE_LEFT_ARMHOLE
        elif label == RIGHT_ARMHOLE:
            zone_labels[index] = ZONE_RIGHT_ARMHOLE
        elif label == COLLAR:
            zone_labels[index] = ZONE_COLLAR
        elif label == HEM:
            zone_labels[index] = ZONE_HEM

    _assign_zone(zone_labels, curves.get("neckline_loop", []), ZONE_COLLAR)
    _assign_zone(zone_labels, curves.get("hem_loop", []), ZONE_HEM)
    _assign_zone(zone_labels, curves.get("left_armhole_loop", []), ZONE_LEFT_ARMHOLE)
    _assign_zone(zone_labels, curves.get("right_armhole_loop", []), ZONE_RIGHT_ARMHOLE)
    _assign_zone(zone_labels, curves.get("left_sleeve_cuff_loop", []), ZONE_LEFT_SLEEVE)
    _assign_zone(zone_labels, curves.get("right_sleeve_cuff_loop", []), ZONE_RIGHT_SLEEVE)
    zones = {
        zone_name: [index for index, label in enumerate(zone_labels) if label == zone_name]
        for zone_name in ZONE_NAMES
    }
    return zones, zone_labels


def _assign_zone(
    labels: list[str],
    indices: list[int],
    zone_name: str,
) -> None:
    for index in indices:
        if 0 <= int(index) < len(labels):
            labels[int(index)] = zone_name


def _regions_from_labels(labels: list[str]) -> dict[str, list[int]]:
    return {
        region_name: [index for index, label in enumerate(labels) if label == region_name]
        for region_name in (
            TORSO_FRONT,
            TORSO_BACK,
            LEFT_SLEEVE,
            RIGHT_SLEEVE,
            COLLAR,
            LEFT_ARMHOLE,
            RIGHT_ARMHOLE,
            HEM,
        )
    }


def _build_metadata(
    *,
    body_vertices: np.ndarray,
    garment_vertices: np.ndarray,
    garment_faces: np.ndarray,
    regions: dict[str, list[int]],
    zones: dict[str, list[int]],
    curves: dict[str, list[int]],
    metrics: _BodyMetrics,
) -> dict[str, Any]:
    distance_stats = compute_shirt_body_distance_stats(garment_vertices, body_vertices)
    topology = _topology_diagnostics(garment_faces, curves)
    shoulder_limit = max(metrics.left_arm.shoulder[1], metrics.right_arm.shoulder[1]) + (metrics.height * 0.020)
    sleeve_indices = regions[LEFT_SLEEVE] + regions[RIGHT_SLEEVE] + regions[LEFT_ARMHOLE] + regions[RIGHT_ARMHOLE]
    sleeve_max_y = float(garment_vertices[sleeve_indices, 1].max()) if sleeve_indices else 0.0
    sleeve_height_warning = sleeve_max_y > shoulder_limit
    return {
        "torso_vertex_count": int(len(regions[TORSO_FRONT]) + len(regions[TORSO_BACK])),
        "sleeve_vertex_count": int(len(regions[LEFT_SLEEVE]) + len(regions[RIGHT_SLEEVE])),
        "collar_vertex_count": int(len(curves.get("neckline_loop", []))),
        "left_armhole_vertex_count": int(len(curves.get("left_armhole_loop", []))),
        "right_armhole_vertex_count": int(len(curves.get("right_armhole_loop", []))),
        "left_sleeve_ring_vertex_count": int(len(curves.get("left_sleeve_cuff_loop", []))),
        "right_sleeve_ring_vertex_count": int(len(curves.get("right_sleeve_cuff_loop", []))),
        "hem_vertex_count": int(len(curves.get("hem_loop", []))),
        "zone_counts": {zone_name: int(len(indices)) for zone_name, indices in zones.items()},
        "collar_landmarks": _collar_landmarks(body_vertices, metrics),
        "hem_landmarks": _hem_landmarks(body_vertices, metrics),
        "average_shirt_body_distance": distance_stats["average"],
        "max_shirt_body_distance": distance_stats["max"],
        "sleeve_max_y": sleeve_max_y,
        "sleeve_height_limit": float(shoulder_limit),
        "sleeve_height_warning": bool(sleeve_height_warning),
        "topology": topology,
    }


def _collar_landmarks(
    vertices: np.ndarray,
    metrics: _BodyMetrics,
) -> dict[str, list[float]]:
    targets = {
        "left_shoulder_base": metrics.left_arm.shoulder,
        "right_shoulder_base": metrics.right_arm.shoulder,
        "upper_sternum": np.array(
            [metrics.center_x, metrics.y_min + (metrics.height * 0.705), metrics.center_z + (metrics.height * 0.080)],
            dtype=np.float64,
        ),
        "neck_base": np.array(
            [metrics.center_x, metrics.y_min + (metrics.height * 0.770), metrics.center_z + (metrics.height * 0.015)],
            dtype=np.float64,
        ),
    }
    return {name: _round_point(_nearest_vertex(vertices, target)) for name, target in targets.items()}


def _hem_landmarks(
    vertices: np.ndarray,
    metrics: _BodyMetrics,
) -> dict[str, list[float]]:
    hem_y = metrics.y_min + (metrics.height * 0.485)
    targets = {
        "front_center": np.array([metrics.center_x, hem_y, metrics.center_z + (metrics.height * 0.090)], dtype=np.float64),
        "back_center": np.array([metrics.center_x, hem_y, metrics.center_z - (metrics.height * 0.090)], dtype=np.float64),
        "left_side": np.array([metrics.center_x - (metrics.height * 0.170), hem_y, metrics.center_z], dtype=np.float64),
        "right_side": np.array([metrics.center_x + (metrics.height * 0.170), hem_y, metrics.center_z], dtype=np.float64),
    }
    return {name: _round_point(_nearest_vertex(vertices, target)) for name, target in targets.items()}


def _measure_body(
    vertices: np.ndarray,
    body_joints,
) -> _BodyMetrics:
    y_min = float(vertices[:, 1].min())
    y_max = float(vertices[:, 1].max())
    height = max(y_max - y_min, 1e-9)
    y_ratio = (vertices[:, 1] - y_min) / height
    torso_mask = (y_ratio >= 0.44) & (y_ratio <= 0.80)
    torso_vertices = vertices[torso_mask] if np.any(torso_mask) else vertices
    center_x = float(np.median(torso_vertices[:, 0]))
    center_z = float(np.median(torso_vertices[:, 2]))
    left_arm = _arm_context_from_joints(vertices, body_joints, height, center_x, y_min, side=-1.0)
    right_arm = _arm_context_from_joints(vertices, body_joints, height, center_x, y_min, side=1.0)
    return _BodyMetrics(
        y_min=y_min,
        y_max=y_max,
        height=height,
        center_x=center_x,
        center_z=center_z,
        left_arm=left_arm,
        right_arm=right_arm,
    )


def _arm_context_from_joints(
    vertices: np.ndarray,
    body_joints,
    height: float,
    center_x: float,
    y_min: float,
    *,
    side: float,
) -> _ArmContext:
    joint_array = None if body_joints is None else np.asarray(body_joints, dtype=np.float64)
    if joint_array is not None and joint_array.ndim == 3:
        joint_array = joint_array[0]
    if joint_array is not None and joint_array.ndim == 2 and joint_array.shape[0] > 19:
        pairs = [
            (joint_array[16], joint_array[18]),
            (joint_array[17], joint_array[19]),
        ]
        pairs = sorted(pairs, key=lambda pair: pair[0][0])
        shoulder, elbow = pairs[0] if side < 0 else pairs[-1]
        return _make_arm_context(vertices, shoulder, elbow, height, side=side)

    y_ratio = (vertices[:, 1] - y_min) / height
    side_mask = np.sign(vertices[:, 0] - center_x) == side
    shoulder_band = side_mask & (y_ratio >= 0.70) & (y_ratio <= 0.82)
    elbow_band = side_mask & (y_ratio >= 0.58) & (y_ratio <= 0.72)
    shoulder_candidates = vertices[shoulder_band] if np.any(shoulder_band) else vertices[side_mask]
    elbow_candidates = vertices[elbow_band] if np.any(elbow_band) else vertices[side_mask]
    shoulder = np.array(
        [
            float(np.percentile(shoulder_candidates[:, 0], 8 if side < 0 else 92)),
            float(np.percentile(shoulder_candidates[:, 1], 72)),
            float(np.median(shoulder_candidates[:, 2])),
        ],
        dtype=np.float64,
    )
    elbow = np.array(
        [
            float(np.percentile(elbow_candidates[:, 0], 4 if side < 0 else 96)),
            float(np.percentile(elbow_candidates[:, 1], 44)),
            float(np.median(elbow_candidates[:, 2])),
        ],
        dtype=np.float64,
    )
    return _make_arm_context(vertices, shoulder, elbow, height, side=side)


def _make_arm_context(
    vertices: np.ndarray,
    shoulder: np.ndarray,
    elbow: np.ndarray,
    height: float,
    *,
    side: float,
) -> _ArmContext:
    axis_vector = elbow - shoulder
    length = max(float(np.linalg.norm(axis_vector)), height * 0.12)
    axis = axis_vector / length
    axial = (vertices - shoulder) @ axis
    radial = np.linalg.norm((vertices - shoulder) - (axis * axial[:, None]), axis=1)
    local = (
        (axial >= -height * 0.025)
        & (axial <= length * 0.62)
        & (radial <= height * 0.13)
    )
    radius = float(np.percentile(radial[local], 70)) if np.any(local) else height * 0.038
    return _ArmContext(
        side=side,
        shoulder=np.asarray(shoulder, dtype=np.float64),
        elbow=np.asarray(elbow, dtype=np.float64),
        axis=axis,
        length=length,
        radius=max(radius, height * 0.032),
    )


def _ordered_loop_by_axes(
    vertices: np.ndarray,
    indices: list[int],
    *,
    axes: tuple[int, int],
    center: np.ndarray,
) -> np.ndarray:
    if not indices:
        return np.asarray([], dtype=np.int32)

    index_array = np.asarray(indices, dtype=np.int32)
    points = vertices[index_array]
    vectors = points[:, axes] - center[list(axes)]
    order = np.argsort(np.arctan2(vectors[:, 1], vectors[:, 0]))
    return index_array[order]


def _ordered_sleeve_ring(
    vertices: np.ndarray,
    indices: list[int],
    arm: _ArmContext,
) -> np.ndarray:
    if not indices:
        return np.asarray([], dtype=np.int32)

    index_array = np.asarray(indices, dtype=np.int32)
    radial = _arm_radial_vectors(vertices[index_array], arm)
    order = np.argsort(np.arctan2(radial[:, 2], radial[:, 1]))
    return index_array[order]


def _smooth_ordered_loop(
    vertices: np.ndarray,
    loop: np.ndarray,
    *,
    strength: float,
    vertical_strength: float,
) -> np.ndarray:
    if len(loop) < 4:
        return vertices

    smoothed = vertices.copy()
    for loop_index, index in enumerate(loop):
        previous_point = vertices[loop[(loop_index - 1) % len(loop)]]
        next_point = vertices[loop[(loop_index + 1) % len(loop)]]
        average = (previous_point + next_point) * 0.5
        target = vertices[index].copy()
        target[0] = (target[0] * (1.0 - strength)) + (average[0] * strength)
        target[2] = (target[2] * (1.0 - strength)) + (average[2] * strength)
        target[1] = (target[1] * (1.0 - vertical_strength)) + (average[1] * vertical_strength)
        smoothed[index] = target

    return smoothed


def _build_vertex_adjacency(
    vertex_count: int,
    faces: np.ndarray,
) -> list[set[int]]:
    adjacency: list[set[int]] = [set() for _ in range(vertex_count)]
    for face in faces:
        a, b, c = (int(face[0]), int(face[1]), int(face[2]))
        adjacency[a].update((b, c))
        adjacency[b].update((a, c))
        adjacency[c].update((a, b))

    return adjacency


def _boundary_vertex_components(faces: np.ndarray) -> list[list[int]]:
    edge_counts: dict[tuple[int, int], int] = {}
    for face in faces:
        for start, end in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            edge = tuple(sorted((int(start), int(end))))
            edge_counts[edge] = edge_counts.get(edge, 0) + 1

    adjacency: dict[int, set[int]] = {}
    for start, end in (edge for edge, count in edge_counts.items() if count == 1):
        adjacency.setdefault(start, set()).add(end)
        adjacency.setdefault(end, set()).add(start)

    components: list[list[int]] = []
    seen: set[int] = set()
    for start in adjacency:
        if start in seen:
            continue

        stack = [start]
        seen.add(start)
        component: list[int] = []
        while stack:
            vertex_index = stack.pop()
            component.append(vertex_index)
            for neighbor in adjacency[vertex_index]:
                if neighbor in seen:
                    continue
                seen.add(neighbor)
                stack.append(neighbor)
        components.append(component)

    return components


def _topology_diagnostics(
    faces: np.ndarray,
    curves: dict[str, list[int]],
) -> dict[str, Any]:
    face_array = np.asarray(faces, dtype=np.int32)
    edge_counts = _edge_counts(face_array)
    boundary_edges = [edge for edge, count in edge_counts.items() if count == 1]
    nonmanifold_edges = [edge for edge, count in edge_counts.items() if count > 2]
    boundary_components = _edge_components(boundary_edges)
    face_components = _face_components(face_array, edge_counts)
    left_seam = _seam_continuity(curves.get("left_armhole_loop", []), edge_counts)
    right_seam = _seam_continuity(curves.get("right_armhole_loop", []), edge_counts)
    expected_hole_count = 4
    hole_count = len(boundary_components)
    return {
        "disconnected_mesh_islands": int(len(face_components)),
        "component_face_counts": [int(len(component)) for component in face_components],
        "boundary_edge_count": int(len(boundary_edges)),
        "nonmanifold_edge_count": int(len(nonmanifold_edges)),
        "hole_count": int(hole_count),
        "expected_hole_count": expected_hole_count,
        "unexpected_hole_count": int(abs(hole_count - expected_hole_count)),
        "boundary_component_vertex_counts": [int(len(component)) for component in boundary_components],
        "left_armhole_seam_continuous": bool(left_seam["continuous"]),
        "right_armhole_seam_continuous": bool(right_seam["continuous"]),
        "left_armhole_bad_edge_count": int(left_seam["bad_edge_count"]),
        "right_armhole_bad_edge_count": int(right_seam["bad_edge_count"]),
        "seam_continuity_valid": bool(left_seam["continuous"] and right_seam["continuous"]),
        "manifold_with_expected_openings": bool(
            len(face_components) == 1
            and len(nonmanifold_edges) == 0
            and hole_count == expected_hole_count
            and left_seam["continuous"]
            and right_seam["continuous"]
        ),
    }


def _validate_topology_or_raise(topology: dict[str, Any]) -> None:
    if topology["nonmanifold_edge_count"] > 0:
        raise ValueError(
            "Generated T-shirt mesh is non-manifold: "
            f"{topology['nonmanifold_edge_count']} non-manifold edges."
        )
    if topology["disconnected_mesh_islands"] != 1:
        raise ValueError(
            "Generated T-shirt mesh is disconnected: "
            f"{topology['disconnected_mesh_islands']} mesh islands."
        )
    if topology["hole_count"] != topology["expected_hole_count"]:
        raise ValueError(
            "Generated T-shirt mesh has unexpected open boundaries: "
            f"{topology['hole_count']} boundary loops, expected "
            f"{topology['expected_hole_count']} garment openings."
        )
    if not topology["seam_continuity_valid"]:
        raise ValueError(
            "Generated T-shirt mesh has discontinuous armhole sleeve seams: "
            f"left_bad={topology['left_armhole_bad_edge_count']}, "
            f"right_bad={topology['right_armhole_bad_edge_count']}."
        )


def _edge_counts(faces: np.ndarray) -> dict[tuple[int, int], int]:
    edge_counts: dict[tuple[int, int], int] = {}
    for face in faces:
        for start, end in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            edge = tuple(sorted((int(start), int(end))))
            edge_counts[edge] = edge_counts.get(edge, 0) + 1
    return edge_counts


def _edge_components(edges: list[tuple[int, int]]) -> list[list[int]]:
    adjacency: dict[int, set[int]] = {}
    for start, end in edges:
        adjacency.setdefault(start, set()).add(end)
        adjacency.setdefault(end, set()).add(start)

    components: list[list[int]] = []
    seen: set[int] = set()
    for start in adjacency:
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        component: list[int] = []
        while stack:
            vertex_index = stack.pop()
            component.append(vertex_index)
            for neighbor in adjacency[vertex_index]:
                if neighbor in seen:
                    continue
                seen.add(neighbor)
                stack.append(neighbor)
        components.append(component)
    return components


def _face_components(
    faces: np.ndarray,
    edge_counts: dict[tuple[int, int], int],
) -> list[list[int]]:
    edge_to_faces: dict[tuple[int, int], list[int]] = {
        edge: [] for edge in edge_counts
    }
    for face_index, face in enumerate(faces):
        for start, end in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            edge = tuple(sorted((int(start), int(end))))
            edge_to_faces[edge].append(face_index)

    neighbors: list[set[int]] = [set() for _ in range(len(faces))]
    for face_indices in edge_to_faces.values():
        if len(face_indices) < 2:
            continue
        for face_index in face_indices:
            neighbors[face_index].update(
                other for other in face_indices if other != face_index
            )

    components: list[list[int]] = []
    seen = np.zeros(len(faces), dtype=bool)
    for face_index in range(len(faces)):
        if seen[face_index]:
            continue
        stack = [face_index]
        seen[face_index] = True
        component: list[int] = []
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbor in neighbors[current]:
                if seen[neighbor]:
                    continue
                seen[neighbor] = True
                stack.append(neighbor)
        components.append(component)
    return components


def _seam_continuity(
    loop: list[int],
    edge_counts: dict[tuple[int, int], int],
) -> dict[str, Any]:
    if len(loop) < 3:
        return {"continuous": False, "bad_edge_count": len(loop)}

    bad_edges = 0
    for loop_index, start in enumerate(loop):
        end = loop[(loop_index + 1) % len(loop)]
        count = edge_counts.get(tuple(sorted((int(start), int(end)))), 0)
        if count != 2:
            bad_edges += 1
    return {"continuous": bad_edges == 0, "bad_edge_count": bad_edges}


def _select_neckline_boundary_component(
    vertices: np.ndarray,
    components: list[list[int]],
    metrics: _BodyMetrics,
) -> list[int]:
    candidates: list[tuple[float, list[int]]] = []
    for component in components:
        if len(component) < 6:
            continue
        points = vertices[np.asarray(component, dtype=np.int32)]
        center_distance = abs(float(points[:, 0].mean()) - metrics.center_x)
        if center_distance > metrics.height * 0.135:
            continue
        candidates.append((float(points[:, 1].mean()), component))

    if not candidates:
        return []

    return max(candidates, key=lambda item: item[0])[1]


def _select_hem_boundary_component(
    vertices: np.ndarray,
    components: list[list[int]],
    metrics: _BodyMetrics,
) -> list[int]:
    candidates: list[tuple[float, list[int]]] = []
    for component in components:
        if len(component) < 8:
            continue
        points = vertices[np.asarray(component, dtype=np.int32)]
        center_distance = abs(float(points[:, 0].mean()) - metrics.center_x)
        if center_distance > metrics.height * 0.160:
            continue
        candidates.append((float(points[:, 1].mean()), component))

    if not candidates:
        return []

    return min(candidates, key=lambda item: item[0])[1]


def _project_on_arm_axis(points: np.ndarray, arm: _ArmContext) -> np.ndarray:
    return (points - arm.shoulder) @ arm.axis


def _arm_radial_vectors(points: np.ndarray, arm: _ArmContext) -> np.ndarray:
    axial = _project_on_arm_axis(points, arm)
    axis_points = arm.shoulder + (arm.axis * axial[:, None])
    return points - axis_points


def _normalize_vector(
    vector: np.ndarray,
    *,
    fallback: np.ndarray,
) -> np.ndarray:
    magnitude = float(np.linalg.norm(vector))
    if magnitude < 1e-12:
        return fallback

    return vector / magnitude


def _nearest_vertex(vertices: np.ndarray, target: np.ndarray) -> np.ndarray:
    distances = np.linalg.norm(vertices - target, axis=1)
    return vertices[int(np.argmin(distances))]


def _nearest_distances(points: np.ndarray, candidates: np.ndarray, *, chunk_size: int = 256) -> np.ndarray:
    distances: list[np.ndarray] = []
    for start in range(0, len(points), chunk_size):
        chunk = points[start:start + chunk_size]
        squared = np.sum((chunk[:, None, :] - candidates[None, :, :]) ** 2, axis=2)
        distances.append(np.sqrt(np.min(squared, axis=1)))

    return np.concatenate(distances) if distances else np.empty(0, dtype=np.float64)


def _round_point(point: np.ndarray) -> list[float]:
    return [round(float(value), 5) for value in point]


def _smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 0.0

    t = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return float(t * t * (3.0 - (2.0 * t)))


def _y_ratio(y_values: np.ndarray, metrics: _BodyMetrics) -> np.ndarray:
    return (np.asarray(y_values, dtype=np.float64) - metrics.y_min) / metrics.height


def _as_vertices(vertices) -> np.ndarray:
    array = np.asarray(vertices, dtype=np.float64)
    if array.ndim != 2 or array.shape[1] != 3:
        raise ValueError("vertices must be an Nx3 array")

    return array


def _as_faces(faces) -> np.ndarray:
    array = np.asarray(faces, dtype=np.int32)
    if array.size == 0:
        return array.reshape((0, 3))
    if array.ndim != 2 or array.shape[1] != 3:
        raise ValueError("faces must be an Mx3 array")

    return array
