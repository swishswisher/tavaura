from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .garment_regions import classify_garment_regions
from .panels import generate_panel_tshirt


@dataclass(frozen=True)
class GarmentProxyMesh:
    vertices: np.ndarray
    faces: np.ndarray
    # Explicit panel regions drive fitting. The legacy regions are retained only
    # for older diagnostics that still expect coarse lowercase names.
    regions: dict[str, list[int]]
    region_labels: tuple[str, ...] = ()
    explicit_regions: dict[str, list[int]] | None = None
    legacy_regions: dict[str, list[int]] | None = None
    curves: dict[str, list[int]] | None = None


def create_tshirt_proxy(
    vertices,
    faces,
    *,
    surface_offset: float = 0.018,
) -> GarmentProxyMesh:
    body_vertices = _as_vertices(vertices)
    body_faces = _as_faces(faces)
    archetype = generate_panel_tshirt(
        body_vertices,
        body_faces,
        surface_offset=surface_offset,
    )
    legacy_regions = classify_garment_regions(archetype.vertices)

    return GarmentProxyMesh(
        vertices=archetype.vertices,
        faces=archetype.faces,
        regions=archetype.regions,
        region_labels=archetype.region_labels,
        explicit_regions=archetype.regions,
        legacy_regions=legacy_regions,
        curves=archetype.curves,
    )


def _create_surface_tshirt_proxy(
    vertices,
    faces,
    *,
    surface_offset: float = 0.018,
) -> GarmentProxyMesh:
    body_vertices = _as_vertices(vertices)
    body_faces = _as_faces(faces)
    selected_faces = _select_tshirt_faces(body_vertices, body_faces)
    if len(selected_faces) == 0:
        raise ValueError("Could not create T-shirt proxy; no torso faces selected.")

    selected_faces = _remove_small_face_components(selected_faces)
    unique_indices, compact_faces = np.unique(
        selected_faces.reshape(-1),
        return_inverse=True,
    )
    proxy_faces = compact_faces.reshape((-1, 3)).astype(np.int32)
    proxy_faces = _remove_tiny_faces(body_vertices[unique_indices], proxy_faces)

    vertex_normals = _estimate_vertex_normals(body_vertices, body_faces)
    proxy_body_vertices = body_vertices[unique_indices]
    proxy_normals = vertex_normals[unique_indices]
    boundary_vertices, boundary_edges = _find_boundary_topology(proxy_faces)
    proxy_body_vertices = _smooth_proxy_surface(
        proxy_body_vertices,
        proxy_faces,
        boundary_vertices,
    )
    proxy_body_vertices = _preserve_garment_structure(
        proxy_body_vertices,
        body_vertices,
    )
    proxy_body_vertices = _relax_fabric_surface(
        proxy_body_vertices,
        proxy_faces,
        boundary_vertices,
    )
    inflation = _calculate_region_inflation(
        proxy_body_vertices,
        body_vertices,
        boundary_vertices,
        base_offset=surface_offset,
    )
    proxy_vertices = proxy_body_vertices + (proxy_normals * inflation[:, None])
    proxy_vertices, proxy_faces = _add_boundary_rim(
        proxy_vertices,
        proxy_faces,
        proxy_normals,
        boundary_edges,
    )
    regions = classify_garment_regions(proxy_vertices)

    return GarmentProxyMesh(vertices=proxy_vertices, faces=proxy_faces, regions=regions)


