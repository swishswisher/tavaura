from __future__ import annotations

from dataclasses import dataclass

import numpy as np


TORSO_FRONT = "TORSO_FRONT"
TORSO_BACK = "TORSO_BACK"
LEFT_SLEEVE = "LEFT_SLEEVE"
RIGHT_SLEEVE = "RIGHT_SLEEVE"
COLLAR = "COLLAR"
LEFT_ARMHOLE = "LEFT_ARMHOLE"
RIGHT_ARMHOLE = "RIGHT_ARMHOLE"
HEM = "HEM"

REGION_PRIORITY = (
    TORSO_FRONT,
    TORSO_BACK,
    LEFT_ARMHOLE,
    RIGHT_ARMHOLE,
    LEFT_SLEEVE,
    RIGHT_SLEEVE,
    COLLAR,
    HEM,
)
LEGACY_REGION_MAP = {
    "torso": TORSO_FRONT,
    "left_sleeve": LEFT_SLEEVE,
    "right_sleeve": RIGHT_SLEEVE,
    "underarm": LEFT_ARMHOLE,
    "collar": COLLAR,
    "hem": HEM,
}
REGION_ATTRACTION = {
    TORSO_FRONT: 0.125,
    TORSO_BACK: 0.105,
    LEFT_SLEEVE: 0.060,
    RIGHT_SLEEVE: 0.060,
    COLLAR: 0.018,
    LEFT_ARMHOLE: 0.052,
    RIGHT_ARMHOLE: 0.052,
    HEM: 0.024,
}
REGION_OFFSETS = {
    TORSO_FRONT: 0.044,
    TORSO_BACK: 0.046,
    LEFT_SLEEVE: 0.040,
    RIGHT_SLEEVE: 0.040,
    COLLAR: 0.020,
    LEFT_ARMHOLE: 0.042,
    RIGHT_ARMHOLE: 0.042,
    HEM: 0.058,
}
REGION_MAX_MOVE = {
    TORSO_FRONT: 0.018,
    TORSO_BACK: 0.016,
    LEFT_SLEEVE: 0.012,
    RIGHT_SLEEVE: 0.012,
    COLLAR: 0.006,
    LEFT_ARMHOLE: 0.008,
    RIGHT_ARMHOLE: 0.008,
    HEM: 0.006,
}
REGION_SMOOTHING = {
    TORSO_FRONT: 0.085,
    TORSO_BACK: 0.075,
    LEFT_SLEEVE: 0.038,
    RIGHT_SLEEVE: 0.038,
    COLLAR: 0.018,
    LEFT_ARMHOLE: 0.030,
    RIGHT_ARMHOLE: 0.030,
    HEM: 0.022,
}
DEFAULT_REGION = TORSO_FRONT


@dataclass(frozen=True)
class _ArmContext:
    shoulder: np.ndarray
    elbow: np.ndarray
    axis: np.ndarray
    length: float
    radius: float


@dataclass(frozen=True)
class _BodyContext:
    vertices: np.ndarray
    faces: np.ndarray
    joints: np.ndarray | None
    y_min: float
    y_max: float
    height: float
    center_x: float
    center_z: float
    left_arm: _ArmContext
    right_arm: _ArmContext


