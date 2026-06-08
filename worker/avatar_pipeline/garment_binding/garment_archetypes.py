from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class GarmentArchetypeMesh:
    vertices: np.ndarray
    faces: np.ndarray


@dataclass(frozen=True)
class _BodyFitMetrics:
    center_x: float
    center_z: float
    y_min: float
    y_max: float
    height: float
    hem_y: float
    armhole_y: float
    shoulder_y: float
    hem_half_width: float
    waist_half_width: float
    chest_half_width: float
    shoulder_half_width: float
    front_depth: float
    back_depth: float


FRONT_COUNT = 17
SIDE_COUNT = 8
BACK_COUNT = 17
LOOP_COUNT = FRONT_COUNT + SIDE_COUNT + BACK_COUNT + SIDE_COUNT
TORSO_RING_COUNT = 18
SLEEVE_SEGMENTS = 32
SLEEVE_RING_COUNT = 9


def generate_fitted_tshirt_archetype(
    vertices,
    faces=None,
    *,
    surface_offset: float = 0.018,
) -> GarmentArchetypeMesh:
    """Generate a believable structured T-shirt archetype.

    The archetype must look like apparel before fitting. This generator creates
    front/back panels, side seams, a real neckline loop, armhole loops, and
    sleeves extruded from those armhole loops. Better topology matters before
    realism because fitting can refine a good garment shell, but it cannot
    reliably fix a wing-like or box-like source mesh.
    """
    body_vertices = _as_vertices(vertices)
    metrics = _measure_body_fit(body_vertices, surface_offset=surface_offset)
    out_vertices: list[tuple[float, float, float]] = []
    out_faces: list[tuple[int, int, int]] = []

    torso_grid = _add_torso_panels(out_vertices, out_faces, metrics)
    _add_hem_rim(out_vertices, out_faces, torso_grid[0], metrics)
    _add_collar_and_yoke(out_vertices, out_faces, torso_grid[-1], metrics)
    for side in (-1.0, 1.0):
        _add_sleeve_with_armhole(out_vertices, out_faces, torso_grid, metrics, side=side)

    mesh_vertices = np.asarray(out_vertices, dtype=np.float64)
    mesh_faces = _remove_degenerate_faces(
        mesh_vertices,
        np.asarray(out_faces, dtype=np.int32),
    )
    return GarmentArchetypeMesh(vertices=mesh_vertices, faces=mesh_faces)


def _measure_body_fit(
    vertices: np.ndarray,
    *,
    surface_offset: float,
) -> _BodyFitMetrics:
    y_min = float(vertices[:, 1].min())
    y_max = float(vertices[:, 1].max())
    height = max(y_max - y_min, 1e-9)
    torso_mask = _body_y_mask(vertices, y_min, height, 0.42, 0.82)
    torso_vertices = vertices[torso_mask] if np.any(torso_mask) else vertices
    center_x = float(np.median(torso_vertices[:, 0]))
    center_z = float(np.median(torso_vertices[:, 2]))
    width_ease = surface_offset + (height * 0.012)
    depth_ease = surface_offset + (height * 0.010)

    raw_hem_half_width = _half_extent_at_body_ratio(
        vertices,
        center_x,
        y_min,
        height,
        0.47,
        axis=0,
        minimum=height * 0.145,
    )
    raw_waist_half_width = _half_extent_at_body_ratio(
        vertices,
        center_x,
        y_min,
        height,
        0.56,
        axis=0,
        minimum=height * 0.135,
    )
    raw_chest_half_width = _half_extent_at_body_ratio(
        vertices,
        center_x,
        y_min,
        height,
        0.615,
        axis=0,
        minimum=height * 0.175,
    )
    # T-pose arms contaminate raw lateral measurements near the shoulder. Derive
    # apparel shoulder width from torso/chest proportions so the shirt starts as
    # a wearable garment, not a wing stretched across the whole arm span.
    hem_half_width = min(raw_hem_half_width, height * 0.170)
    waist_half_width = min(raw_waist_half_width, height * 0.155)
    chest_half_width = min(raw_chest_half_width, height * 0.188)
    shoulder_half_width = min(
        max(chest_half_width * 1.08, height * 0.180),
        height * 0.205,
    )
    chest_depth = _half_extent_at_body_ratio(
        vertices,
        center_z,
        y_min,
        height,
        0.64,
        axis=2,
        minimum=height * 0.070,
    )

    return _BodyFitMetrics(
        center_x=center_x,
        center_z=center_z,
        y_min=y_min,
        y_max=y_max,
        height=height,
        hem_y=y_min + (height * 0.485),
        armhole_y=y_min + (height * 0.738),
        shoulder_y=y_min + (height * 0.805),
        hem_half_width=(hem_half_width * 0.82) + (width_ease * 0.70),
        waist_half_width=(waist_half_width * 0.76) + (width_ease * 0.68),
        chest_half_width=(chest_half_width * 0.92) + (width_ease * 0.72),
        shoulder_half_width=(shoulder_half_width * 0.84) + (width_ease * 0.65),
        front_depth=(chest_depth * 1.08) + (depth_ease * 0.78),
        back_depth=(chest_depth * 0.92) + (depth_ease * 0.65),
    )