def _select_tshirt_faces(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    face_vertices = vertices[faces]
    centers = face_vertices.mean(axis=1)
    y_min = float(vertices[:, 1].min())
    y_max = float(vertices[:, 1].max())
    height = max(y_max - y_min, 1e-9)
    y_ratio = (centers[:, 1] - y_min) / height
    center_x = float(np.median(vertices[:, 0]))
    abs_x = np.abs(centers[:, 0] - center_x)

    # Approximate a fitted T-shirt using vertical body bands:
    # lower torso at the hem, narrower waist, broader chest/shoulder cap.
    half_width = np.interp(
        y_ratio,
        [0.46, 0.56, 0.68, 0.78],
        [0.19, 0.17, 0.22, 0.29],
    ) * height

    torso_band = (y_ratio >= 0.455) & (y_ratio <= 0.785)
    central_torso = abs_x <= half_width

    # Leave a small collar opening so the proxy reads as a shirt, not a body shell.
    collar_opening = (y_ratio >= 0.715) & (abs_x <= (height * 0.065))

    return faces[torso_band & central_torso & ~collar_opening]


def _remove_small_face_components(faces: np.ndarray) -> np.ndarray:
    vertex_to_faces: dict[int, list[int]] = {}
    for face_index, face in enumerate(faces):
        for vertex_index in face:
            vertex_to_faces.setdefault(int(vertex_index), []).append(face_index)

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
            for vertex_index in faces[current]:
                for neighbor in vertex_to_faces[int(vertex_index)]:
                    if visited[neighbor]:
                        continue

                    visited[neighbor] = True
                    stack.append(neighbor)

        components.append(component)

    if not components:
        return faces

    largest_size = max(len(component) for component in components)
    min_size = max(24, int(largest_size * 0.08))
    kept_face_indices = [
        face_index
        for component in components
        if len(component) >= min_size
        for face_index in component
    ]
    if not kept_face_indices:
        return faces

    return faces[np.array(sorted(kept_face_indices), dtype=np.int32)]


def _remove_tiny_faces(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    triangles = vertices[faces]
    areas = np.linalg.norm(
        np.cross(
            triangles[:, 1] - triangles[:, 0],
            triangles[:, 2] - triangles[:, 0],
        ),
        axis=1,
    ) * 0.5
    if len(areas) == 0:
        return faces

    positive_areas = areas[areas > 1e-12]
    if len(positive_areas) == 0:
        return faces

    min_area = float(np.median(positive_areas) * 0.015)
    return faces[areas >= min_area]


def _find_boundary_topology(faces: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    edge_counts: dict[tuple[int, int], int] = {}
    for face in faces:
        for start, end in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            edge = tuple(sorted((int(start), int(end))))
            edge_counts[edge] = edge_counts.get(edge, 0) + 1

    boundary_edges = np.array(
        [edge for edge, count in edge_counts.items() if count == 1],
        dtype=np.int32,
    )
    if len(boundary_edges) == 0:
        return np.array([], dtype=np.int32), boundary_edges

    return np.unique(boundary_edges.reshape(-1)), boundary_edges


def _smooth_proxy_surface(
    vertices: np.ndarray,
    faces: np.ndarray,
    boundary_vertices: np.ndarray,
) -> np.ndarray:
    adjacency = _build_vertex_adjacency(len(vertices), faces)
    boundary_mask = np.zeros(len(vertices), dtype=bool)
    boundary_mask[boundary_vertices] = True
    smoothed = vertices.copy()

    for _ in range(6):
        next_vertices = smoothed.copy()
        for vertex_index, neighbors in enumerate(adjacency):
            if not neighbors:
                continue

            neighbor_average = smoothed[list(neighbors)].mean(axis=0)
            weight = 0.48 if boundary_mask[vertex_index] else 0.14
            next_vertices[vertex_index] = (
                smoothed[vertex_index] * (1.0 - weight)
            ) + (neighbor_average * weight)

        smoothed = next_vertices

    return smoothed


def _preserve_garment_structure(
    vertices: np.ndarray,
    body_vertices: np.ndarray,
) -> np.ndarray:
    structured = vertices.copy()
    y_min, y_max, height = _body_vertical_metrics(body_vertices)
    y_ratio = (structured[:, 1] - y_min) / height
    center_x = float(np.median(body_vertices[:, 0]))
    center_z = float(np.median(body_vertices[:, 2]))

    structured = _preserve_torso_width(
        structured,
        y_ratio,
        center_x,
        height,
    )
    structured = _shape_sleeves_and_armpits(
        structured,
        y_ratio,
        center_x,
        center_z,
        height,
    )
    structured = _smooth_chest_shell(
        structured,
        y_ratio,
        center_x,
        center_z,
        height,
    )
    return structured


def _preserve_torso_width(
    vertices: np.ndarray,
    y_ratio: np.ndarray,
    center_x: float,
    height: float,
) -> np.ndarray:
    structured = vertices.copy()
    for lower, upper in _iter_vertical_bands(0.455, 0.785, 18):
        band_mask = (y_ratio >= lower) & (y_ratio < upper)
        if not np.any(band_mask):
            continue

        band_center = (lower + upper) / 2.0
        target_half_width = (
            np.interp(
                band_center,
                [0.455, 0.54, 0.64, 0.72, 0.785],
                [0.205, 0.195, 0.235, 0.275, 0.305],
            )
            * height
        )
        relative_x = structured[band_mask, 0] - center_x
        abs_x = np.abs(relative_x)
        current_half_width = float(np.percentile(abs_x, 90))
        if current_half_width <= 1e-9 or current_half_width >= target_half_width:
            continue

        scale = min(1.16, target_half_width / current_half_width)
        side_strength = np.clip(abs_x / max(current_half_width, 1e-9), 0.0, 1.0)
        local_scale = 1.0 + ((scale - 1.0) * side_strength * 0.75)
        structured[band_mask, 0] = center_x + (relative_x * local_scale)

    return structured


def _shape_sleeves_and_armpits(
    vertices: np.ndarray,
    y_ratio: np.ndarray,
    center_x: float,
    center_z: float,
    height: float,
) -> np.ndarray:
    structured = vertices.copy()
    relative_x = structured[:, 0] - center_x
    abs_x_ratio = np.abs(relative_x) / height
    side_sign = np.sign(relative_x)
    side_sign[side_sign == 0.0] = 1.0

    sleeve_mask = (y_ratio >= 0.62) & (y_ratio <= 0.79) & (abs_x_ratio >= 0.175)
    structured[sleeve_mask, 0] += side_sign[sleeve_mask] * height * 0.018

    for side in (-1.0, 1.0):
        side_mask = sleeve_mask & (side_sign == side)
        if not np.any(side_mask):
            continue

        side_center_z = float(np.median(structured[side_mask, 2]))
        structured[side_mask, 2] = side_center_z + (
            (structured[side_mask, 2] - side_center_z) * 1.10
        )

    armpit_mask = (y_ratio >= 0.585) & (y_ratio <= 0.69) & (abs_x_ratio >= 0.145)
    structured[armpit_mask, 0] += side_sign[armpit_mask] * height * 0.024
    structured[armpit_mask, 1] += height * 0.006
    structured[armpit_mask, 2] = center_z + (
        (structured[armpit_mask, 2] - center_z) * 1.05
    )
    return structured


def _smooth_chest_shell(
    vertices: np.ndarray,
    y_ratio: np.ndarray,
    center_x: float,
    center_z: float,
    height: float,
) -> np.ndarray:
    structured = vertices.copy()
    abs_x_ratio = np.abs(structured[:, 0] - center_x) / height
    chest_mask = (y_ratio >= 0.60) & (y_ratio <= 0.735) & (abs_x_ratio <= 0.22)
    if not np.any(chest_mask):
        return structured

    front_mask = chest_mask & (structured[:, 2] >= center_z)
    back_mask = chest_mask & (structured[:, 2] < center_z)
    if np.any(front_mask):
        front_center_z = float(np.median(structured[front_mask, 2]))
        structured[front_mask, 2] = front_center_z + (
            (structured[front_mask, 2] - front_center_z) * 0.52
        )
    if np.any(back_mask):
        back_center_z = float(np.median(structured[back_mask, 2]))
        structured[back_mask, 2] = back_center_z + (
            (structured[back_mask, 2] - back_center_z) * 0.72
        )

    structured[chest_mask, 0] = center_x + (
        (structured[chest_mask, 0] - center_x) * 1.025
    )
    return structured


def _relax_fabric_surface(
    vertices: np.ndarray,
    faces: np.ndarray,
    boundary_vertices: np.ndarray,
    *,
    iterations: int = 3,
) -> np.ndarray:
    adjacency = _build_vertex_adjacency(len(vertices), faces)
    boundary_mask = np.zeros(len(vertices), dtype=bool)
    boundary_mask[boundary_vertices] = True
    relaxed = vertices.copy()

    for _ in range(iterations):
        next_vertices = relaxed.copy()
        for vertex_index, neighbors in enumerate(adjacency):
            if not neighbors:
                continue

            neighbor_average = relaxed[list(neighbors)].mean(axis=0)
            weight = 0.10 if boundary_mask[vertex_index] else 0.075
            next_vertices[vertex_index] = (
                relaxed[vertex_index] * (1.0 - weight)
            ) + (neighbor_average * weight)

        relaxed = next_vertices

    return relaxed


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


def _calculate_region_inflation(
    vertices: np.ndarray,
    body_vertices: np.ndarray,
    boundary_vertices: np.ndarray,
    *,
    base_offset: float,
) -> np.ndarray:
    y_min, _, height = _body_vertical_metrics(body_vertices)
    y_ratio = (vertices[:, 1] - y_min) / height
    center_x = float(np.median(body_vertices[:, 0]))
    abs_x_ratio = np.abs(vertices[:, 0] - center_x) / height

    inflation = np.full(len(vertices), base_offset, dtype=np.float64)
    chest = (y_ratio >= 0.62) & (y_ratio <= 0.74)
    sleeves = (y_ratio >= 0.62) & (abs_x_ratio >= 0.17)
    armpit = (y_ratio >= 0.585) & (y_ratio <= 0.69) & (abs_x_ratio >= 0.145)
    hem = y_ratio <= 0.50

    inflation[chest] += 0.012
    inflation[sleeves] += 0.020
    inflation[armpit] += 0.026
    inflation[hem] += 0.006
    inflation[boundary_vertices] += 0.006
    return inflation


def _add_boundary_rim(
    vertices: np.ndarray,
    faces: np.ndarray,
    normals: np.ndarray,
    boundary_edges: np.ndarray,
    *,
    rim_offset: float = 0.007,
) -> tuple[np.ndarray, np.ndarray]:
    if len(boundary_edges) == 0:
        return vertices, faces

    boundary_vertices = np.unique(boundary_edges.reshape(-1))
    rim_index_by_vertex: dict[int, int] = {}
    rim_vertices = []
    for vertex_index in boundary_vertices:
        rim_index_by_vertex[int(vertex_index)] = len(vertices) + len(rim_vertices)
        rim_vertices.append(vertices[vertex_index] + (normals[vertex_index] * rim_offset))

    rim_faces = []
    for start, end in boundary_edges:
        start = int(start)
        end = int(end)
        raised_start = rim_index_by_vertex[start]
        raised_end = rim_index_by_vertex[end]
        rim_faces.append((start, end, raised_end))
        rim_faces.append((start, raised_end, raised_start))

    return (
        np.vstack((vertices, np.asarray(rim_vertices, dtype=np.float64))),
        np.vstack((faces, np.asarray(rim_faces, dtype=np.int32))),
    )


def _estimate_vertex_normals(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    normals = np.zeros_like(vertices, dtype=np.float64)
    triangles = vertices[faces]
    face_normals = np.cross(
        triangles[:, 1] - triangles[:, 0],
        triangles[:, 2] - triangles[:, 0],
    )

    for corner in range(3):
        np.add.at(normals, faces[:, corner], face_normals)

    magnitudes = np.linalg.norm(normals, axis=1)
    nonzero = magnitudes > 1e-12
    normals[nonzero] = normals[nonzero] / magnitudes[nonzero, None]
    return normals


def _body_vertical_metrics(vertices: np.ndarray) -> tuple[float, float, float]:
    y_min = float(vertices[:, 1].min())
    y_max = float(vertices[:, 1].max())
    return y_min, y_max, max(y_max - y_min, 1e-9)


def _iter_vertical_bands(
    lower: float,
    upper: float,
    count: int,
) -> list[tuple[float, float]]:
    edges = np.linspace(lower, upper, count + 1)
    return [(float(edges[index]), float(edges[index + 1])) for index in range(count)]


def _as_vertices(vertices) -> np.ndarray:
    array = np.asarray(vertices, dtype=np.float64)
    if array.ndim != 2 or array.shape[1] != 3:
        raise ValueError("vertices must be an Nx3 array")

    return array


def _as_faces(faces) -> np.ndarray:
    array = np.asarray(faces, dtype=np.int32)
    if array.ndim != 2 or array.shape[1] != 3:
        raise ValueError("faces must be an Mx3 array")

    return array
