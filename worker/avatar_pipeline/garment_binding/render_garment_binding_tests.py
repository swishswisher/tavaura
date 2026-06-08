from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import numpy as np
import torch
from PIL import Image, ImageDraw


CURRENT_DIR = Path(__file__).resolve().parent
AVATAR_PIPELINE_DIR = CURRENT_DIR.parent
SMPLX_DIR = AVATAR_PIPELINE_DIR / "smplx"
SMPLX_RENDER_HELPER_PATH = SMPLX_DIR / "test_betas.py"
MODEL_PATH = SMPLX_DIR / "models"
OUTPUT_DIR = CURRENT_DIR / "output"
FITTED_OUTPUT_DIR = OUTPUT_DIR / "fitted"
ARCHETYPE_NAMES = ("slim", "athletic", "curvy", "plus_size")
POSE_NAMES = ("t_pose", "relaxed", "slight_walk")

if str(AVATAR_PIPELINE_DIR) not in sys.path:
    sys.path.append(str(AVATAR_PIPELINE_DIR))

from archetypes.archetype_library import get_archetype  # noqa: E402
from garment_binding.body_derived_tshirt import (  # noqa: E402
    compute_shirt_body_distance_stats,
    create_body_derived_tshirt,
)
from garment_binding.surface_fit import fit_garment_to_body  # noqa: E402
from poses.pose_library import get_pose  # noqa: E402


def main() -> None:
    render_helper = _load_smplx_render_helper()
    smplx = render_helper.smplx

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FITTED_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model = smplx.create(
        str(MODEL_PATH),
        model_type="smplx",
        gender="female",
        use_face_contour=True,
        num_betas=10,
        ext="npz",
    )

    for pose_name in POSE_NAMES:
        pose = get_pose(pose_name)
        for archetype_name in ARCHETYPE_NAMES:
            archetype = get_archetype(archetype_name)
            output = model(
                betas=torch.tensor([archetype.betas], dtype=torch.float32),
                body_pose=torch.tensor([pose.body_pose], dtype=torch.float32),
            )
            vertices = output.vertices.detach().cpu().numpy().squeeze()
            joints = output.joints.detach().cpu().numpy().squeeze()
            garment = create_body_derived_tshirt(vertices, model.faces, body_joints=joints)
            prefit_vertices = garment.vertices.copy()
            fitted_vertices = fit_garment_to_body(
                garment.vertices,
                garment.regions,
                vertices,
                model.faces,
                garment_faces=garment.faces,
                body_joints=joints,
                garment_region_labels=garment.region_labels,
                garment_curves=garment.curves,
            )
            output_pose_name = "neutral" if pose.name == "t_pose" else pose.name
            output_path = OUTPUT_DIR / f"{archetype.name}_tshirt_{output_pose_name}.png"

            render_body_with_tshirt(
                render_helper=render_helper,
                body_vertices=vertices,
                body_faces=model.faces,
                garment_vertices=fitted_vertices,
                garment_faces=garment.faces,
                output_path=output_path,
            )
            if pose.name == "t_pose":
                render_fitting_debug_outputs(
                    render_helper=render_helper,
                    archetype_name=archetype.name,
                    body_vertices=vertices,
                    body_faces=model.faces,
                    prefit_vertices=prefit_vertices,
                    fitted_vertices=fitted_vertices,
                    garment_faces=garment.faces,
                    metadata=garment.metadata,
                )

            print(f"archetype: {archetype.name}")
            print(f"pose: {pose.name}")
            print(f"garment vertices: {len(garment.vertices)}")
            print(f"garment faces: {len(garment.faces)}")
            print_body_derived_diagnostics(garment.metadata, fitted_vertices, vertices)
            print(f"output: {output_path}")

    build_fitted_comparison()


