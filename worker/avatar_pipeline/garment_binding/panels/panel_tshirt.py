from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PanelGarmentMesh:
    vertices: np.ndarray
    faces: np.ndarray
    curves: dict[str, list[int]]
    regions: dict[str, list[int]]
    region_labels: tuple[str, ...]


@dataclass(frozen=True)
class _PanelMetrics:
    center_x: float
    center_z: float
    y_min: float
    height: float
    hem_y: float
    underarm_y: float
    shoulder_y: float
    hem_half_width: float
    waist_half_width: float
    chest_half_width: float
    shoulder_half_width: float
    front_depth: float
    back_depth: float


PANEL_ROWS = 19
PANEL_COLUMNS = 25
SLEEVE_SEGMENTS = 28
SLEEVE_RINGS = 8

TORSO_FRONT = "TORSO_FRONT"
TORSO_BACK = "TORSO_BACK"
LEFT_SLEEVE = "LEFT_SLEEVE"
RIGHT_SLEEVE = "RIGHT_SLEEVE"
COLLAR = "COLLAR"
LEFT_ARMHOLE = "LEFT_ARMHOLE"
RIGHT_ARMHOLE = "RIGHT_ARMHOLE"
HEM = "HEM"
REGION_NAMES = (
    TORSO_FRONT,
    TORSO_BACK,
    LEFT_SLEEVE,
    RIGHT_SLEEVE,
    COLLAR,
    LEFT_ARMHOLE,
    RIGHT_ARMHOLE,
    HEM,
)


def generate_panel_tshirt(
    vertices,
    faces=None,
    *,
    surface_offset: float = 0.018,
) -> PanelGarmentMesh:
    """Generate a T-shirt from explicit garment panels.

    The mesh is built as front/back torso panels with stitched side and shoulder
    seams. Sleeve panels are quad strips grown from armhole seam loops, not
    separate primitive cylinders. Open boundaries should represent only the
    actual garment openings: neckline, hem, and sleeve cuffs.
    """
    del faces
    body_vertices = _as_vertices(vertices)
    metrics = _measure_panel_metrics(body_vertices, surface_offset=surface_offset)
    out_vertices: list[tuple[float, float, float]] = []
    out_faces: list[tuple[int, int, int]] = []
    curves: dict[str, list[int]] = {}

    front_grid, back_grid = _build_torso_panels(out_vertices, out_faces, metrics, curves)
    _connect_shoulder_seams(out_faces, front_grid, back_grid)
    curves["hem_loop"] = _make_hem_loop(front_grid, back_grid)
    curves["neckline_loop"] = _make_neckline_loop(front_grid, back_grid)
    curves["left_side_seam"] = [row[0] for row in front_grid]
    curves["right_side_seam"] = [row[-1] for row in front_grid]
    curves["left_shoulder_seam"] = _make_shoulder_curve(front_grid, back_grid, side=-1.0)
    curves["right_shoulder_seam"] = _make_shoulder_curve(front_grid, back_grid, side=1.0)

    for side, name in ((-1.0, "left"), (1.0, "right")):
        panel_armhole_loop = _panel_armhole_panel_targets(front_grid, back_grid, side=side)
        # The armhole loop is the actual torso boundary. Sleeves are extruded
        # from these welded vertices so the root seam is continuous topology,
        # not a separate sleeve primitive stitched visually to the torso side.
        sleeve_grid = _append_sleeve_panel(
            out_vertices,
            out_faces,
            metrics,
            panel_armhole_loop,
            side=side,
        )
        curves[f"{name}_armhole_loop"] = panel_armhole_loop
        curves[f"{name}_armhole_panel_loop"] = panel_armhole_loop
        curves[f"{name}_sleeve_cuff_loop"] = sleeve_grid[-1]

    mesh_vertices = np.asarray(out_vertices, dtype=np.float64)
    mesh_faces = _remove_degenerate_faces(
        mesh_vertices,
        np.asarray(out_faces, dtype=np.int32),
    )
    regions, region_labels = _build_panel_regions(mesh_vertices, front_grid, back_grid, curves)
    return PanelGarmentMesh(
        vertices=mesh_vertices,
        faces=mesh_faces,
        curves=curves,
        regions=regions,
        region_labels=tuple(region_labels),
    )