def fit_garment_to_body(
    garment_vertices,
    garment_regions,
    body_vertices,
    body_faces,
    *,
    garment_faces=None,
    body_joints=None,
    garment_region_labels=None,
    garment_curves=None,
) -> np.ndarray:
    """Fit a structured garment with region-specific deterministic constraints.

    The public function remains compatible with older callers. New panel-based
    callers can pass explicit region labels, panel curves, garment faces, and
    SMPL-X joints for arm-local sleeve fitting.
    """
    garment = _as_vertices(garment_vertices)
    body = _as_vertices(body_vertices)
    body_mesh_faces = _as_faces(body_faces)
    mesh_faces = _as_faces(garment_faces) if garment_faces is not None else np.empty((0, 3), dtype=np.int32)
    if len(garment) == 0:
        return garment.copy()

    explicit_regions, labels = _normalize_regions(
        garment_regions,
        garment_region_labels,
        len(garment),
    )
    explicit_regions, labels = _apply_curve_region_overrides(
        explicit_regions,
        labels,
        garment_curves,
        len(garment),
    )
    context = _build_body_context(body, body_mesh_faces, body_joints)
    fitted = garment.copy()

    for region_name in REGION_PRIORITY:
        indices = _valid_region_indices(explicit_regions, region_name, len(garment))
        if len(indices) == 0:
            continue

        if region_name in (LEFT_SLEEVE, RIGHT_SLEEVE):
            fitted = _fit_sleeve_region_arm_local(
                original=garment,
                fitted=fitted,
                indices=indices,
                region_name=region_name,
                context=context,
            )
        elif region_name in (LEFT_ARMHOLE, RIGHT_ARMHOLE):
            fitted[indices] = _fit_armhole_region(
                original=garment[indices],
                current=fitted[indices],
                region_name=region_name,
                context=context,
            )
        else:
            fitted[indices] = _fit_directional_region(
                points=fitted[indices],
                region_name=region_name,
                context=context,
            )

    fitted = _stabilize_collar(garment, fitted, explicit_regions, context)
    fitted = _stabilize_hem(garment, fitted, explicit_regions)
    fitted = _relax_garment(
        original=garment,
        fitted=fitted,
        faces=mesh_faces,
        labels=labels,
        context=context,
        iterations=2,
    )
    fitted = _stabilize_collar(garment, fitted, explicit_regions, context)
    fitted = _stabilize_hem(garment, fitted, explicit_regions)
    fitted = _restore_minimum_offsets(fitted, explicit_regions, context)
    return _limit_total_displacement(garment, fitted, explicit_regions, context)


def get_candidate_body_vertices_for_region(
    region_name,
    body_vertices,
) -> np.ndarray:
    body = _as_vertices(body_vertices)
    context = _build_body_context(body, np.empty((0, 3), dtype=np.int32), None)
    return context.vertices[_candidate_body_indices_for_region(_normalize_region_name(region_name), context)]


def _normalize_regions(
    garment_regions,
    garment_region_labels,
    vertex_count: int,
) -> tuple[dict[str, list[int]], tuple[str, ...]]:
    if garment_region_labels is not None and len(garment_region_labels) == vertex_count:
        labels = tuple(_normalize_region_name(label) for label in garment_region_labels)
        return _regions_from_labels(labels), labels

    labels = [DEFAULT_REGION for _ in range(vertex_count)]
    if isinstance(garment_regions, dict):
        for source_name, indices in garment_regions.items():
            region_name = _normalize_region_name(source_name)
            for index in indices:
                if 0 <= int(index) < vertex_count:
                    labels[int(index)] = region_name

    normalized = tuple(labels)
    return _regions_from_labels(normalized), normalized


def _normalize_region_name(region_name) -> str:
    key = str(region_name).strip()
    if key in REGION_PRIORITY:
        return key

    return LEGACY_REGION_MAP.get(key.lower(), DEFAULT_REGION)


def _apply_curve_region_overrides(
    regions: dict[str, list[int]],
    labels: tuple[str, ...],
    garment_curves,
    vertex_count: int,
) -> tuple[dict[str, list[int]], tuple[str, ...]]:
    if not isinstance(garment_curves, dict):
        return regions, labels

    updated_labels = list(labels)
    curve_region_map = {
        "neckline_loop": COLLAR,
        "hem_loop": HEM,
        "left_armhole_loop": LEFT_ARMHOLE,
        "left_armhole_panel_loop": LEFT_ARMHOLE,
        "right_armhole_loop": RIGHT_ARMHOLE,
        "right_armhole_panel_loop": RIGHT_ARMHOLE,
        "left_sleeve_cuff_loop": LEFT_SLEEVE,
        "right_sleeve_cuff_loop": RIGHT_SLEEVE,
    }
    for curve_name, region_name in curve_region_map.items():
        for index in garment_curves.get(curve_name, []):
            vertex_index = int(index)
            if 0 <= vertex_index < vertex_count:
                updated_labels[vertex_index] = region_name

    normalized = tuple(updated_labels)
    return _regions_from_labels(normalized), normalized


def _regions_from_labels(labels: tuple[str, ...]) -> dict[str, list[int]]:
    return {
        region_name: [index for index, label in enumerate(labels) if label == region_name]
        for region_name in REGION_PRIORITY
    }