def render_fitting_debug_outputs(
    *,
    render_helper: ModuleType,
    archetype_name: str,
    body_vertices,
    body_faces,
    prefit_vertices,
    fitted_vertices,
    garment_faces,
    metadata: dict,
) -> None:
    fitted_path = FITTED_OUTPUT_DIR / f"{archetype_name}_tshirt_fitted.png"
    wireframe_path = FITTED_OUTPUT_DIR / f"{archetype_name}_tshirt_wireframe.png"
    render_body_only(
        render_helper=render_helper,
        body_vertices=body_vertices,
        body_faces=body_faces,
        output_path=FITTED_OUTPUT_DIR / f"{archetype_name}_body.png",
    )
    render_body_with_tshirt(
        render_helper=render_helper,
        body_vertices=body_vertices,
        body_faces=body_faces,
        garment_vertices=prefit_vertices,
        garment_faces=garment_faces,
        output_path=FITTED_OUTPUT_DIR / f"{archetype_name}_tshirt_prefit.png",
    )
    render_body_with_tshirt(
        render_helper=render_helper,
        body_vertices=body_vertices,
        body_faces=body_faces,
        garment_vertices=fitted_vertices,
        garment_faces=garment_faces,
        output_path=fitted_path,
    )
    render_body_with_tshirt(
        render_helper=render_helper,
        body_vertices=body_vertices,
        body_faces=body_faces,
        garment_vertices=fitted_vertices,
        garment_faces=garment_faces,
        output_path=wireframe_path,
        wireframe=True,
    )
    render_body_with_tshirt(
        render_helper=render_helper,
        body_vertices=_rotate_y(body_vertices, -90.0),
        body_faces=body_faces,
        garment_vertices=_rotate_y(fitted_vertices, -90.0),
        garment_faces=garment_faces,
        output_path=FITTED_OUTPUT_DIR / f"{archetype_name}_tshirt_side.png",
    )
    save_detail_crop(
        source_path=fitted_path,
        output_path=FITTED_OUTPUT_DIR / f"{archetype_name}_tshirt_neckline_closeup.png",
        box=(0.22, 0.38, 0.78, 0.66),
    )
    save_detail_crop(
        source_path=fitted_path,
        output_path=FITTED_OUTPUT_DIR / f"{archetype_name}_tshirt_sleeve_closeup.png",
        box=(0.02, 0.24, 0.46, 0.58),
    )
    save_detail_crop(
        source_path=fitted_path,
        output_path=FITTED_OUTPUT_DIR / f"{archetype_name}_tshirt_underarm_closeup.png",
        box=(0.02, 0.34, 0.42, 0.60),
    )
    save_detail_crop(
        source_path=wireframe_path,
        output_path=FITTED_OUTPUT_DIR / f"{archetype_name}_tshirt_sleeve_seam_closeup.png",
        box=(0.02, 0.31, 0.48, 0.59),
    )
    save_manifold_debug_render(
        source_path=wireframe_path,
        output_path=FITTED_OUTPUT_DIR / f"{archetype_name}_tshirt_manifold_debug.png",
        topology=metadata.get("topology", {}),
    )


def save_detail_crop(
    *,
    source_path: Path,
    output_path: Path,
    box: tuple[float, float, float, float],
) -> None:
    with Image.open(source_path).convert("RGB") as image:
        width, height = image.size
        crop_box = (
            int(width * box[0]),
            int(height * box[1]),
            int(width * box[2]),
            int(height * box[3]),
        )
        crop = image.crop(crop_box)
        crop = crop.resize((512, 512), Image.Resampling.LANCZOS)
        crop.save(output_path)


def save_manifold_debug_render(
    *,
    source_path: Path,
    output_path: Path,
    topology: dict,
) -> None:
    with Image.open(source_path).convert("RGB") as image:
        draw = ImageDraw.Draw(image)
        lines = [
            f"islands: {topology.get('disconnected_mesh_islands', 'n/a')}",
            f"boundary edges: {topology.get('boundary_edge_count', 'n/a')}",
            f"nonmanifold edges: {topology.get('nonmanifold_edge_count', 'n/a')}",
            f"holes: {topology.get('hole_count', 'n/a')}",
            f"seams ok: {topology.get('seam_continuity_valid', 'n/a')}",
        ]
        margin = 18
        line_height = 22
        panel_width = 250
        panel_height = (len(lines) * line_height) + (margin * 2)
        draw.rectangle(
            (12, 12, 12 + panel_width, 12 + panel_height),
            fill=(0, 0, 0),
            outline=(60, 180, 255),
            width=2,
        )
        for index, line in enumerate(lines):
            draw.text(
                (12 + margin, 12 + margin + (index * line_height)),
                line,
                fill=(255, 255, 255),
            )
        image.save(output_path)