def _add_torso_panels(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, int, int]],
    metrics: _BodyFitMetrics,
) -> list[list[int]]:
    grid: list[list[int]] = []
    for ring_index in range(TORSO_RING_COUNT):
        t = ring_index / (TORSO_RING_COUNT - 1)
        y = metrics.hem_y + ((metrics.shoulder_y - metrics.hem_y) * t)
        half_width = _torso_half_width(metrics, t)
        front_depth = _front_depth(metrics, t)
        back_depth = _back_depth(metrics, t)
        ring = _append_torso_loop(
            vertices,
            metrics,
            y=y,
            half_width=half_width,
            front_depth=front_depth,
            back_depth=back_depth,
            chest_t=t,
        )
        grid.append(ring)

    for ring_index in range(TORSO_RING_COUNT - 1):
        _connect_torso_rings_with_armholes(faces, grid[ring_index], grid[ring_index + 1], ring_index)

    return grid


def _connect_torso_rings_with_armholes(
    faces: list[tuple[int, int, int]],
    lower: list[int],
    upper: list[int],
    ring_index: int,
) -> None:
    for column_index in range(len(lower)):
        if _is_armhole_cutout_cell(ring_index, column_index):
            continue

        next_index = (column_index + 1) % len(lower)
        a = lower[column_index]
        b = lower[next_index]
        c = upper[next_index]
        d = upper[column_index]
        faces.append((a, b, c))
        faces.append((a, c, d))


def _is_armhole_cutout_cell(ring_index: int, column_index: int) -> bool:
    # These cells form the side-panel openings where the sleeve armhole loop is
    # inserted. Removing only this bounded patch keeps the torso stable while
    # giving the sleeve bridge real boundary edges to share.
    if not 10 <= ring_index < TORSO_RING_COUNT - 1:
        return False

    right_side_cell = FRONT_COUNT - 1 <= column_index < FRONT_COUNT + SIDE_COUNT
    left_side_start = FRONT_COUNT + SIDE_COUNT + BACK_COUNT - 1
    left_side_cell = left_side_start <= column_index < LOOP_COUNT
    return right_side_cell or left_side_cell


