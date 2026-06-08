from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Iterable

import numpy as np
import torch
import trimesh
from PIL import Image, ImageDraw


CURRENT_DIR = Path(__file__).resolve().parent
GARMENT_BINDING_DIR = CURRENT_DIR.parent
AVATAR_PIPELINE_DIR = GARMENT_BINDING_DIR.parent
SMPLX_DIR = AVATAR_PIPELINE_DIR / "smplx"
SMPLX_RENDER_HELPER_PATH = SMPLX_DIR / "test_betas.py"
MODEL_PATH = SMPLX_DIR / "models"
OUTPUT_DIR = GARMENT_BINDING_DIR / "output"
DEFAULT_ARCHETYPE = "slim"
DEFAULT_POSE = "t_pose"
IMAGE_SIZE = (900, 1200)
IMAGE_MARGIN = 90

if str(AVATAR_PIPELINE_DIR) not in sys.path:
    sys.path.append(str(AVATAR_PIPELINE_DIR))

from archetypes.archetype_library import get_archetype  # noqa: E402
from garment_binding.garment_proxy import create_tshirt_proxy  # noqa: E402
from garment_binding.surface_fit import fit_garment_to_body  # noqa: E402
from poses.pose_library import get_pose  # noqa: E402


@dataclass(frozen=True)
class DebugMeshState:
    body_vertices: np.ndarray
    body_faces: np.ndarray
    body_joints: np.ndarray | None
    prefit_vertices: np.ndarray
    fitted_vertices: np.ndarray
    garment_faces: np.ndarray
    regions: dict[str, list[int]]
    archetype_name: str
    pose_name: str


COMPONENT_COLORS = (
    (76, 160, 255, 235),
    (255, 104, 104, 235),
    (90, 220, 150, 235),
    (255, 210, 90, 235),
    (205, 125, 255, 235),
    (85, 225, 230, 235),
    (255, 145, 70, 235),
    (190, 225, 90, 235),
)
ORIGIN_COLORS = {
    "torso": (70, 150, 255, 235),
    "left_sleeve": (255, 90, 90, 235),
    "right_sleeve": (90, 220, 135, 235),
    "bridge": (255, 225, 80, 235),
}
ORIGIN_REGION_GROUPS = {
    "torso": ("torso", "TORSO_FRONT", "TORSO_BACK"),
    "left_sleeve": ("left_sleeve", "LEFT_SLEEVE"),
    "right_sleeve": ("right_sleeve", "RIGHT_SLEEVE"),
    "bridge": ("underarm", "collar", "hem", "LEFT_ARMHOLE", "RIGHT_ARMHOLE", "COLLAR", "HEM"),
}


def build_debug_mesh_state(
    *,
    archetype_name: str = DEFAULT_ARCHETYPE,
    pose_name: str = DEFAULT_POSE,
) -> DebugMeshState:
    render_helper = load_smplx_render_helper()
    smplx = render_helper.smplx
    model = smplx.create(
        str(MODEL_PATH),
        model_type="smplx",
        gender="female",
        use_face_contour=True,
        num_betas=10,
        ext="npz",
    )
    archetype = get_archetype(archetype_name)
    pose = get_pose(pose_name)
    output = model(
        betas=torch.tensor([archetype.betas], dtype=torch.float32),
        body_pose=torch.tensor([pose.body_pose], dtype=torch.float32),
    )
    body_vertices = output.vertices.detach().cpu().numpy().squeeze()
    body_joints = output.joints.detach().cpu().numpy().squeeze()
    body_faces = np.asarray(model.faces, dtype=np.int32)
    garment = create_tshirt_proxy(body_vertices, body_faces)
    fitted_vertices = fit_garment_to_body(
        garment.vertices,
        garment.regions,
        body_vertices,
        body_faces,
        garment_faces=garment.faces,
        body_joints=body_joints,
        garment_region_labels=garment.region_labels,
        garment_curves=garment.curves,
    )
    return DebugMeshState(
        body_vertices=np.asarray(body_vertices, dtype=np.float64),
        body_faces=body_faces,
        body_joints=np.asarray(body_joints, dtype=np.float64),
        prefit_vertices=np.asarray(garment.vertices, dtype=np.float64),
        fitted_vertices=np.asarray(fitted_vertices, dtype=np.float64),
        garment_faces=np.asarray(garment.faces, dtype=np.int32),
        regions=garment.regions,
        archetype_name=archetype_name,
        pose_name=pose_name,
    )