def _fit_directional_region(
    points: np.ndarray,
    region_name: str,
    context: _BodyContext,
) -> np.ndarray:
    candidate_indices = _candidate_body_indices_for_region(region_name, context)
    if len(candidate_indices) == 0:
        return points

    candidates = context.vertices[candidate_indices]
    targets = _directional_body_targets(points, candidates, region_name, context)
    outward = _radial_directions(points, context)
    shell_offset = REGION_OFFSETS[region_name] * context.height
    attraction = REGION_ATTRACTION[region_name]
    max_move = REGION_MAX_MOVE[region_name] * context.height
    deltas = ((targets + (outward * shell_offset)) - points) * attraction
    return points + _clamp_vector_lengths(deltas, max_move)


def _fit_armhole_region(
    *,
    original: np.ndarray,
    current: np.ndarray,
    region_name: str,
    context: _BodyContext,
) -> np.ndarray:
    arm = context.left_arm if region_name == LEFT_ARMHOLE else context.right_arm
    side = -1.0 if region_name == LEFT_ARMHOLE else 1.0
    fitted = current.copy()
    radial = _arm_radial_vectors(fitted, arm)
    radial_dirs = _normalize_rows(radial, fallback=np.array([0.0, 0.0, 1.0], dtype=np.float64))
    axial = _project_on_arm_axis(fitted, arm)
    axis_points = arm.shoulder + (arm.axis * axial[:, None])
    target_radius = max(arm.radius + (context.height * 0.044), context.height * 0.052)
    target = axis_points + (radial_dirs * target_radius)
    target[:, 0] = np.maximum(target[:, 0], context.center_x + (context.height * 0.105)) if side > 0 else np.minimum(target[:, 0], context.center_x - (context.height * 0.105))
    deltas = (target - fitted) * REGION_ATTRACTION[region_name]
    deltas = _clamp_vector_lengths(deltas, REGION_MAX_MOVE[region_name] * context.height)
    return original * 0.18 + (fitted + deltas) * 0.82


def _fit_sleeve_region_arm_local(
    *,
    original: np.ndarray,
    fitted: np.ndarray,
    indices: np.ndarray,
    region_name: str,
    context: _BodyContext,
    bin_count: int = 8,
) -> np.ndarray:
    arm = context.left_arm if region_name == LEFT_SLEEVE else context.right_arm
    result = fitted.copy()
    axial = _project_on_arm_axis(original[indices], arm)
    min_axial = float(axial.min())
    max_axial = float(axial.max())
    span = max(max_axial - min_axial, 1e-9)
    edges = np.linspace(min_axial, max_axial, bin_count + 1)
    for bin_index in range(bin_count):
        lower = edges[bin_index]
        upper = edges[bin_index + 1]
        if bin_index == bin_count - 1:
            mask = (axial >= lower) & (axial <= upper)
        else:
            mask = (axial >= lower) & (axial < upper)

        ring_indices = indices[mask]
        if len(ring_indices) < 4:
            continue

        progress = float(np.clip((((lower + upper) * 0.5) - min_axial) / span, 0.0, 1.0))
        current = result[ring_indices]
        original_ring = original[ring_indices]
        current_axial = _project_on_arm_axis(current, arm)
        axis_points = arm.shoulder + (arm.axis * current_axial[:, None])
        current_radial = current - axis_points
        original_radial = original_ring - (arm.shoulder + (_project_on_arm_axis(original_ring, arm)[:, None] * arm.axis))
        radial_dirs = _normalize_rows(current_radial, fallback=np.array([0.0, 0.0, 1.0], dtype=np.float64))
        original_radius = max(
            float(np.median(np.linalg.norm(original_radial, axis=1))),
            context.height * 0.046,
        )
        target_radius = max(
            arm.radius + (context.height * _lerp(0.044, 0.032, progress)),
            original_radius * _lerp(1.02, 0.92, progress),
        )
        target = axis_points + (radial_dirs * target_radius)
        root_preservation = 1.0 - _smoothstep(0.0, 0.32, progress)
        target = (target * (1.0 - (root_preservation * 0.30))) + (original_ring * root_preservation * 0.30)
        deltas = (target - current) * _lerp(0.34, 0.58, progress)
        deltas = _clamp_vector_lengths(deltas, REGION_MAX_MOVE[region_name] * context.height)
        result[ring_indices] += deltas

    return result