def _append_torso_loop(
    vertices: list[tuple[float, float, float]],
    metrics: _BodyFitMetrics,
    *,
    y: float,
    half_width: float,
    front_depth: float,
    back_depth: float,
    chest_t: float,
) -> list[int]:
    ring: list[int] = []

    for index in range(FRONT_COUNT):
        u = -1.0 + ((2.0 * index) / (FRONT_COUNT - 1))
        curve = 0.68 + (0.32 * (1.0 - abs(u) ** 1.85))
        chest_bulge = (
            metrics.height
            * 0.018
            * _smoothstep(0.34, 0.78, chest_t)
            * (0.48 + (0.52 * (1.0 - abs(u) ** 1.6)))
        )
        neckline_drop = (
            metrics.height
            * 0.044
            * _smoothstep(0.78, 1.0, chest_t)
            * (1.0 - abs(u) ** 1.7)
        )
        shoulder_slope = (
            metrics.height
            * 0.045
            * _smoothstep(0.70, 1.0, chest_t)
            * (abs(u) ** 1.35)
        )
        hem_round = (
            metrics.height
            * 0.010
            * (1.0 - _smoothstep(0.0, 0.10, chest_t))
            * (0.35 + (0.65 * (1.0 - abs(u) ** 1.8)))
        )
        ring.append(
            _append_vertex(
                vertices,
                metrics.center_x + (u * half_width),
                y - neckline_drop - shoulder_slope - hem_round,
                metrics.center_z + (front_depth * curve) + chest_bulge,
            )
        )

    for index in range(1, SIDE_COUNT + 1):
        v = index / (SIDE_COUNT + 1)
        side_round = np.sin(np.pi * v) * metrics.height * 0.004
        side_slope = metrics.height * 0.040 * _smoothstep(0.64, 1.0, chest_t)
        ring.append(
            _append_vertex(
                vertices,
                metrics.center_x + half_width + side_round,
                y - side_slope,
                metrics.center_z + _lerp(front_depth * 0.60, -back_depth * 0.70, v),
            )
        )

    for index in range(BACK_COUNT):
        u = 1.0 - ((2.0 * index) / (BACK_COUNT - 1))
        curve = 0.70 + (0.25 * (1.0 - abs(u) ** 1.7))
        back_curve_lift = (
            metrics.height
            * 0.009
            * _smoothstep(0.28, 0.78, chest_t)
            * (1.0 - abs(u) ** 1.7)
        )
        shoulder_slope = (
            metrics.height
            * 0.036
            * _smoothstep(0.70, 1.0, chest_t)
            * (abs(u) ** 1.30)
        )
        ring.append(
            _append_vertex(
                vertices,
                metrics.center_x + (u * half_width),
                y - shoulder_slope + back_curve_lift,
                metrics.center_z - (back_depth * curve),
            )
        )

    for index in range(1, SIDE_COUNT + 1):
        v = index / (SIDE_COUNT + 1)
        side_round = np.sin(np.pi * v) * metrics.height * 0.004
        side_slope = metrics.height * 0.040 * _smoothstep(0.64, 1.0, chest_t)
        ring.append(
            _append_vertex(
                vertices,
                metrics.center_x - half_width - side_round,
                y - side_slope,
                metrics.center_z + _lerp(-back_depth * 0.70, front_depth * 0.60, v),
            )
        )

    return ring


def _add_hem_rim(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, int, int]],
    hem_ring: list[int],
    metrics: _BodyFitMetrics,
) -> None:
    rim = []
    for source_index in hem_ring:
        source = np.asarray(vertices[source_index], dtype=np.float64)
        local = source - np.array([metrics.center_x, source[1], metrics.center_z])
        rim.append(
            _append_vertex(
                vertices,
                metrics.center_x + (local[0] * 0.965),
                source[1] - (metrics.height * 0.008),
                metrics.center_z + (local[2] * 0.965),
            )
        )

    _connect_equal_rings(faces, hem_ring, rim, reverse=True)


def _add_collar_and_yoke(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, int, int]],
    shoulder_ring: list[int],
    metrics: _BodyFitMetrics,
) -> None:
    collar_ring = _append_collar_loop(vertices, metrics)
    # A dedicated yoke ring gives the shoulder/collar area a sewn garment
    # transition instead of one flat bridge from shoulder edge to neckline.
    yoke_ring = _append_interpolated_ring(
        vertices,
        shoulder_ring,
        collar_ring,
        blend=0.48,
        y_bias=metrics.height * 0.010,
    )
    _connect_equal_rings(faces, shoulder_ring, yoke_ring)
    _connect_equal_rings(faces, yoke_ring, collar_ring)
    _add_collar_rim(vertices, faces, collar_ring, metrics)