def print_body_derived_diagnostics(
    metadata: dict,
    fitted_vertices,
    body_vertices,
) -> None:
    fitted_distances = compute_shirt_body_distance_stats(fitted_vertices, body_vertices)
    print(f"torso vertices used: {metadata.get('torso_vertex_count', 0)}")
    print(f"sleeve vertices used: {metadata.get('sleeve_vertex_count', 0)}")
    print(f"collar vertex count: {metadata.get('collar_vertex_count', 0)}")
    print(f"left armhole vertex count: {metadata.get('left_armhole_vertex_count', 0)}")
    print(f"right armhole vertex count: {metadata.get('right_armhole_vertex_count', 0)}")
    print(f"left sleeve ring vertex count: {metadata.get('left_sleeve_ring_vertex_count', 0)}")
    print(f"right sleeve ring vertex count: {metadata.get('right_sleeve_ring_vertex_count', 0)}")
    print(f"hem vertex count: {metadata.get('hem_vertex_count', 0)}")
    print(f"collar landmarks: {metadata.get('collar_landmarks', {})}")
    print(f"hem landmarks: {metadata.get('hem_landmarks', {})}")
    print(
        "raw shirt-body distance: "
        f"avg={metadata.get('average_shirt_body_distance', 0.0):.5f}, "
        f"max={metadata.get('max_shirt_body_distance', 0.0):.5f}"
    )
    print(
        "fitted shirt-body distance: "
        f"avg={fitted_distances['average']:.5f}, "
        f"max={fitted_distances['max']:.5f}"
    )
    if metadata.get("sleeve_height_warning", False):
        print(
            "warning: sleeve vertices exceed shoulder tolerance "
            f"(max_y={metadata.get('sleeve_max_y', 0.0):.5f}, "
            f"limit={metadata.get('sleeve_height_limit', 0.0):.5f})"
        )
    topology = metadata.get("topology", {})
    print(f"disconnected mesh islands: {topology.get('disconnected_mesh_islands', 0)}")
    print(f"boundary edge count: {topology.get('boundary_edge_count', 0)}")
    print(f"non-manifold edge count: {topology.get('nonmanifold_edge_count', 0)}")
    print(f"hole count: {topology.get('hole_count', 0)}")
    print(f"boundary component vertex counts: {topology.get('boundary_component_vertex_counts', [])}")
    print(f"seam continuity valid: {topology.get('seam_continuity_valid', False)}")


def render_body_only(
    *,
    render_helper: ModuleType,
    body_vertices,
    body_faces,
    output_path: Path,
) -> None:
    trimesh = render_helper.trimesh
    pyrender = render_helper.pyrender

    body_mesh = trimesh.Trimesh(body_vertices, body_faces, process=False)
    body_material = pyrender.MetallicRoughnessMaterial(
        baseColorFactor=[0.74, 0.70, 0.65, 1.0],
        metallicFactor=0.0,
        roughnessFactor=0.82,
    )

    scene = pyrender.Scene(bg_color=[1, 1, 1, 0])
    scene.add(pyrender.Mesh.from_trimesh(body_mesh, material=body_material, smooth=True))

    camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)
    camera_pose = _camera_pose()
    scene.add(camera, pose=camera_pose)
    scene.add(
        pyrender.DirectionalLight(color=np.ones(3), intensity=3.0),
        pose=camera_pose,
    )

    renderer = pyrender.OffscreenRenderer(viewport_width=512, viewport_height=1024)
    color, _ = renderer.render(scene)
    renderer.delete()
    Image.fromarray(color).save(output_path)


def render_body_with_tshirt(
    *,
    render_helper: ModuleType,
    body_vertices,
    body_faces,
    garment_vertices,
    garment_faces,
    output_path: Path,
    wireframe: bool = False,
) -> None:
    trimesh = render_helper.trimesh
    pyrender = render_helper.pyrender

    body_mesh = trimesh.Trimesh(body_vertices, body_faces, process=False)
    garment_mesh = trimesh.Trimesh(garment_vertices, garment_faces, process=False)
    body_material = pyrender.MetallicRoughnessMaterial(
        baseColorFactor=[0.74, 0.70, 0.65, 1.0],
        metallicFactor=0.0,
        roughnessFactor=0.82,
    )
    garment_material = pyrender.MetallicRoughnessMaterial(
        baseColorFactor=[0.02, 0.02, 0.02, 1.0] if wireframe else [0.08, 0.32, 0.58, 1.0],
        metallicFactor=0.0,
        roughnessFactor=0.78 if wireframe else 0.70,
    )

    scene = pyrender.Scene(bg_color=[1, 1, 1, 0])
    scene.add(pyrender.Mesh.from_trimesh(body_mesh, material=body_material, smooth=True))
    scene.add(_make_render_mesh(pyrender, garment_mesh, garment_material, wireframe=wireframe))

    camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)
    camera_pose = _camera_pose()
    scene.add(camera, pose=camera_pose)
    scene.add(
        pyrender.DirectionalLight(color=np.ones(3), intensity=3.0),
        pose=camera_pose,
    )

    renderer = pyrender.OffscreenRenderer(viewport_width=512, viewport_height=1024)
    color, _ = renderer.render(scene)
    renderer.delete()
    Image.fromarray(color).save(output_path)