def _directional_body_targets(
    points: np.ndarray,
    candidates: np.ndarray,
    region_name: str,
    context: _BodyContext,
) -> np.ndarray:
    targets = np.zeros_like(points)
    y_window = _region_y_window(region_name, context.height)
    candidate_xz = candidates[:, [0, 2]]
    center_xz = np.array([context.center_x, context.center_z], dtype=np.float64)
    candidate_vectors = candidate_xz - center_xz
    candidate_radii = np.linalg.norm(candidate_vectors, axis=1)
    candidate_dirs = _normalize_2d(candidate_vectors)

    for point_index, point in enumerate(points):
        local_mask = np.abs(candidates[:, 1] - point[1]) <= y_window
        if region_name in (TORSO_FRONT, TORSO_BACK):
            z_side = 1.0 if region_name == TORSO_FRONT else -1.0
            local_mask &= np.sign(candidates[:, 2] - context.center_z) == z_side
        local_candidates = candidates[local_mask] if np.any(local_mask) else candidates
        local_dirs = candidate_dirs[local_mask] if np.any(local_mask) else candidate_dirs
        local_radii = candidate_radii[local_mask] if np.any(local_mask) else candidate_radii
        point_vector = np.array(
            [point[0] - context.center_x, point[2] - context.center_z],
            dtype=np.float64,
        )
        point_radius = max(float(np.linalg.norm(point_vector)), 1e-9)
        point_dir = point_vector / point_radius
        angular_distance = 1.0 - np.clip(local_dirs @ point_dir, -1.0, 1.0)
        y_distance = np.abs(local_candidates[:, 1] - point[1]) / context.height
        radial_distance = np.abs(local_radii - point_radius) / context.height
        score = (angular_distance * 2.6) + (y_distance * 1.8) + (radial_distance * 0.24)
        targets[point_index] = local_candidates[int(np.argmin(score))]

    return targets


def _candidate_body_indices_for_region(
    region_name: str,
    context: _BodyContext,
) -> np.ndarray:
    vertices = context.vertices
    y_ratio = (vertices[:, 1] - context.y_min) / context.height
    x_ratio = (vertices[:, 0] - context.center_x) / context.height
    z_ratio = (vertices[:, 2] - context.center_z) / context.height
    abs_x = np.abs(x_ratio)
    abs_z = np.abs(z_ratio)

    if region_name == TORSO_FRONT:
        mask = (y_ratio >= 0.43) & (y_ratio <= 0.79) & (abs_x <= 0.31) & (z_ratio >= -0.04) & (abs_z <= 0.20)
    elif region_name == TORSO_BACK:
        mask = (y_ratio >= 0.43) & (y_ratio <= 0.80) & (abs_x <= 0.31) & (z_ratio <= 0.04) & (abs_z <= 0.20)
    elif region_name == COLLAR:
        mask = (y_ratio >= 0.68) & (y_ratio <= 0.85) & (abs_x <= 0.22) & (abs_z <= 0.17)
    elif region_name == HEM:
        mask = (y_ratio >= 0.42) & (y_ratio <= 0.55) & (abs_x <= 0.32) & (abs_z <= 0.20)
    elif region_name == LEFT_ARMHOLE:
        mask = (y_ratio >= 0.56) & (y_ratio <= 0.75) & (x_ratio <= -0.11) & (x_ratio >= -0.42) & (abs_z <= 0.19)
    elif region_name == RIGHT_ARMHOLE:
        mask = (y_ratio >= 0.56) & (y_ratio <= 0.75) & (x_ratio >= 0.11) & (x_ratio <= 0.42) & (abs_z <= 0.19)
    elif region_name == LEFT_SLEEVE:
        return _arm_candidate_indices(context.left_arm, context.vertices, context.height)
    elif region_name == RIGHT_SLEEVE:
        return _arm_candidate_indices(context.right_arm, context.vertices, context.height)
    else:
        mask = (y_ratio >= 0.43) & (y_ratio <= 0.80) & (abs_x <= 0.32) & (abs_z <= 0.20)

    indices = np.nonzero(mask)[0].astype(np.int32)
    if len(indices) > 0:
        return indices

    fallback = (y_ratio >= 0.43) & (y_ratio <= 0.80) & (abs_x <= 0.34)
    return np.nonzero(fallback)[0].astype(np.int32)