def _append_collar_loop(
    vertices: list[tuple[float, float, float]],
    metrics: _BodyFitMetrics,
) -> list[int]:
    front_y = metrics.y_min + (metrics.height * 0.754)
    side_y = metrics.y_min + (metrics.height * 0.798)
    back_y = metrics.y_min + (metrics.height * 0.830)
    front_width = metrics.height * 0.052
    back_width = metrics.height * 0.062
    front_depth = metrics.height * 0.052
    back_depth = metrics.height * 0.040
    ring: list[int] = []

    for index in range(FRONT_COUNT):
        u = -1.0 + ((2.0 * index) / (FRONT_COUNT - 1))
        y = front_y + ((abs(u) ** 1.65) * (side_y - front_y))
        ring.append(
            _append_vertex(
                vertices,
                metrics.center_x + (u * front_width),
                y,
                metrics.center_z + (front_depth * (0.70 + (0.30 * (1.0 - abs(u))))),
            )
        )

    for index in range(1, SIDE_COUNT + 1):
        v = index / (SIDE_COUNT + 1)
        ring.append(
            _append_vertex(
                vertices,
                metrics.center_x + _lerp(front_width, back_width, v),
                _lerp(side_y, back_y, v),
                metrics.center_z + _lerp(front_depth * 0.68, -back_depth * 0.82, v),
            )
        )

    for index in range(BACK_COUNT):
        u = 1.0 - ((2.0 * index) / (BACK_COUNT - 1))
        y = back_y - ((1.0 - abs(u)) * metrics.height * 0.006)
        ring.append(
            _append_vertex(
                vertices,
                metrics.center_x + (u * back_width),
                y,
                metrics.center_z - (back_depth * (0.78 + (0.14 * (1.0 - abs(u))))),
            )
        )

    for index in range(1, SIDE_COUNT + 1):
        v = index / (SIDE_COUNT + 1)
        ring.append(
            _append_vertex(
                vertices,
                metrics.center_x - _lerp(back_width, front_width, v),
                _lerp(back_y, side_y, v),
                metrics.center_z + _lerp(-back_depth * 0.82, front_depth * 0.68, v),
            )
        )

    return ring


def _add_collar_rim(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, int, int]],
    collar_ring: list[int],
    metrics: _BodyFitMetrics,
) -> None:
    rim = []
    for source_index in collar_ring:
        source = np.asarray(vertices[source_index], dtype=np.float64)
        local = source - np.array([metrics.center_x, source[1], metrics.center_z])
        rim.append(
            _append_vertex(
                vertices,
                metrics.center_x + (local[0] * 0.90),
                source[1] - (metrics.height * 0.003),
                metrics.center_z + (local[2] * 0.91),
            )
        )

    _connect_equal_rings(faces, collar_ring, rim, reverse=True)


def _add_sleeve_with_armhole(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, int, int]],
    torso_grid: list[list[int]],
    metrics: _BodyFitMetrics,
    *,
    side: float,
) -> None:
    armhole_ring = _append_armhole_ring(vertices, metrics, side=side)
    seam_ring = _append_armhole_seam_ring(vertices, metrics, armhole_ring, side=side)
    _connect_seam_ring_to_torso_grid(faces, torso_grid, seam_ring, side=side)
    _connect_armhole_to_torso(faces, seam_ring, armhole_ring)
    # Sleeves are extruded from the armhole loop itself. This keeps the sleeve
    # root as a continuous boundary of the garment instead of a separately
    # attached cylinder with a visible seam break.
    sleeve_grid = [armhole_ring]
    for ring_index in range(1, SLEEVE_RING_COUNT):
        t = ring_index / (SLEEVE_RING_COUNT - 1)
        sleeve_grid.append(
            _append_sleeve_extrusion_ring(
                vertices,
                metrics,
                armhole_ring,
                side=side,
                t=t,
            )
        )

    for ring_index in range(SLEEVE_RING_COUNT - 1):
        _connect_equal_rings(faces, sleeve_grid[ring_index], sleeve_grid[ring_index + 1])

    _add_sleeve_cuff_rim(vertices, faces, sleeve_grid[-1], metrics, side=side)