def _measure_panel_metrics(
    vertices: np.ndarray,
    *,
    surface_offset: float,
) -> _PanelMetrics:
    y_min = float(vertices[:, 1].min())
    y_max = float(vertices[:, 1].max())
    height = max(y_max - y_min, 1e-9)
    torso_mask = _body_y_mask(vertices, y_min, height, 0.42, 0.82)
    torso_vertices = vertices[torso_mask] if np.any(torso_mask) else vertices
    center_x = float(np.median(torso_vertices[:, 0]))
    center_z = float(np.median(torso_vertices[:, 2]))
    width_ease = surface_offset + (height * 0.016)
    depth_ease = surface_offset + (height * 0.012)

    hem_half_width = min(
        _half_extent_at_ratio(vertices, center_x, y_min, height, 0.49, axis=0),
        height * 0.175,
    )
    waist_half_width = min(
        _half_extent_at_ratio(vertices, center_x, y_min, height, 0.57, axis=0),
        height * 0.160,
    )
    chest_half_width = min(
        _half_extent_at_ratio(vertices, center_x, y_min, height, 0.66, axis=0),
        height * 0.195,
    )
    shoulder_half_width = min(max(chest_half_width * 1.13, height * 0.185), height * 0.215)
    chest_depth = _half_extent_at_ratio(vertices, center_z, y_min, height, 0.65, axis=2)

    return _PanelMetrics(
        center_x=center_x,
        center_z=center_z,
        y_min=y_min,
        height=height,
        hem_y=y_min + (height * 0.485),
        underarm_y=y_min + (height * 0.700),
        shoulder_y=y_min + (height * 0.804),
        hem_half_width=(hem_half_width * 0.86) + (width_ease * 0.68),
        waist_half_width=(waist_half_width * 0.82) + (width_ease * 0.66),
        chest_half_width=(chest_half_width * 0.94) + (width_ease * 0.70),
        shoulder_half_width=(shoulder_half_width * 0.88) + (width_ease * 0.58),
        front_depth=(chest_depth * 1.08) + (depth_ease * 0.76),
        back_depth=(chest_depth * 0.94) + (depth_ease * 0.66),
    )


def _build_torso_panels(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, int, int]],
    metrics: _PanelMetrics,
    curves: dict[str, list[int]],
) -> tuple[list[list[int]], list[list[int]]]:
    front_grid: list[list[int]] = []
    back_grid: list[list[int]] = []
    for row_index in range(PANEL_ROWS):
        t = row_index / (PANEL_ROWS - 1)
        front_row: list[int] = []
        back_row: list[int] = []
        for column_index in range(PANEL_COLUMNS):
            u = -1.0 + ((2.0 * column_index) / (PANEL_COLUMNS - 1))
            front_row.append(
                _append_vertex(vertices, *_torso_panel_point(metrics, t, u, "front"))
            )
            back_row.append(
                _append_vertex(vertices, *_torso_panel_point(metrics, t, u, "back"))
            )

        front_grid.append(front_row)
        back_grid.append(back_row)

    for row_index in range(PANEL_ROWS - 1):
        for column_index in range(PANEL_COLUMNS - 1):
            if _skip_front_cell(row_index, column_index):
                pass
            else:
                _add_quad(
                    faces,
                    front_grid[row_index][column_index],
                    front_grid[row_index][column_index + 1],
                    front_grid[row_index + 1][column_index + 1],
                    front_grid[row_index + 1][column_index],
                )
            if _skip_back_cell(row_index, column_index):
                continue

            _add_quad(
                faces,
                back_grid[row_index][column_index + 1],
                back_grid[row_index][column_index],
                back_grid[row_index + 1][column_index],
                back_grid[row_index + 1][column_index + 1],
            )

    _connect_lower_side_panels(faces, front_grid, back_grid)
    curves["front_panel_boundary"] = _panel_boundary(front_grid)
    curves["back_panel_boundary"] = _panel_boundary(back_grid)
    return front_grid, back_grid


def _connect_lower_side_panels(
    faces: list[tuple[int, int, int]],
    front_grid: list[list[int]],
    back_grid: list[list[int]],
) -> None:
    lower_armhole_row = 10
    for row_index in range(lower_armhole_row):
        next_row = row_index + 1
        _add_quad(
            faces,
            back_grid[row_index][0],
            front_grid[row_index][0],
            front_grid[next_row][0],
            back_grid[next_row][0],
        )
        _add_quad(
            faces,
            front_grid[row_index][-1],
            back_grid[row_index][-1],
            back_grid[next_row][-1],
            front_grid[next_row][-1],
        )