def _arm_candidate_indices(
    arm: _ArmContext,
    vertices: np.ndarray,
    height: float,
) -> np.ndarray:
    axial = _project_on_arm_axis(vertices, arm)
    radial = np.linalg.norm(_arm_radial_vectors(vertices, arm), axis=1)
    mask = (
        (axial >= -height * 0.025)
        & (axial <= arm.length + (height * 0.10))
        & (radial <= height * 0.145)
    )
    return np.nonzero(mask)[0].astype(np.int32)


def _stabilize_collar(
    original: np.ndarray,
    fitted: np.ndarray,
    regions: dict[str, list[int]],
    context: _BodyContext,
) -> np.ndarray:
    indices = _valid_region_indices(regions, COLLAR, len(original))
    if len(indices) < 4:
        return fitted

    result = fitted.copy()
    ordered = _order_loop_by_angle(result[indices], axes=(0, 2))
    loop_indices = indices[ordered]
    original_center = original[loop_indices].mean(axis=0)
    fitted_center = result[loop_indices].mean(axis=0)
    original_rel = original[loop_indices] - original_center
    fitted_rel = result[loop_indices] - fitted_center
    original_radius = np.linalg.norm(original_rel[:, [0, 2]], axis=1)
    fitted_radius = np.linalg.norm(fitted_rel[:, [0, 2]], axis=1)
    min_radius = original_radius * 0.94
    too_small = fitted_radius < min_radius
    if np.any(too_small):
        scale = np.ones(len(loop_indices), dtype=np.float64)
        scale[too_small] = min_radius[too_small] / np.maximum(fitted_radius[too_small], 1e-9)
        fitted_rel[:, 0] *= scale
        fitted_rel[:, 2] *= scale

    stabilized = fitted_center + (fitted_rel * 0.62) + (original_rel * 0.38)
    stabilized[:, 1] = (result[loop_indices, 1] * 0.88) + (stabilized[:, 1] * 0.12)
    result[loop_indices] = _tangential_loop_smooth(stabilized, vertical_weight=0.08)
    result[loop_indices, 1] = np.maximum(
        result[loop_indices, 1],
        context.y_min + (context.height * 0.690),
    )
    return result


def _stabilize_hem(
    original: np.ndarray,
    fitted: np.ndarray,
    regions: dict[str, list[int]],
) -> np.ndarray:
    indices = _valid_region_indices(regions, HEM, len(original))
    if len(indices) < 6:
        return fitted

    result = fitted.copy()
    original_center = original[indices].mean(axis=0)
    fitted_center = result[indices].mean(axis=0)
    result[indices] = fitted_center + ((result[indices] - fitted_center) * 0.70) + ((original[indices] - original_center) * 0.30)
    return result


def _relax_garment(
    *,
    original: np.ndarray,
    fitted: np.ndarray,
    faces: np.ndarray,
    labels: tuple[str, ...],
    context: _BodyContext,
    iterations: int,
) -> np.ndarray:
    if len(faces) == 0:
        return fitted

    adjacency = _build_vertex_adjacency(len(fitted), faces)
    edges = _unique_edges(faces)
    weights = np.asarray(
        [REGION_SMOOTHING.get(label, 0.04) for label in labels],
        dtype=np.float64,
    )
    relaxed = fitted.copy()
    for _ in range(iterations):
        relaxed = _laplacian_smooth_with_weights(relaxed, adjacency, weights)
        relaxed = _stabilize_edge_lengths(original, relaxed, edges, labels, strength=0.10)
        relaxed = _normal_preserving_relax(original, relaxed, faces, context, strength=0.05)

    return relaxed


def _laplacian_smooth_with_weights(
    vertices: np.ndarray,
    adjacency: list[set[int]],
    weights: np.ndarray,
) -> np.ndarray:
    smoothed = vertices.copy()
    for vertex_index, neighbors in enumerate(adjacency):
        if not neighbors:
            continue

        neighbor_average = vertices[list(neighbors)].mean(axis=0)
        smoothed[vertex_index] += (neighbor_average - vertices[vertex_index]) * weights[vertex_index]

    return smoothed