def _append_armhole_ring(
    vertices: list[tuple[float, float, float]],
    metrics: _BodyFitMetrics,
    *,
    side: float,
) -> list[int]:
    ring = []
    for index in range(SLEEVE_SEGMENTS):
        theta = (2.0 * np.pi * index) / SLEEVE_SEGMENTS
        sin_theta = float(np.sin(theta))
        cos_theta = float(np.cos(theta))
        y = metrics.armhole_y + (metrics.height * 0.036 * sin_theta)
        t = _torso_t_for_y(metrics, y)
        half_width = _torso_half_width(metrics, t)
        cap = max(sin_theta, 0.0)
        underarm = max(-sin_theta, 0.0)
        front_back = abs(cos_theta)
        x = metrics.center_x + side * (
            (half_width * 0.990)
            + (metrics.height * ((0.009 * cap) - (0.012 * underarm) - (0.004 * front_back)))
        )
        z = metrics.center_z + _armhole_z(metrics, t, cos_theta, scale=0.62)
        ring.append(_append_vertex(vertices, x, y, z))

    return ring


def _append_armhole_seam_ring(
    vertices: list[tuple[float, float, float]],
    metrics: _BodyFitMetrics,
    armhole_ring: list[int],
    *,
    side: float,
) -> list[int]:
    """Build the torso-side edge loop that the sleeve extrudes from.

    The old generator connected the sleeve to arbitrary nearest torso vertices,
    which made the root behave like a stitched-on primitive. This ordered seam
    loop follows the same angular layout as the armhole loop, so the topology has
    a stable edge flow from front panel to underarm to back panel.
    """
    seam_ring: list[int] = []
    for index, armhole_index in enumerate(armhole_ring):
        theta = (2.0 * np.pi * index) / SLEEVE_SEGMENTS
        sin_theta = float(np.sin(theta))
        cos_theta = float(np.cos(theta))
        armhole_point = np.asarray(vertices[armhole_index], dtype=np.float64)
        t = _torso_t_for_y(metrics, float(armhole_point[1]))
        half_width = _torso_half_width(metrics, t)
        shoulder_blend = max(sin_theta, 0.0)
        underarm_blend = max(-sin_theta, 0.0)
        front_back_blend = abs(cos_theta)

        torso_x = metrics.center_x + side * (
            (half_width * (0.930 + (0.036 * shoulder_blend)))
            - (metrics.height * 0.010 * underarm_blend)
        )
        torso_z = metrics.center_z + _armhole_z(metrics, t, cos_theta, scale=0.74)
        torso_y = (
            armhole_point[1]
            + (metrics.height * 0.010 * shoulder_blend)
            - (metrics.height * 0.006 * underarm_blend)
        )
        seam_point = np.array([torso_x, torso_y, torso_z], dtype=np.float64)
        seam_point = _lerp_array(seam_point, armhole_point, 0.18 + (0.10 * front_back_blend))
        seam_ring.append(_append_vertex(vertices, *seam_point))

    return seam_ring


def _append_sleeve_extrusion_ring(
    vertices: list[tuple[float, float, float]],
    metrics: _BodyFitMetrics,
    armhole_ring: list[int],
    *,
    side: float,
    t: float,
) -> list[int]:
    ring = []
    armhole_points = np.asarray([vertices[index] for index in armhole_ring], dtype=np.float64)
    armhole_center = armhole_points.mean(axis=0)
    blend = _smoothstep(0.0, 0.92, t)
    center = armhole_center.copy()
    center[0] += side * metrics.height * 0.072 * t
    center[1] -= metrics.height * 0.040 * t
    center[2] = _lerp(armhole_center[2], metrics.center_z + (metrics.height * 0.004), blend)
    radius_y = metrics.height * _lerp(0.036, 0.026, t)
    radius_z = metrics.height * _lerp(0.033, 0.023, t)

    for index, source in enumerate(armhole_points):
        theta = (2.0 * np.pi * index) / SLEEVE_SEGMENTS
        target = np.array(
            [
                center[0],
                center[1] + (radius_y * np.sin(theta)),
                center[2] + (radius_z * np.cos(theta)),
            ],
            dtype=np.float64,
        )
        point = _lerp_array(source, target, blend)
        # Keep the first support rings very close to the armhole so the edge
        # flow reads as an extrusion rather than an attached primitive.
        point[0] = _lerp(source[0] + (side * metrics.height * 0.012 * t), point[0], blend)
        ring.append(_append_vertex(vertices, *point))

    return ring