def _connect_shoulder_seams(
    faces: list[tuple[int, int, int]],
    front_grid: list[list[int]],
    back_grid: list[list[int]],
) -> None:
    top = PANEL_ROWS - 1
    center = PANEL_COLUMNS // 2
    front_left_neck = center - 4
    front_right_neck = center + 4
    back_left_neck = center - 3
    back_right_neck = center + 3

    for column_index in range(0, min(front_left_neck, back_left_neck) - 1):
        _add_quad(
            faces,
            front_grid[top][column_index],
            front_grid[top][column_index + 1],
            back_grid[top][column_index + 1],
            back_grid[top][column_index],
        )

    for column_index in range(max(front_right_neck, back_right_neck), PANEL_COLUMNS - 1):
        _add_quad(
            faces,
            front_grid[top][column_index],
            front_grid[top][column_index + 1],
            back_grid[top][column_index + 1],
            back_grid[top][column_index],
        )


def _torso_panel_point(
    metrics: _PanelMetrics,
    t: float,
    u: float,
    panel: str,
    *,
    side: float = 0.0,
) -> tuple[float, float, float]:
    half_width = _torso_half_width(metrics, t)
    y = metrics.hem_y + ((metrics.shoulder_y - metrics.hem_y) * t)
    shoulder_slope = metrics.height * 0.040 * _smoothstep(0.68, 1.0, t) * (abs(u) ** 1.35)
    hem_round = metrics.height * 0.009 * (1.0 - _smoothstep(0.0, 0.12, t)) * (1.0 - abs(u) ** 1.8)
    x = metrics.center_x + (u * half_width)

    if panel == "side":
        return (
            metrics.center_x + (side * half_width),
            y - shoulder_slope - hem_round,
            metrics.center_z,
        )

    curve = 0.58 + (0.42 * (1.0 - abs(u) ** 1.7))
    if panel == "front":
        chest_bulge = metrics.height * 0.014 * _smoothstep(0.36, 0.76, t) * (1.0 - abs(u) ** 1.5)
        neckline_drop = metrics.height * 0.035 * _smoothstep(0.80, 1.0, t) * (1.0 - abs(u) ** 1.8)
        return (
            x,
            y - shoulder_slope - hem_round - neckline_drop,
            metrics.center_z + (_front_depth(metrics, t) * curve) + chest_bulge,
        )

    back_lift = metrics.height * 0.008 * _smoothstep(0.35, 0.82, t) * (1.0 - abs(u) ** 1.7)
    return (
        x,
        y - shoulder_slope - hem_round + back_lift,
        metrics.center_z - (_back_depth(metrics, t) * curve),
    )


def _skip_front_cell(row_index: int, column_index: int) -> bool:
    row_t = (row_index + 0.5) / (PANEL_ROWS - 1)
    col_u = -1.0 + ((2.0 * (column_index + 0.5)) / (PANEL_COLUMNS - 1))
    neckline = row_t >= (0.825 + (abs(col_u) * 0.115)) and abs(col_u) <= 0.36
    return neckline or _skip_armhole_cell(row_index, column_index)


def _skip_back_cell(row_index: int, column_index: int) -> bool:
    row_t = (row_index + 0.5) / (PANEL_ROWS - 1)
    col_u = -1.0 + ((2.0 * (column_index + 0.5)) / (PANEL_COLUMNS - 1))
    neckline = row_t >= (0.910 + (abs(col_u) * 0.050)) and abs(col_u) <= 0.32
    return neckline or _skip_armhole_cell(row_index, column_index)


def _skip_armhole_cell(row_index: int, column_index: int) -> bool:
    if row_index < 10:
        return False

    return column_index <= 2 or column_index >= PANEL_COLUMNS - 4


def _panel_armhole_panel_targets(
    front_grid: list[list[int]],
    back_grid: list[list[int]],
    *,
    side: float,
) -> list[int]:
    lower_row = 10
    upper_row = PANEL_ROWS - 1
    if side > 0:
        inner = PANEL_COLUMNS - 4
        side_col = PANEL_COLUMNS - 1
        return [
            *[front_grid[row_index][inner] for row_index in range(lower_row, upper_row + 1)],
            front_grid[upper_row][inner + 1],
            front_grid[upper_row][inner + 2],
            front_grid[upper_row][side_col],
            back_grid[upper_row][side_col],
            back_grid[upper_row][inner + 2],
            back_grid[upper_row][inner + 1],
            back_grid[upper_row][inner],
            *[back_grid[row_index][inner] for row_index in range(upper_row - 1, lower_row - 1, -1)],
            back_grid[lower_row][inner + 1],
            back_grid[lower_row][inner + 2],
            back_grid[lower_row][side_col],
            front_grid[lower_row][side_col],
            front_grid[lower_row][inner + 2],
            front_grid[lower_row][inner + 1],
        ]

    inner = 3
    side_col = 0
    return [
        *[front_grid[row_index][inner] for row_index in range(lower_row, upper_row + 1)],
        front_grid[upper_row][inner - 1],
        front_grid[upper_row][inner - 2],
        front_grid[upper_row][side_col],
        back_grid[upper_row][side_col],
        back_grid[upper_row][inner - 2],
        back_grid[upper_row][inner - 1],
        back_grid[upper_row][inner],
        *[back_grid[row_index][inner] for row_index in range(upper_row - 1, lower_row - 1, -1)],
        back_grid[lower_row][inner - 1],
        back_grid[lower_row][inner - 2],
        back_grid[lower_row][side_col],
        front_grid[lower_row][side_col],
        front_grid[lower_row][inner - 2],
        front_grid[lower_row][inner - 1],
    ]