def load_smplx_render_helper() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "tavaura_smplx_test_betas",
        SMPLX_RENDER_HELPER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load SMPL-X helper: {SMPLX_RENDER_HELPER_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mesh_components(faces: np.ndarray) -> list[list[int]]:
    edge_to_faces = build_edge_face_map(faces)
    face_neighbors: list[set[int]] = [set() for _ in range(len(faces))]
    for face_indices in edge_to_faces.values():
        if len(face_indices) < 2:
            continue

        for face_index in face_indices:
            face_neighbors[face_index].update(
                neighbor for neighbor in face_indices if neighbor != face_index
            )

    visited = np.zeros(len(faces), dtype=bool)
    components: list[list[int]] = []
    for face_index in range(len(faces)):
        if visited[face_index]:
            continue

        stack = [face_index]
        visited[face_index] = True
        component: list[int] = []
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbor in face_neighbors[current]:
                if visited[neighbor]:
                    continue

                visited[neighbor] = True
                stack.append(neighbor)

        components.append(component)

    return components


def build_edge_face_map(faces: np.ndarray) -> dict[tuple[int, int], list[int]]:
    edge_to_faces: dict[tuple[int, int], list[int]] = {}
    for face_index, face in enumerate(faces):
        for start, end in iter_face_edges(face):
            edge = tuple(sorted((int(start), int(end))))
            edge_to_faces.setdefault(edge, []).append(face_index)

    return edge_to_faces


def iter_face_edges(face: Iterable[int]) -> tuple[tuple[int, int], ...]:
    values = tuple(int(index) for index in face)
    return (
        (values[0], values[1]),
        (values[1], values[2]),
        (values[2], values[0]),
    )


def topology_metrics(vertices: np.ndarray, faces: np.ndarray) -> dict[str, object]:
    edge_to_faces = build_edge_face_map(faces)
    valences = np.asarray([len(face_indices) for face_indices in edge_to_faces.values()])
    boundary_edges = [edge for edge, face_indices in edge_to_faces.items() if len(face_indices) == 1]
    nonmanifold_edges = [
        edge for edge, face_indices in edge_to_faces.items() if len(face_indices) > 2
    ]
    components = mesh_components(faces)
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    return {
        "connected_component_count": len(components),
        "component_face_counts": [len(component) for component in components],
        "is_watertight": bool(mesh.is_watertight),
        "is_winding_consistent": bool(mesh.is_winding_consistent),
        "boundary_edge_count": len(boundary_edges),
        "nonmanifold_edge_count": len(nonmanifold_edges),
        "average_edge_valence": float(valences.mean()) if len(valences) else 0.0,
        "vertex_count": int(len(vertices)),
        "triangle_count": int(len(faces)),
        "disconnected_seam_clusters": count_edge_clusters(boundary_edges),
        "degenerate_triangle_count": count_degenerate_triangles(vertices, faces),
    }


def region_density_metrics(
    vertices: np.ndarray,
    faces: np.ndarray,
    regions: dict[str, list[int]],
) -> dict[str, dict[str, float | int]]:
    labels = _semantic_vertex_labels(regions, len(vertices))
    face_labels = [_majority_label(labels, face) for face in faces]
    triangles = vertices[faces]
    areas = np.linalg.norm(
        np.cross(
            triangles[:, 1] - triangles[:, 0],
            triangles[:, 2] - triangles[:, 0],
        ),
        axis=1,
    ) * 0.5
    edge_lengths_by_region: dict[str, list[float]] = {
        region_name: [] for region_name in sorted(set(labels))
    }
    for face in faces:
        for start, end in iter_face_edges(face):
            start_label = labels[int(start)]
            end_label = labels[int(end)]
            if start_label != end_label:
                continue

            length = float(np.linalg.norm(vertices[int(start)] - vertices[int(end)]))
            edge_lengths_by_region.setdefault(start_label, []).append(length)

    result: dict[str, dict[str, float | int]] = {}
    for region_name in sorted(set(labels)):
        vertex_count = sum(1 for label in labels if label == region_name)
        face_indices = [
            face_index for face_index, label in enumerate(face_labels) if label == region_name
        ]
        edge_lengths = edge_lengths_by_region.get(region_name, [])
        result[region_name] = {
            "vertex_count": int(vertex_count),
            "triangle_count": int(len(face_indices)),
            "surface_area": float(areas[face_indices].sum()) if face_indices else 0.0,
            "average_internal_edge_length": (
                float(np.mean(edge_lengths)) if edge_lengths else 0.0
            ),
        }

    return result


def count_degenerate_triangles(vertices: np.ndarray, faces: np.ndarray) -> int:
    if len(faces) == 0:
        return 0

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
    return int(np.count_nonzero(repeated | (areas <= 1e-10)))


def count_edge_clusters(edges: Iterable[tuple[int, int]]) -> int:
    edge_list = list(edges)
    if not edge_list:
        return 0

    vertex_to_edges: dict[int, list[int]] = {}
    for edge_index, (start, end) in enumerate(edge_list):
        vertex_to_edges.setdefault(start, []).append(edge_index)
        vertex_to_edges.setdefault(end, []).append(edge_index)

    visited = np.zeros(len(edge_list), dtype=bool)
    clusters = 0
    for edge_index in range(len(edge_list)):
        if visited[edge_index]:
            continue

        clusters += 1
        stack = [edge_index]
        visited[edge_index] = True
        while stack:
            current = stack.pop()
            for vertex in edge_list[current]:
                for neighbor in vertex_to_edges[vertex]:
                    if visited[neighbor]:
                        continue

                    visited[neighbor] = True
                    stack.append(neighbor)

    return clusters


def render_component_islands(
    *,
    state: DebugMeshState,
    garment_vertices: np.ndarray,
    output_path: Path,
    view: str,
) -> None:
    components = mesh_components(state.garment_faces)
    face_colors = np.zeros((len(state.garment_faces), 4), dtype=np.uint8)
    for component_index, component_faces in enumerate(components):
        color = COMPONENT_COLORS[component_index % len(COMPONENT_COLORS)]
        face_colors[component_faces] = color

    render_colored_faces(
        body_vertices=state.body_vertices,
        body_faces=state.body_faces,
        garment_vertices=garment_vertices,
        garment_faces=state.garment_faces,
        face_colors=face_colors,
        output_path=output_path,
        view=view,
    )


def render_vertex_origins(
    *,
    state: DebugMeshState,
    garment_vertices: np.ndarray,
    output_path: Path,
    view: str,
) -> None:
    vertex_labels = classify_vertex_origins(state.regions, len(state.prefit_vertices))
    face_colors = face_colors_from_vertex_labels(state.garment_faces, vertex_labels)
    render_colored_faces(
        body_vertices=state.body_vertices,
        body_faces=state.body_faces,
        garment_vertices=garment_vertices,
        garment_faces=state.garment_faces,
        face_colors=face_colors,
        output_path=output_path,
        view=view,
    )


def classify_vertex_origins(regions: dict[str, list[int]], vertex_count: int) -> list[str]:
    labels = ["bridge"] * vertex_count
    for output_label, region_names in ORIGIN_REGION_GROUPS.items():
        for region_name in region_names:
            for index in regions.get(region_name, []):
                if 0 <= index < vertex_count:
                    labels[index] = output_label

    return labels


def face_colors_from_vertex_labels(faces: np.ndarray, labels: list[str]) -> np.ndarray:
    colors = np.zeros((len(faces), 4), dtype=np.uint8)
    for face_index, face in enumerate(faces):
        face_labels = [labels[int(vertex_index)] for vertex_index in face]
        label = max(set(face_labels), key=face_labels.count)
        colors[face_index] = ORIGIN_COLORS[label]

    return colors


def _semantic_vertex_labels(regions: dict[str, list[int]], vertex_count: int) -> list[str]:
    labels = ["unclassified"] * vertex_count
    for region_name, indices in regions.items():
        for index in indices:
            if 0 <= index < vertex_count:
                labels[index] = region_name

    return labels


def _majority_label(labels: list[str], face: Iterable[int]) -> str:
    face_labels = [labels[int(vertex_index)] for vertex_index in face]
    return max(set(face_labels), key=face_labels.count)


def render_colored_faces(
    *,
    body_vertices: np.ndarray,
    body_faces: np.ndarray,
    garment_vertices: np.ndarray,
    garment_faces: np.ndarray,
    face_colors: np.ndarray,
    output_path: Path,
    view: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bounds_vertices = np.vstack((body_vertices, garment_vertices))
    projector = _make_projector(bounds_vertices, view)
    image = Image.new("RGBA", IMAGE_SIZE, (0, 0, 0, 255))
    draw = ImageDraw.Draw(image, "RGBA")
    _draw_faces(
        draw,
        projector,
        body_vertices,
        body_faces,
        np.tile(np.asarray((238, 238, 238, 255), dtype=np.uint8), (len(body_faces), 1)),
    )
    _draw_faces(draw, projector, garment_vertices, garment_faces, face_colors)
    image.convert("RGB").save(output_path)


def render_seam_edges(
    *,
    state: DebugMeshState,
    garment_vertices: np.ndarray,
    output_path: Path,
    view: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    edge_to_faces = build_edge_face_map(state.garment_faces)
    internal_edges = [edge for edge, face_indices in edge_to_faces.items() if len(face_indices) == 2]
    boundary_edges = [edge for edge, face_indices in edge_to_faces.items() if len(face_indices) == 1]
    nonmanifold_edges = [
        edge for edge, face_indices in edge_to_faces.items() if len(face_indices) > 2
    ]

    bounds_vertices = np.vstack((state.body_vertices, garment_vertices))
    projector = _make_projector(bounds_vertices, view)
    image = Image.new("RGBA", IMAGE_SIZE, (0, 0, 0, 255))
    draw = ImageDraw.Draw(image, "RGBA")
    _draw_faces(
        draw,
        projector,
        state.body_vertices,
        state.body_faces,
        np.tile(np.asarray((238, 238, 238, 255), dtype=np.uint8), (len(state.body_faces), 1)),
    )
    _draw_faces(
        draw,
        projector,
        garment_vertices,
        state.garment_faces,
        np.tile(np.asarray((42, 42, 42, 145), dtype=np.uint8), (len(state.garment_faces), 1)),
    )
    _draw_edges(draw, projector, garment_vertices, internal_edges, (70, 230, 120, 180), width=1)
    _draw_edges(draw, projector, garment_vertices, boundary_edges, (255, 65, 65, 255), width=3)
    _draw_edges(draw, projector, garment_vertices, nonmanifold_edges, (255, 225, 65, 255), width=4)
    image.convert("RGB").save(output_path)


def render_stage_mesh(
    *,
    state: DebugMeshState,
    garment_vertices: np.ndarray,
    output_path: Path,
    view: str,
    wireframe: bool,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bounds_vertices = np.vstack((state.body_vertices, garment_vertices))
    projector = _make_projector(bounds_vertices, view)
    image = Image.new("RGBA", IMAGE_SIZE, (0, 0, 0, 255))
    draw = ImageDraw.Draw(image, "RGBA")
    _draw_faces(
        draw,
        projector,
        state.body_vertices,
        state.body_faces,
        np.tile(np.asarray((238, 238, 238, 255), dtype=np.uint8), (len(state.body_faces), 1)),
    )
    _draw_faces(
        draw,
        projector,
        garment_vertices,
        state.garment_faces,
        np.tile(np.asarray((75, 150, 225, 230), dtype=np.uint8), (len(state.garment_faces), 1)),
    )
    if wireframe:
        _draw_edges(
            draw,
            projector,
            garment_vertices,
            build_edge_face_map(state.garment_faces).keys(),
            (255, 255, 255, 220),
            width=1,
        )

    image.convert("RGB").save(output_path)


def export_obj(vertices: np.ndarray, faces: np.ndarray, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    mesh.export(output_path)


def write_json(data: object, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _draw_faces(
    draw: ImageDraw.ImageDraw,
    projector: "_Projector",
    vertices: np.ndarray,
    faces: np.ndarray,
    face_colors: np.ndarray,
) -> None:
    face_depths = projector.depth(vertices[faces].mean(axis=1))
    for face_index in np.argsort(face_depths):
        polygon = [tuple(point) for point in projector.project(vertices[faces[face_index]])]
        draw.polygon(polygon, fill=tuple(int(value) for value in face_colors[face_index]))


def _draw_edges(
    draw: ImageDraw.ImageDraw,
    projector: "_Projector",
    vertices: np.ndarray,
    edges: Iterable[tuple[int, int]],
    color: tuple[int, int, int, int],
    *,
    width: int,
) -> None:
    for start, end in edges:
        points = projector.project(vertices[[int(start), int(end)]])
        draw.line([tuple(points[0]), tuple(points[1])], fill=color, width=width)


@dataclass(frozen=True)
class _Projector:
    view: str
    offset: np.ndarray
    scale: float

    def project(self, vertices: np.ndarray) -> np.ndarray:
        coords = _view_coordinates(vertices, self.view)
        projected = (coords - self.offset) * self.scale
        projected[:, 0] += IMAGE_MARGIN
        projected[:, 1] = IMAGE_SIZE[1] - IMAGE_MARGIN - projected[:, 1]
        return projected

    def depth(self, vertices: np.ndarray) -> np.ndarray:
        if self.view == "side":
            return vertices[:, 0]

        return vertices[:, 2]


def _make_projector(vertices: np.ndarray, view: str) -> _Projector:
    coords = _view_coordinates(vertices, view)
    minimum = coords.min(axis=0)
    maximum = coords.max(axis=0)
    span = np.maximum(maximum - minimum, 1e-9)
    usable_width = IMAGE_SIZE[0] - (IMAGE_MARGIN * 2)
    usable_height = IMAGE_SIZE[1] - (IMAGE_MARGIN * 2)
    scale = float(min(usable_width / span[0], usable_height / span[1]))
    scaled_width = span[0] * scale
    scaled_height = span[1] * scale
    offset = minimum.copy()
    offset[0] -= (usable_width - scaled_width) / (2.0 * scale)
    offset[1] -= (usable_height - scaled_height) / (2.0 * scale)
    return _Projector(view=view, offset=offset, scale=scale)


def _view_coordinates(vertices: np.ndarray, view: str) -> np.ndarray:
    if view == "side":
        return vertices[:, [2, 1]]
    if view == "front":
        return vertices[:, [0, 1]]

    raise ValueError(f"Unsupported view: {view}")