def _armhole_z(metrics: _BodyFitMetrics, t: float, cos_theta: float, *, scale: float) -> float:
    if cos_theta >= 0:
        return _front_depth(metrics, t) * scale * cos_theta

    return _back_depth(metrics, t) * scale * cos_theta


def _connect_armhole_to_torso(
    faces: list[tuple[int, int, int]],
    seam_ring: list[int],
    armhole_ring: list[int],
) -> None:
    _connect_equal_rings(faces, seam_ring, armhole_ring)


def _connect_seam_ring_to_torso_grid(
    faces: list[tuple[int, int, int]],
    torso_grid: list[list[int]],
    seam_ring: list[int],
    *,
    side: float,
) -> None:
    anchor_ring = _torso_armhole_boundary_ring(torso_grid, side=side)
    _connect_equal_rings(faces, anchor_ring, seam_ring)


def _torso_armhole_boundary_ring(
    torso_grid: list[list[int]],
    *,
    side: float,
) -> list[int]:
    """Return an ordered side-panel boundary that shares real torso edges.

    The path starts at the front of the armhole, rises over the shoulder,
    travels across the upper side panel, drops through the back of the armhole,
    crosses the underarm, and returns to the start. Because every consecutive
    pair is an existing torso edge, the sleeve-root bridge becomes part of the
    same mesh component instead of a vertex-touching attachment.
    """
    side_indices = _torso_side_indices(side)
    front_col = side_indices[0]
    back_col = side_indices[-1]
    mid_ring = 13
    upper_ring = TORSO_RING_COUNT - 1
    lower_ring = 10
    boundary: list[int] = []

    for ring_index in range(mid_ring, upper_ring + 1):
        boundary.append(torso_grid[ring_index][front_col])

    for column_index in side_indices[1:]:
        boundary.append(torso_grid[upper_ring][column_index])

    for ring_index in range(upper_ring - 1, lower_ring - 1, -1):
        boundary.append(torso_grid[ring_index][back_col])

    for column_index in reversed(side_indices[:-1]):
        boundary.append(torso_grid[lower_ring][column_index])

    for ring_index in range(lower_ring + 1, mid_ring):
        boundary.append(torso_grid[ring_index][front_col])

    if len(boundary) != SLEEVE_SEGMENTS:
        raise ValueError("Armhole boundary must match sleeve segment count.")

    return boundary


def _torso_side_indices(side: float) -> list[int]:
    if side > 0:
        return [FRONT_COUNT - 1, *range(FRONT_COUNT, FRONT_COUNT + SIDE_COUNT), FRONT_COUNT + SIDE_COUNT]

    left_side_start = FRONT_COUNT + SIDE_COUNT + BACK_COUNT
    return [
        0,
        *range(left_side_start + SIDE_COUNT - 1, left_side_start - 1, -1),
        FRONT_COUNT + SIDE_COUNT + BACK_COUNT - 1,
    ]


def _append_interpolated_ring(
    vertices: list[tuple[float, float, float]],
    outer_ring: list[int],
    inner_ring: list[int],
    *,
    blend: float,
    y_bias: float,
) -> list[int]:
    ring = []
    for outer_index, inner_index in zip(outer_ring, inner_ring):
        outer = np.asarray(vertices[outer_index], dtype=np.float64)
        inner = np.asarray(vertices[inner_index], dtype=np.float64)
        point = _lerp_array(outer, inner, blend)
        point[1] += y_bias * (0.45 + (0.55 * blend))
        ring.append(_append_vertex(vertices, *point))

    return ring


def _add_sleeve_cuff_rim(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, int, int]],
    cuff_ring: list[int],
    metrics: _BodyFitMetrics,
    *,
    side: float,
) -> None:
    center = np.asarray([vertices[index] for index in cuff_ring], dtype=np.float64).mean(axis=0)
    rim = []
    for source_index in cuff_ring:
        source = np.asarray(vertices[source_index], dtype=np.float64)
        local = source - center
        local[0] -= side * metrics.height * 0.006
        rim.append(_append_vertex(vertices, *(center + (local * 0.90))))

    _connect_equal_rings(faces, cuff_ring, rim)