def _append_sleeve_panel(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, int, int]],
    metrics: _PanelMetrics,
    armhole_loop: list[int],
    *,
    side: float,
) -> list[list[int]]:
    grid = [armhole_loop]
    armhole_points = np.asarray([vertices[index] for index in armhole_loop], dtype=np.float64)
    armhole_center = armhole_points.mean(axis=0)
    segment_count = len(armhole_loop)
    for ring_index in range(1, SLEEVE_RINGS):
        t = ring_index / (SLEEVE_RINGS - 1)
        blend = _smoothstep(0.0, 1.0, t)
        center = armhole_center.copy()
        center[0] += side * metrics.height * 0.112 * t
        center[1] -= metrics.height * 0.030 * t
        center[2] = _lerp(armhole_center[2], metrics.center_z + (metrics.height * 0.004), blend)
        radius_y = metrics.height * _lerp(0.040, 0.029, t)
        radius_z = metrics.height * _lerp(0.034, 0.023, t)
        row: list[int] = []
        for index, source in enumerate(armhole_points):
            theta = (2.0 * np.pi * index) / segment_count
            target = np.array(
                [
                    center[0],
                    center[1] + (radius_y * np.sin(theta)),
                    center[2] + (radius_z * np.cos(theta)),
                ],
                dtype=np.float64,
            )
            point = _lerp_array(source, target, blend)
            row.append(_append_vertex(vertices, *point))

        grid.append(row)

    for ring_index in range(SLEEVE_RINGS - 1):
        _connect_equal_rings(faces, grid[ring_index], grid[ring_index + 1])

    return grid


def _make_hem_loop(front_grid: list[list[int]], back_grid: list[list[int]]) -> list[int]:
    return [*front_grid[0], *reversed(back_grid[0])]


def _make_neckline_loop(front_grid: list[list[int]], back_grid: list[list[int]]) -> list[int]:
    top_row = PANEL_ROWS - 1
    center = PANEL_COLUMNS // 2
    front_left = center - 4
    front_right = center + 4
    back_left = center - 3
    back_right = center + 3
    return [
        *front_grid[top_row][front_left : front_right + 1],
        *reversed(back_grid[top_row][back_left : back_right + 1]),
    ]


def _make_shoulder_curve(
    front_grid: list[list[int]],
    back_grid: list[list[int]],
    *,
    side: float,
) -> list[int]:
    top_row = PANEL_ROWS - 1
    center = PANEL_COLUMNS // 2
    if side < 0:
        return [*front_grid[top_row][0 : center - 4], *reversed(back_grid[top_row][0 : center - 3])]

    return [
        *front_grid[top_row][center + 4 :],
        *reversed(back_grid[top_row][center + 3 :]),
    ]


def _build_panel_regions(
    vertices: np.ndarray,
    front_grid: list[list[int]],
    back_grid: list[list[int]],
    curves: dict[str, list[int]],
) -> tuple[dict[str, list[int]], list[str]]:
    vertex_count = len(vertices)
    labels = [TORSO_FRONT for _ in range(vertex_count)]
    for row in back_grid:
        for vertex_index in row:
            labels[vertex_index] = TORSO_BACK
    for row in front_grid:
        for vertex_index in row:
            labels[vertex_index] = TORSO_FRONT

    _assign_curve(labels, curves.get("left_armhole_panel_loop", []), LEFT_ARMHOLE)
    _assign_curve(labels, curves.get("left_armhole_loop", []), LEFT_ARMHOLE)
    _assign_curve(labels, curves.get("right_armhole_panel_loop", []), RIGHT_ARMHOLE)
    _assign_curve(labels, curves.get("right_armhole_loop", []), RIGHT_ARMHOLE)
    _assign_curve(labels, curves.get("left_sleeve_cuff_loop", []), LEFT_SLEEVE)
    _assign_curve(labels, curves.get("right_sleeve_cuff_loop", []), RIGHT_SLEEVE)
    _assign_curve(labels, curves.get("neckline_loop", []), COLLAR)
    _assign_curve(labels, curves.get("hem_loop", []), HEM)

    torso_indices = sorted(
        {index for row in front_grid for index in row}
        | {index for row in back_grid for index in row}
    )
    torso_vertex_set = set(torso_indices)
    center_x = float(np.median(vertices[torso_indices, 0])) if torso_indices else 0.0
    for vertex_index, label in enumerate(labels):
        if label in (LEFT_ARMHOLE, RIGHT_ARMHOLE, COLLAR, HEM):
            continue
        if vertex_index not in torso_vertex_set:
            labels[vertex_index] = LEFT_SLEEVE if vertices[vertex_index, 0] < center_x else RIGHT_SLEEVE

    regions = {
        region_name: [
            vertex_index
            for vertex_index, label in enumerate(labels)
            if label == region_name
        ]
        for region_name in REGION_NAMES
    }
    return regions, labels