def _stabilize_edge_lengths(
    original: np.ndarray,
    vertices: np.ndarray,
    edges: np.ndarray,
    labels: tuple[str, ...],
    *,
    strength: float,
) -> np.ndarray:
    adjusted = vertices.copy()
    for start, end in edges:
        current_vector = adjusted[end] - adjusted[start]
        current_length = float(np.linalg.norm(current_vector))
        if current_length <= 1e-9:
            continue

        target_length = float(np.linalg.norm(original[end] - original[start]))
        correction = (current_length - target_length) * strength
        direction = current_vector / current_length
        start_weight = _edge_region_mobility(labels[start])
        end_weight = _edge_region_mobility(labels[end])
        total = max(start_weight + end_weight, 1e-9)
        adjusted[start] += direction * correction * (start_weight / total)
        adjusted[end] -= direction * correction * (end_weight / total)

    return adjusted


def _normal_preserving_relax(
    original: np.ndarray,
    vertices: np.ndarray,
    faces: np.ndarray,
    context: _BodyContext,
    *,
    strength: float,
) -> np.ndarray:
    del faces
    outward = _radial_directions(vertices, context)
    delta = vertices - original
    normal_component = np.einsum("ij,ij->i", delta, outward)
    tangential_delta = delta - (outward * normal_component[:, None])
    return original + (tangential_delta * (1.0 - strength)) + (outward * normal_component[:, None])


def _restore_minimum_offsets(
    vertices: np.ndarray,
    regions: dict[str, list[int]],
    context: _BodyContext,
) -> np.ndarray:
    restored = vertices.copy()
    for region_name in REGION_PRIORITY:
        indices = _valid_region_indices(regions, region_name, len(vertices))
        if len(indices) == 0 or region_name in (LEFT_SLEEVE, RIGHT_SLEEVE):
            continue

        candidates = context.vertices[_candidate_body_indices_for_region(region_name, context)]
        targets = _directional_body_targets(restored[indices], candidates, region_name, context)
        outward = _radial_directions(restored[indices], context)
        min_offset = REGION_OFFSETS[region_name] * context.height * 0.60
        distance = np.einsum("ij,ij->i", restored[indices] - targets, outward)
        too_close = distance < min_offset
        if np.any(too_close):
            restored[indices[too_close]] += outward[too_close] * (min_offset - distance[too_close])[:, None]

    return restored


def _limit_total_displacement(
    original: np.ndarray,
    fitted: np.ndarray,
    regions: dict[str, list[int]],
    context: _BodyContext,
) -> np.ndarray:
    limited = fitted.copy()
    for region_name in REGION_PRIORITY:
        indices = _valid_region_indices(regions, region_name, len(original))
        if len(indices) == 0:
            continue

        max_move = REGION_MAX_MOVE[region_name] * context.height * 1.75
        deltas = limited[indices] - original[indices]
        limited[indices] = original[indices] + _clamp_vector_lengths(deltas, max_move)

    return limited


def _candidate_arm_from_joints(
    body_vertices: np.ndarray,
    center_x: float,
    height: float,
    joints,
    *,
    side: float,
) -> _ArmContext | None:
    if joints is None:
        return None

    joint_array = np.asarray(joints, dtype=np.float64)
    if joint_array.ndim == 3:
        joint_array = joint_array[0]
    if joint_array.ndim != 2 or joint_array.shape[0] <= 19:
        return None

    pairs = [
        (joint_array[16], joint_array[18]),
        (joint_array[17], joint_array[19]),
    ]
    pairs = sorted(pairs, key=lambda pair: pair[0][0])
    shoulder, elbow = pairs[0] if side < 0 else pairs[-1]
    return _make_arm_context(body_vertices, shoulder, elbow, height)


