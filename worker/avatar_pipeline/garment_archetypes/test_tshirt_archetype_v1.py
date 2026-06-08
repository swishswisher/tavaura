from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent))
    from tshirt_archetype_v1 import (  # type: ignore[import-not-found]
        OUTPUT_DIR,
        REGIONS,
        export_mesh,
        generate_tshirt_archetype_v1,
        render_archetype_views,
        validate_topology,
    )
else:
    from .tshirt_archetype_v1 import (
        OUTPUT_DIR,
        REGIONS,
        export_mesh,
        generate_tshirt_archetype_v1,
        render_archetype_views,
        validate_topology,
    )


def main() -> None:
    archetype = generate_tshirt_archetype_v1()
    report = validate_topology(archetype.mesh)

    _assert_mesh_generated(report)
    _assert_single_component(report)
    _assert_no_boundary_holes(report)
    _assert_no_non_manifold_edges(report)
    _assert_reasonable_counts(report)
    _assert_region_labels(archetype.regions)

    mesh_path = export_mesh(archetype, OUTPUT_DIR / "tshirt_archetype_v1.obj")
    render_paths = render_archetype_views(archetype, OUTPUT_DIR)

    print("T-shirt archetype v1 topology validation passed.")
    print(f"connected_components: {report.connected_components}")
    print(f"boundary_edges: {report.boundary_edges}")
    print(f"non_manifold_edges: {report.non_manifold_edges}")
    print(f"vertex_count: {report.vertex_count}")
    print(f"face_count: {report.face_count}")
    print(f"mesh: {mesh_path}")
    for view, path in render_paths.items():
        print(f"{view}: {path}")


def _assert_mesh_generated(report) -> None:
    assert report.vertex_count > 0, "Mesh must contain vertices."
    assert report.face_count > 0, "Mesh must contain faces."


def _assert_single_component(report) -> None:
    assert report.connected_components == 1, (
        "Expected a single connected mesh component, "
        f"got {report.connected_components}."
    )


def _assert_no_boundary_holes(report) -> None:
    assert report.boundary_edges == 0, (
        "Expected zero open boundary edges, "
        f"got {report.boundary_edges}."
    )


def _assert_no_non_manifold_edges(report) -> None:
    assert report.non_manifold_edges == 0, (
        "Expected zero non-manifold edges, "
        f"got {report.non_manifold_edges}."
    )


def _assert_reasonable_counts(report) -> None:
    assert 1_000 <= report.vertex_count <= 20_000, (
        "Unexpected vertex count for canonical T-shirt archetype: "
        f"{report.vertex_count}."
    )
    assert 2_000 <= report.face_count <= 40_000, (
        "Unexpected face count for canonical T-shirt archetype: "
        f"{report.face_count}."
    )


def _assert_region_labels(regions: dict[str, list[int]]) -> None:
    missing = [region for region in REGIONS if len(regions.get(region, [])) == 0]
    assert not missing, f"Expected all garment regions to be represented: {missing}."


if __name__ == "__main__":
    main()
