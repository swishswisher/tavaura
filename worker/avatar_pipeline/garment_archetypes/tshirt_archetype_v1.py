from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw


REGION_FRONT_PANEL = "front_panel"
REGION_BACK_PANEL = "back_panel"
REGION_LEFT_SLEEVE = "left_sleeve"
REGION_RIGHT_SLEEVE = "right_sleeve"
REGION_COLLAR_OPENING = "collar_opening"
REGION_HEM = "hem"

REGIONS = (
    REGION_FRONT_PANEL,
    REGION_BACK_PANEL,
    REGION_LEFT_SLEEVE,
    REGION_RIGHT_SLEEVE,
    REGION_COLLAR_OPENING,
    REGION_HEM,
)

REGION_COLORS = {
    REGION_FRONT_PANEL: (72, 132, 196),
    REGION_BACK_PANEL: (54, 81, 116),
    REGION_LEFT_SLEEVE: (72, 166, 132),
    REGION_RIGHT_SLEEVE: (80, 184, 176),
    REGION_COLLAR_OPENING: (188, 92, 166),
    REGION_HEM: (92, 170, 210),
}

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


@dataclass(frozen=True)
class TshirtArchetypeV1:
    """Canonical closed T-shirt topology used for Phase B validation.

    The mesh is intentionally watertight: collar, hem, and sleeve cuff areas
    are tagged as semantic rim/cap regions instead of being open boundaries.
    Runtime apparel openings can be cut later after the topology contract is
    stable.
    """

    mesh: trimesh.Trimesh
    face_regions: tuple[str, ...]
    regions: dict[str, list[int]]


@dataclass(frozen=True)
class TopologyReport:
    connected_components: int
    boundary_edges: int
    non_manifold_edges: int
    vertex_count: int
    face_count: int


def generate_tshirt_archetype_v1() -> TshirtArchetypeV1:
    """Generate a connected, closed canonical T-shirt archetype mesh.

    This generator creates a clean sealed topology asset for validation. It is
    not body-fitted and does not modify the existing SMPL-X or garment fitting
    paths.
    """

    x_values = np.linspace(-1.18, 1.18, 83)
    y_values = np.linspace(0.0, 1.56, 67)
    included_cells = _build_silhouette_cells(x_values, y_values)

    vertices: list[tuple[float, float, float]] = []
    vertex_by_key: dict[tuple[str, int, int], int] = {}
    faces: list[tuple[int, int, int]] = []
    face_regions: list[str] = []

    def vertex_index(side: str, xi: int, yi: int) -> int:
        key = (side, xi, yi)
        existing = vertex_by_key.get(key)
        if existing is not None:
            return existing

        x = float(x_values[xi])
        y = float(y_values[yi])
        z = _half_depth(x, y)
        if side == "back":
            z *= -1.0

        vertex_by_key[key] = len(vertices)
        vertices.append((x, y, z))
        return vertex_by_key[key]

    for cell in sorted(included_cells):
        xi, yi = cell
        front_region = _classify_face_region(x_values, y_values, xi, yi, "front")
        back_region = _classify_face_region(x_values, y_values, xi, yi, "back")

        f00 = vertex_index("front", xi, yi)
        f10 = vertex_index("front", xi + 1, yi)
        f11 = vertex_index("front", xi + 1, yi + 1)
        f01 = vertex_index("front", xi, yi + 1)
        b00 = vertex_index("back", xi, yi)
        b10 = vertex_index("back", xi + 1, yi)
        b11 = vertex_index("back", xi + 1, yi + 1)
        b01 = vertex_index("back", xi, yi + 1)

        _add_quad(faces, face_regions, f00, f10, f11, f01, front_region)
        _add_quad(faces, face_regions, b10, b00, b01, b11, back_region)

        for direction, edge_vertices in _boundary_edges_for_cell(
            cell, included_cells, f00, f10, f11, f01, b00, b10, b11, b01
        ):
            side_region = _classify_boundary_region(x_values, y_values, xi, yi, direction)
            _add_quad(faces, face_regions, *edge_vertices, side_region)

    mesh = trimesh.Trimesh(
        vertices=np.asarray(vertices, dtype=np.float64),
        faces=np.asarray(faces, dtype=np.int64),
        process=False,
    )
    regions = _group_faces_by_region(face_regions)

    return TshirtArchetypeV1(
        mesh=mesh,
        face_regions=tuple(face_regions),
        regions=regions,
    )