def build_fitted_comparison() -> None:
    image_groups = []
    for archetype_name in ARCHETYPE_NAMES:
        image_groups.append(
            (
                archetype_name,
                FITTED_OUTPUT_DIR / f"{archetype_name}_body.png",
                FITTED_OUTPUT_DIR / f"{archetype_name}_tshirt_prefit.png",
                FITTED_OUTPUT_DIR / f"{archetype_name}_tshirt_fitted.png",
                FITTED_OUTPUT_DIR / f"{archetype_name}_tshirt_wireframe.png",
                FITTED_OUTPUT_DIR / f"{archetype_name}_tshirt_side.png",
                FITTED_OUTPUT_DIR / f"{archetype_name}_tshirt_neckline_closeup.png",
                FITTED_OUTPUT_DIR / f"{archetype_name}_tshirt_sleeve_closeup.png",
                FITTED_OUTPUT_DIR / f"{archetype_name}_tshirt_underarm_closeup.png",
                FITTED_OUTPUT_DIR / f"{archetype_name}_tshirt_sleeve_seam_closeup.png",
                FITTED_OUTPUT_DIR / f"{archetype_name}_tshirt_manifold_debug.png",
            )
        )

    existing_groups = [
        group for group in image_groups if all(path.exists() for path in group[1:])
    ]
    if not existing_groups:
        return

    cell_width = 300
    cell_height = 560
    label_height = 44
    gap = 18
    columns = (
        "body",
        "raw",
        "fitted",
        "wireframe",
        "side",
        "neckline",
        "sleeve",
        "underarm",
        "seam",
        "manifold",
    )
    canvas_width = (len(columns) * cell_width) + ((len(columns) + 1) * gap)
    canvas_height = (
        (len(existing_groups) * (cell_height + label_height))
        + ((len(existing_groups) + 1) * gap)
    )
    canvas = Image.new("RGB", (canvas_width, canvas_height), "#f6f3ee")
    draw = ImageDraw.Draw(canvas)

    for row, group in enumerate(existing_groups):
        archetype_name = group[0]
        y = gap + (row * (cell_height + label_height + gap))
        for column, path in enumerate(group[1:]):
            x = gap + (column * (cell_width + gap))
            image = Image.open(path).convert("RGB")
            image.thumbnail((cell_width, cell_height), Image.Resampling.LANCZOS)
            image_x = x + ((cell_width - image.width) // 2)
            image_y = y + ((cell_height - image.height) // 2)
            canvas.paste(image, (image_x, image_y))
            label = f"{archetype_name} {columns[column]}"
            draw.text((x + 8, y + cell_height + 12), label, fill="#2d2823")

    canvas.save(FITTED_OUTPUT_DIR / "fitted_comparison.png")


def _make_render_mesh(
    pyrender,
    garment_mesh,
    garment_material,
    *,
    wireframe: bool,
):
    try:
        return pyrender.Mesh.from_trimesh(
            garment_mesh,
            material=garment_material,
            smooth=not wireframe,
            wireframe=wireframe,
        )
    except TypeError:
        return pyrender.Mesh.from_trimesh(
            garment_mesh,
            material=garment_material,
            smooth=not wireframe,
        )


def _camera_pose() -> np.ndarray:
    return np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.15],
            [0.0, 0.0, 1.0, 3.8],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )


def _rotate_y(vertices, angle_degrees: float):
    array = np.asarray(vertices, dtype=np.float64)
    center = array.mean(axis=0)
    angle = np.deg2rad(angle_degrees)
    rotation = np.array(
        [
            [np.cos(angle), 0.0, np.sin(angle)],
            [0.0, 1.0, 0.0],
            [-np.sin(angle), 0.0, np.cos(angle)],
        ],
        dtype=np.float64,
    )
    return ((array - center) @ rotation.T) + center


def _load_smplx_render_helper() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "tavaura_smplx_test_betas",
        SMPLX_RENDER_HELPER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load SMPL-X render helper: {SMPLX_RENDER_HELPER_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    main()