def _heuristic_arm_context(
    body_vertices: np.ndarray,
    center_x: float,
    y_min: float,
    height: float,
    *,
    side: float,
) -> _ArmContext:
    y_ratio = (body_vertices[:, 1] - y_min) / height
    side_mask = np.sign(body_vertices[:, 0] - center_x) == side
    shoulder_band = side_mask & (y_ratio >= 0.70) & (y_ratio <= 0.82)
    elbow_band = side_mask & (y_ratio >= 0.60) & (y_ratio <= 0.74)
    shoulder_candidates = body_vertices[shoulder_band] if np.any(shoulder_band) else body_vertices[side_mask]
    elbow_candidates = body_vertices[elbow_band] if np.any(elbow_band) else body_vertices[side_mask]
    if len(shoulder_candidates) == 0 or len(elbow_candidates) == 0:
        shoulder = np.array([center_x + side * height * 0.20, y_min + height * 0.75, 0.0], dtype=np.float64)
        elbow = shoulder + np.array([side * height * 0.20, -height * 0.05, 0.0], dtype=np.float64)
    else:
        shoulder = np.array(
            [
                float(np.percentile(shoulder_candidates[:, 0], 92 if side > 0 else 8)),
                float(np.percentile(shoulder_candidates[:, 1], 72)),
                float(np.median(shoulder_candidates[:, 2])),
            ],
            dtype=np.float64,
        )
        elbow = np.array(
            [
                float(np.percentile(elbow_candidates[:, 0], 95 if side > 0 else 5)),
                float(np.percentile(elbow_candidates[:, 1], 45)),
                float(np.median(elbow_candidates[:, 2])),
            ],
            dtype=np.float64,
        )

    return _make_arm_context(body_vertices, shoulder, elbow, height)


def _make_arm_context(
    body_vertices: np.ndarray,
    shoulder: np.ndarray,
    elbow: np.ndarray,
    height: float,
) -> _ArmContext:
    axis_vector = elbow - shoulder
    length = max(float(np.linalg.norm(axis_vector)), height * 0.10)
    axis = axis_vector / length
    axial = (body_vertices - shoulder) @ axis
    radial = np.linalg.norm((body_vertices - shoulder) - (axis * axial[:, None]), axis=1)
    local = (axial >= -height * 0.02) & (axial <= length + height * 0.06) & (radial <= height * 0.12)
    radius = float(np.percentile(radial[local], 70)) if np.any(local) else height * 0.036
    return _ArmContext(
        shoulder=shoulder,
        elbow=elbow,
        axis=axis,
        length=length,
        radius=max(radius, height * 0.030),
    )


def _build_body_context(
    body_vertices: np.ndarray,
    body_faces: np.ndarray,
    body_joints,
) -> _BodyContext:
    y_min = float(body_vertices[:, 1].min())
    y_max = float(body_vertices[:, 1].max())
    height = max(y_max - y_min, 1e-9)
    y_ratio = (body_vertices[:, 1] - y_min) / height
    torso_mask = (y_ratio >= 0.42) & (y_ratio <= 0.80)
    torso_vertices = body_vertices[torso_mask] if np.any(torso_mask) else body_vertices
    center_x = float(np.median(torso_vertices[:, 0]))
    center_z = float(np.median(torso_vertices[:, 2]))
    left_arm = _candidate_arm_from_joints(
        body_vertices,
        center_x,
        height,
        body_joints,
        side=-1.0,
    ) or _heuristic_arm_context(body_vertices, center_x, y_min, height, side=-1.0)
    right_arm = _candidate_arm_from_joints(
        body_vertices,
        center_x,
        height,
        body_joints,
        side=1.0,
    ) or _heuristic_arm_context(body_vertices, center_x, y_min, height, side=1.0)
    return _BodyContext(
        vertices=body_vertices,
        faces=body_faces,
        joints=None if body_joints is None else np.asarray(body_joints, dtype=np.float64),
        y_min=y_min,
        y_max=y_max,
        height=height,
        center_x=center_x,
        center_z=center_z,
        left_arm=left_arm,
        right_arm=right_arm,
    )


def _project_on_arm_axis(points: np.ndarray, arm: _ArmContext) -> np.ndarray:
    return (points - arm.shoulder) @ arm.axis


def _arm_radial_vectors(points: np.ndarray, arm: _ArmContext) -> np.ndarray:
    axial = _project_on_arm_axis(points, arm)
    axis_points = arm.shoulder + (arm.axis * axial[:, None])
    return points - axis_points


def _region_y_window(region_name: str, height: float) -> float:
    if region_name == COLLAR:
        return height * 0.028
    if region_name in (LEFT_ARMHOLE, RIGHT_ARMHOLE):
        return height * 0.045
    if region_name == HEM:
        return height * 0.042
    return height * 0.058