def validate_topology(mesh: trimesh.Trimesh) -> TopologyReport:
    edge_to_faces = _edge_to_faces(mesh.faces)
    boundary_edges = sum(1 for face_ids in edge_to_faces.values() if len(face_ids) == 1)
    non_manifold_edges = sum(1 for face_ids in edge_to_faces.values() if len(face_ids) > 2)

    return TopologyReport(
        connected_components=_count_face_components(len(mesh.faces), edge_to_faces),
        boundary_edges=boundary_edges,
        non_manifold_edges=non_manifold_edges,
        vertex_count=int(len(mesh.vertices)),
        face_count=int(len(mesh.faces)),
    )


def render_archetype_views(
    archetype: TshirtArchetypeV1,
    output_dir: Path | str = OUTPUT_DIR,
) -> dict[str, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    outputs = {
        "front": output_path / "tshirt_archetype_v1_front.png",
        "side": output_path / "tshirt_archetype_v1_side.png",
        "wireframe": output_path / "tshirt_archetype_v1_wireframe.png",
    }
    _render_shaded(archetype, outputs["front"], view="front")
    _render_shaded(archetype, outputs["side"], view="side")
    _render_wireframe(archetype, outputs["wireframe"], view="front")
    return outputs


def export_mesh(archetype: TshirtArchetypeV1, output_path: Path | str) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    archetype.mesh.export(path)
    return path


def _build_silhouette_cells(
    x_values: np.ndarray,
    y_values: np.ndarray,
) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for xi in range(len(x_values) - 1):
        for yi in range(len(y_values) - 1):
            x = float((x_values[xi] + x_values[xi + 1]) * 0.5)
            y = float((y_values[yi] + y_values[yi + 1]) * 0.5)
            if _inside_tshirt_silhouette(x, y):
                cells.add((xi, yi))
    return cells


def _inside_tshirt_silhouette(x: float, y: float) -> bool:
    if y < 0.0 or y > 1.55:
        return False

    torso_width = _torso_half_width(y)
    in_torso = 0.02 <= y <= 1.34 and abs(x) <= torso_width

    abs_x = abs(x)
    sleeve_t = (abs_x - 0.42) / 0.70
    sleeve_center_y = 0.93 - 0.10 * sleeve_t
    sleeve_half_height = 0.27 - 0.04 * max(0.0, sleeve_t)
    in_sleeve_span = 0.42 <= abs_x <= 1.12 and 0.0 <= sleeve_t <= 1.0
    left_sleeve = x < 0.0 and in_sleeve_span and abs(y - sleeve_center_y) <= sleeve_half_height
    right_sleeve = x > 0.0 and in_sleeve_span and abs(y - sleeve_center_y) <= sleeve_half_height

    shoulder_band = 1.12 <= y <= 1.43
    shoulder_width = 0.38 + 0.26 * (1.43 - y) / 0.31
    in_shoulder = shoulder_band and abs(x) <= shoulder_width

    return in_torso or left_sleeve or right_sleeve or in_shoulder


def _torso_half_width(y: float) -> float:
    y_points = np.asarray([0.02, 0.38, 0.92, 1.34], dtype=np.float64)
    widths = np.asarray([0.43, 0.39, 0.51, 0.58], dtype=np.float64)
    return float(np.interp(y, y_points, widths, left=0.43, right=0.50))


def _half_depth(x: float, y: float) -> float:
    base_depth = 0.090
    chest_lift = 0.042 * np.exp(-((y - 0.93) ** 2) / 0.060)
    side_softening = 1.0 - min(0.26, abs(x) * 0.12)
    return float((base_depth + chest_lift) * side_softening)


def _classify_face_region(
    x_values: np.ndarray,
    y_values: np.ndarray,
    xi: int,
    yi: int,
    side: str,
) -> str:
    x = float((x_values[xi] + x_values[xi + 1]) * 0.5)
    y = float((y_values[yi] + y_values[yi + 1]) * 0.5)

    if _is_collar_region(x, y):
        return REGION_COLLAR_OPENING
    if y <= 0.13:
        return REGION_HEM
    if x <= -0.48 and 0.58 <= y <= 1.24:
        return REGION_LEFT_SLEEVE
    if x >= 0.48 and 0.58 <= y <= 1.24:
        return REGION_RIGHT_SLEEVE
    if side == "back":
        return REGION_BACK_PANEL
    return REGION_FRONT_PANEL


def _classify_boundary_region(
    x_values: np.ndarray,
    y_values: np.ndarray,
    xi: int,
    yi: int,
    direction: str,
) -> str:
    x = float((x_values[xi] + x_values[xi + 1]) * 0.5)
    y = float((y_values[yi] + y_values[yi + 1]) * 0.5)

    if _is_collar_region(x, y) or (direction == "north" and abs(x) <= 0.38 and y > 1.20):
        return REGION_COLLAR_OPENING
    if direction == "south" or y <= 0.13:
        return REGION_HEM
    if x < -0.45:
        return REGION_LEFT_SLEEVE
    if x > 0.45:
        return REGION_RIGHT_SLEEVE
    return REGION_FRONT_PANEL


def _is_collar_region(x: float, y: float) -> bool:
    collar_x = abs(x) / 0.33
    collar_y = (y - 1.21) / 0.20
    return y >= 1.10 and (collar_x * collar_x + collar_y * collar_y) <= 1.0


def _boundary_edges_for_cell(
    cell: tuple[int, int],
    included_cells: set[tuple[int, int]],
    f00: int,
    f10: int,
    f11: int,
    f01: int,
    b00: int,
    b10: int,
    b11: int,
    b01: int,
) -> list[tuple[str, tuple[int, int, int, int]]]:
    xi, yi = cell
    edges: list[tuple[str, tuple[int, int, int, int]]] = []
    if (xi, yi - 1) not in included_cells:
        edges.append(("south", (b00, f00, f10, b10)))
    if (xi + 1, yi) not in included_cells:
        edges.append(("east", (b10, f10, f11, b11)))
    if (xi, yi + 1) not in included_cells:
        edges.append(("north", (b11, f11, f01, b01)))
    if (xi - 1, yi) not in included_cells:
        edges.append(("west", (b01, f01, f00, b00)))
    return edges


def _add_quad(
    faces: list[tuple[int, int, int]],
    face_regions: list[str],
    a: int,
    b: int,
    c: int,
    d: int,
    region: str,
) -> None:
    faces.append((a, b, c))
    face_regions.append(region)
    faces.append((a, c, d))
    face_regions.append(region)


def _group_faces_by_region(face_regions: list[str]) -> dict[str, list[int]]:
    grouped = {region: [] for region in REGIONS}
    for index, region in enumerate(face_regions):
        grouped.setdefault(region, []).append(index)
    return grouped


def _edge_to_faces(faces: np.ndarray) -> dict[tuple[int, int], list[int]]:
    edge_to_faces: dict[tuple[int, int], list[int]] = defaultdict(list)
    for face_index, face in enumerate(faces):
        a, b, c = (int(face[0]), int(face[1]), int(face[2]))
        for edge in ((a, b), (b, c), (c, a)):
            edge_to_faces[tuple(sorted(edge))].append(face_index)
    return edge_to_faces


def _count_face_components(
    face_count: int,
    edge_to_faces: dict[tuple[int, int], list[int]],
) -> int:
    adjacency: list[set[int]] = [set() for _ in range(face_count)]
    for face_ids in edge_to_faces.values():
        if len(face_ids) < 2:
            continue
        first = face_ids[0]
        for other in face_ids[1:]:
            adjacency[first].add(other)
            adjacency[other].add(first)

    visited: set[int] = set()
    components = 0
    for face_index in range(face_count):
        if face_index in visited:
            continue
        components += 1
        queue: deque[int] = deque([face_index])
        visited.add(face_index)
        while queue:
            current = queue.popleft()
            for neighbor in adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
    return components


def _render_shaded(
    archetype: TshirtArchetypeV1,
    output_path: Path,
    view: str,
) -> None:
    image_size = (900, 1200)
    projected = _project_vertices(archetype.mesh.vertices, image_size, view)
    image = Image.new("RGB", image_size, "#111111")
    draw = ImageDraw.Draw(image, "RGBA")
    faces = archetype.mesh.faces
    depth_axis = 2 if view == "front" else 0

    draw_items = []
    for face_index, face in enumerate(faces):
        points = [(float(projected[index, 0]), float(projected[index, 1])) for index in face]
        depth = float(np.mean(archetype.mesh.vertices[face, depth_axis]))
        color = REGION_COLORS[archetype.face_regions[face_index]]
        shade = _face_shade(archetype.mesh.vertices[face], view)
        shaded = tuple(max(0, min(255, int(channel * shade))) for channel in color)
        draw_items.append((depth, points, shaded))

    reverse = view == "front"
    for _, points, color in sorted(draw_items, key=lambda item: item[0], reverse=reverse):
        draw.polygon(points, fill=(*color, 235))

    image.save(output_path, format="PNG")


def _render_wireframe(
    archetype: TshirtArchetypeV1,
    output_path: Path,
    view: str,
) -> None:
    image_size = (900, 1200)
    projected = _project_vertices(archetype.mesh.vertices, image_size, view)
    image = Image.new("RGB", image_size, "#111111")
    draw = ImageDraw.Draw(image, "RGBA")

    _render_shaded(archetype, output_path, view=view)
    image = Image.open(output_path).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    for edge in sorted(archetype.mesh.edges_unique.tolist()):
        a, b = edge
        draw.line(
            [
                (float(projected[a, 0]), float(projected[a, 1])),
                (float(projected[b, 0]), float(projected[b, 1])),
            ],
            fill=(245, 245, 245, 120),
            width=1,
        )

    image.convert("RGB").save(output_path, format="PNG")


def _project_vertices(
    vertices: np.ndarray,
    image_size: tuple[int, int],
    view: str,
) -> np.ndarray:
    width, height = image_size
    if view == "front":
        coords = np.column_stack([vertices[:, 0], vertices[:, 1]])
    elif view == "side":
        coords = np.column_stack([vertices[:, 2], vertices[:, 1]])
    else:
        raise ValueError(f"Unknown render view: {view}")

    coords[:, 1] *= -1.0
    min_xy = coords.min(axis=0)
    max_xy = coords.max(axis=0)
    span = np.maximum(max_xy - min_xy, 1e-9)
    margin = 82
    scale = min((width - 2 * margin) / span[0], (height - 2 * margin) / span[1])
    projected = (coords - min_xy) * scale
    projected[:, 0] += (width - span[0] * scale) * 0.5
    projected[:, 1] += (height - span[1] * scale) * 0.5
    return projected


def _face_shade(face_vertices: np.ndarray, view: str) -> float:
    normal = np.cross(
        face_vertices[1] - face_vertices[0],
        face_vertices[2] - face_vertices[0],
    )
    norm = float(np.linalg.norm(normal))
    if norm < 1e-9:
        return 0.75
    normal /= norm
    light = np.array([0.22, -0.34, 0.91], dtype=np.float64)
    if view == "side":
        light = np.array([0.82, -0.24, 0.42], dtype=np.float64)
    light /= np.linalg.norm(light)
    return float(0.55 + 0.45 * abs(np.dot(normal, light)))