def _connect_equal_rings(
    faces: list[tuple[int, int, int]],
    lower: list[int],
    upper: list[int],
    *,
    reverse: bool = False,
) -> None:
    if len(lower) != len(upper):
        raise ValueError("Cannot connect rings with different vertex counts.")

    for index in range(len(lower)):
        next_index = (index + 1) % len(lower)
        a = lower[index]
        b = lower[next_index]
        c = upper[next_index]
        d = upper[index]
        if reverse:
            faces.append((a, c, b))
            faces.append((a, d, c))
        else:
            faces.append((a, b, c))
            faces.append((a, c, d))


def _torso_half_width(metrics: _BodyFitMetrics, t: float) -> float:
    return float(
        np.interp(
            t,
            [0.0, 0.33, 0.66, 0.86, 1.0],
            [
                metrics.hem_half_width * 0.90,
                metrics.waist_half_width * 0.84,
                metrics.chest_half_width * 0.98,
                metrics.shoulder_half_width * 0.92,
                metrics.shoulder_half_width * 0.64,
            ],
        )
    )


def _front_depth(metrics: _BodyFitMetrics, t: float) -> float:
    return float(
        np.interp(
            t,
            [0.0, 0.45, 0.72, 1.0],
            [
                metrics.front_depth * 0.88,
                metrics.front_depth * 0.98,
                metrics.front_depth * 1.10,
                metrics.front_depth * 0.86,
            ],
        )
    )


def _back_depth(metrics: _BodyFitMetrics, t: float) -> float:
    return float(
        np.interp(
            t,
            [0.0, 0.55, 1.0],
            [
                metrics.back_depth * 0.82,
                metrics.back_depth * 0.96,
                metrics.back_depth * 0.82,
            ],
        )
    )


def _half_extent_at_body_ratio(
    vertices: np.ndarray,
    center: float,
    y_min: float,
    height: float,
    body_y_ratio: float,
    *,
    axis: int,
    minimum: float,
) -> float:
    band = _body_y_mask(vertices, y_min, height, body_y_ratio - 0.025, body_y_ratio + 0.025)
    if not np.any(band):
        return minimum

    values = np.abs(vertices[band, axis] - center)
    if len(values) == 0:
        return minimum

    return max(float(np.percentile(values, 90.0)), minimum)


def _body_y_mask(
    vertices: np.ndarray,
    y_min: float,
    height: float,
    lower: float,
    upper: float,
) -> np.ndarray:
    y_ratio = (vertices[:, 1] - y_min) / height
    return (y_ratio >= lower) & (y_ratio <= upper)


def _remove_degenerate_faces(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    if len(faces) == 0:
        return faces

    triangles = vertices[faces]
    repeated_vertex = (
        (faces[:, 0] == faces[:, 1])
        | (faces[:, 1] == faces[:, 2])
        | (faces[:, 0] == faces[:, 2])
    )
    areas = np.linalg.norm(
        np.cross(
            triangles[:, 1] - triangles[:, 0],
            triangles[:, 2] - triangles[:, 0],
        ),
        axis=1,
    )
    keep = (~repeated_vertex) & (areas > 1e-10)
    return faces[keep]


def _append_vertex(
    vertices: list[tuple[float, float, float]],
    x: float,
    y: float,
    z: float,
) -> int:
    vertices.append((float(x), float(y), float(z)))
    return len(vertices) - 1


def _lerp(start: float, end: float, t: float) -> float:
    return float(start + ((end - start) * t))


def _lerp_array(start: np.ndarray, end: np.ndarray, t: float) -> np.ndarray:
    return start + ((end - start) * t)


def _torso_t_for_y(metrics: _BodyFitMetrics, y: float) -> float:
    span = max(metrics.shoulder_y - metrics.hem_y, 1e-9)
    return float(np.clip((y - metrics.hem_y) / span, 0.0, 1.0))


def _smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 0.0

    t = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return float(t * t * (3.0 - (2.0 * t)))


def _as_vertices(vertices) -> np.ndarray:
    array = np.asarray(vertices, dtype=np.float64)
    if array.ndim != 2 or array.shape[1] != 3:
        raise ValueError("vertices must be an Nx3 array")

    return array