def _assign_curve(labels: list[str], indices: list[int], region_name: str) -> None:
    for index in indices:
        if 0 <= index < len(labels):
            labels[index] = region_name


def _panel_boundary(grid: list[list[int]]) -> list[int]:
    return [
        *grid[0],
        *[row[-1] for row in grid[1:]],
        *reversed(grid[-1][:-1]),
        *[row[0] for row in reversed(grid[1:-1])],
    ]


def _connect_equal_rings(
    faces: list[tuple[int, int, int]],
    lower: list[int],
    upper: list[int],
) -> None:
    if len(lower) != len(upper):
        raise ValueError("Cannot connect rings with different vertex counts.")

    for index in range(len(lower)):
        next_index = (index + 1) % len(lower)
        _add_quad(faces, lower[index], lower[next_index], upper[next_index], upper[index])


def _add_quad(
    faces: list[tuple[int, int, int]],
    a: int,
    b: int,
    c: int,
    d: int,
) -> None:
    faces.append((a, b, c))
    faces.append((a, c, d))


def _torso_half_width(metrics: _PanelMetrics, t: float) -> float:
    return float(
        np.interp(
            t,
            [0.0, 0.34, 0.66, 0.88, 1.0],
            [
                metrics.hem_half_width * 0.92,
                metrics.waist_half_width * 0.86,
                metrics.chest_half_width * 1.00,
                metrics.shoulder_half_width * 0.95,
                metrics.shoulder_half_width * 0.68,
            ],
        )
    )


def _front_depth(metrics: _PanelMetrics, t: float) -> float:
    return float(
        np.interp(
            t,
            [0.0, 0.45, 0.72, 1.0],
            [
                metrics.front_depth * 0.86,
                metrics.front_depth * 0.98,
                metrics.front_depth * 1.08,
                metrics.front_depth * 0.84,
            ],
        )
    )


def _back_depth(metrics: _PanelMetrics, t: float) -> float:
    return float(
        np.interp(
            t,
            [0.0, 0.55, 1.0],
            [
                metrics.back_depth * 0.80,
                metrics.back_depth * 0.94,
                metrics.back_depth * 0.82,
            ],
        )
    )


def _armhole_depth(metrics: _PanelMetrics, t: float, cos_theta: float) -> float:
    if cos_theta >= 0.0:
        return _front_depth(metrics, t) * 0.68 * cos_theta

    return _back_depth(metrics, t) * 0.68 * cos_theta


def _half_extent_at_ratio(
    vertices: np.ndarray,
    center: float,
    y_min: float,
    height: float,
    ratio: float,
    *,
    axis: int,
) -> float:
    mask = _body_y_mask(vertices, y_min, height, ratio - 0.025, ratio + 0.025)
    if not np.any(mask):
        return height * 0.145

    return max(float(np.percentile(np.abs(vertices[mask, axis] - center), 88.0)), height * 0.120)


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
    repeated = (
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
    return faces[(~repeated) & (areas > 1e-10)]


def _append_vertex(
    vertices: list[tuple[float, float, float]],
    x: float,
    y: float,
    z: float,
) -> int:
    vertices.append((float(x), float(y), float(z)))
    return len(vertices) - 1


def _torso_t_for_y(metrics: _PanelMetrics, y: float) -> float:
    return float(
        np.clip((y - metrics.hem_y) / max(metrics.shoulder_y - metrics.hem_y, 1e-9), 0.0, 1.0)
    )


def _lerp(start: float, end: float, value: float) -> float:
    return float(start + ((end - start) * value))


def _lerp_array(start: np.ndarray, end: np.ndarray, value: float) -> np.ndarray:
    return start + ((end - start) * value)


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