def _radial_directions(points: np.ndarray, context: _BodyContext) -> np.ndarray:
    vectors = np.zeros_like(points, dtype=np.float64)
    vectors[:, 0] = points[:, 0] - context.center_x
    vectors[:, 2] = points[:, 2] - context.center_z
    return _normalize_rows(vectors, fallback=np.array([0.0, 0.0, 1.0], dtype=np.float64))


def _valid_region_indices(
    regions: dict[str, list[int]],
    region_name: str,
    vertex_count: int,
) -> np.ndarray:
    indices = np.asarray(regions.get(region_name, []), dtype=np.int32)
    if len(indices) == 0:
        return indices

    return np.unique(indices[(indices >= 0) & (indices < vertex_count)])


def _build_vertex_adjacency(vertex_count: int, faces: np.ndarray) -> list[set[int]]:
    adjacency: list[set[int]] = [set() for _ in range(vertex_count)]
    for face in faces:
        a, b, c = (int(face[0]), int(face[1]), int(face[2]))
        adjacency[a].update((b, c))
        adjacency[b].update((a, c))
        adjacency[c].update((a, b))

    return adjacency


def _unique_edges(faces: np.ndarray) -> np.ndarray:
    edges = set()
    for face in faces:
        a, b, c = (int(face[0]), int(face[1]), int(face[2]))
        edges.add(tuple(sorted((a, b))))
        edges.add(tuple(sorted((b, c))))
        edges.add(tuple(sorted((c, a))))

    return np.asarray(sorted(edges), dtype=np.int32)


def _edge_region_mobility(region_name: str) -> float:
    if region_name == COLLAR:
        return 0.22
    if region_name == HEM:
        return 0.35
    if region_name in (LEFT_ARMHOLE, RIGHT_ARMHOLE):
        return 0.42
    return 1.0


def _order_loop_by_angle(points: np.ndarray, *, axes: tuple[int, int]) -> np.ndarray:
    center = points[:, axes].mean(axis=0)
    vectors = points[:, axes] - center
    return np.argsort(np.arctan2(vectors[:, 1], vectors[:, 0]))


def _tangential_loop_smooth(points: np.ndarray, *, vertical_weight: float) -> np.ndarray:
    if len(points) < 4:
        return points

    smoothed = points.copy()
    for index in range(len(points)):
        previous_point = points[(index - 1) % len(points)]
        next_point = points[(index + 1) % len(points)]
        neighbor_average = (previous_point + next_point) * 0.5
        smoothed[index, 0] = (points[index, 0] * 0.82) + (neighbor_average[0] * 0.18)
        smoothed[index, 2] = (points[index, 2] * 0.82) + (neighbor_average[2] * 0.18)
        smoothed[index, 1] = (points[index, 1] * (1.0 - vertical_weight)) + (neighbor_average[1] * vertical_weight)

    return smoothed


def _clamp_vector_lengths(vectors: np.ndarray, max_length: float) -> np.ndarray:
    lengths = np.linalg.norm(vectors, axis=1)
    scale = np.ones(len(vectors), dtype=np.float64)
    too_long = lengths > max_length
    scale[too_long] = max_length / np.maximum(lengths[too_long], 1e-9)
    return vectors * scale[:, None]


def _lerp(start: float, end: float, value: float) -> float:
    return float(start + ((end - start) * value))


def _smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 0.0

    t = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return float(t * t * (3.0 - (2.0 * t)))


def _normalize_2d(vectors: np.ndarray) -> np.ndarray:
    magnitudes = np.linalg.norm(vectors, axis=1)
    result = vectors.copy()
    valid = magnitudes > 1e-12
    result[valid] = result[valid] / magnitudes[valid, None]
    result[~valid] = np.array([0.0, 1.0])
    return result


def _normalize_rows(
    vectors: np.ndarray,
    *,
    fallback: np.ndarray,
) -> np.ndarray:
    magnitudes = np.linalg.norm(vectors, axis=1)
    normalized = vectors.copy()
    valid = magnitudes > 1e-12
    normalized[valid] = normalized[valid] / magnitudes[valid, None]
    normalized[~valid] = fallback
    return normalized


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
