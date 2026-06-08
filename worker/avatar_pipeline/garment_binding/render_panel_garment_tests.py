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
OUTPUT_DIR = CURRENT_DIR / "output" / "panel_garments"
ARCHETYPE_NAMES = ("slim", "athletic", "curvy", "plus_size")
POSE_NAMES = ("t_pose", "relaxed", "slight_walk")

if str(AVATAR_PIPELINE_DIR) not in sys.path:
    sys.path.append(str(AVATAR_PIPELINE_DIR))

from archetypes.archetype_library import get_archetype  # noqa: E402
from garment_binding.debug.common import DebugMeshState, render_seam_edges  # noqa: E402
from garment_binding.garment_proxy import create_tshirt_proxy  # noqa: E402
from garment_binding.panels import generate_panel_tshirt  # noqa: E402
from garment_binding.surface_fit import fit_garment_to_body  # noqa: E402
from poses.pose_library import get_pose  # noqa: E402


def main() -> None:
    render_helper = _load_smplx_render_helper()
    smplx = render_helper.smplx
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model = smplx.create(
        str(MODEL_PATH),
        model_type="smplx",
        gender="female",
        use_face_contour=True,
        num_betas=10,
        ext="npz",
    )

    for archetype_name in ARCHETYPE_NAMES:
        archetype = get_archetype(archetype_name)
        for pose_name in POSE_NAMES:
            pose = get_pose(pose_name)
            output = model(
                betas=torch.tensor([archetype.betas], dtype=torch.float32),
                body_pose=torch.tensor([pose.body_pose], dtype=torch.float32),
            )
            body_vertices = output.vertices.detach().cpu().numpy().squeeze()
            body_joints = output.joints.detach().cpu().numpy().squeeze()
            garment = create_tshirt_proxy(body_vertices, model.faces)
            panel_mesh = generate_panel_tshirt(body_vertices, model.faces)
            fitted_vertices = fit_garment_to_body(
                garment.vertices,
                garment.regions,
                body_vertices,
                model.faces,
                garment_faces=garment.faces,
                body_joints=body_joints,
                garment_region_labels=garment.region_labels,
                garment_curves=garment.curves,
            )
            case_name = f"{archetype_name}_{'neutral' if pose_name == 't_pose' else pose_name}"
            debug_state = DebugMeshState(
                body_vertices=body_vertices,
                body_faces=model.faces,
                body_joints=body_joints,
                prefit_vertices=garment.vertices,
                fitted_vertices=fitted_vertices,
                garment_faces=garment.faces,
                regions=garment.regions,
                archetype_name=archetype_name,
                pose_name=pose_name,
            )
            render_body_only(
                render_helper=render_helper,
                body_vertices=body_vertices,
                body_faces=model.faces,
                output_path=OUTPUT_DIR / f"{case_name}_body.png",
            )
            render_panel_curves(
                render_helper=render_helper,
                body_vertices=body_vertices,
                body_faces=model.faces,
                panel_vertices=panel_mesh.vertices,
                panel_curves=panel_mesh.curves,
                output_path=OUTPUT_DIR / f"{case_name}_panel_curves.png",
            )
            render_body_with_panel_garment(
                render_helper=render_helper,
                body_vertices=body_vertices,
                body_faces=model.faces,
                garment_vertices=garment.vertices,
                garment_faces=garment.faces,
                output_path=OUTPUT_DIR / f"{case_name}_prefit.png",
            )
            render_body_with_panel_garment(
                render_helper=render_helper,
                body_vertices=body_vertices,
                body_faces=model.faces,
                garment_vertices=garment.vertices,
                garment_faces=garment.faces,
                output_path=OUTPUT_DIR / f"{case_name}_prefit_wireframe.png",
                wireframe=True,
            )
            render_body_with_panel_garment(
                render_helper=render_helper,
                body_vertices=body_vertices,
                body_faces=model.faces,
                garment_vertices=fitted_vertices,
                garment_faces=garment.faces,
                output_path=OUTPUT_DIR / f"{case_name}_fitted.png",
            )
            render_body_with_panel_garment(
                render_helper=render_helper,
                body_vertices=body_vertices,
                body_faces=model.faces,
                garment_vertices=fitted_vertices,
                garment_faces=garment.faces,
                output_path=OUTPUT_DIR / f"{case_name}_wireframe.png",
                wireframe=True,
            )
            render_body_with_panel_garment(
                render_helper=render_helper,
                body_vertices=body_vertices,
                body_faces=model.faces,
                garment_vertices=fitted_vertices,
                garment_faces=garment.faces,
                output_path=OUTPUT_DIR / f"{case_name}_postfit_wireframe.png",
                wireframe=True,
            )
            render_body_with_panel_garment(
                render_helper=render_helper,
                body_vertices=_rotate_y(body_vertices, -90.0),
                body_faces=model.faces,
                garment_vertices=_rotate_y(fitted_vertices, -90.0),
                garment_faces=garment.faces,
                output_path=OUTPUT_DIR / f"{case_name}_side.png",
            )
            render_seam_edges(
                state=debug_state,
                garment_vertices=fitted_vertices,
                output_path=OUTPUT_DIR / f"{case_name}_seams.png",
                view="front",
            )
            print(f"panel garment: {case_name}")
            print(f"vertices: {len(garment.vertices)}")
            print(f"faces: {len(garment.faces)}")


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
    scene = pyrender.Scene(bg_color=[1, 1, 1, 0])
    scene.add(
        pyrender.Mesh.from_trimesh(
            body_mesh,
            material=_body_material(pyrender),
            smooth=True,
        )
    )
    _render_scene(pyrender, scene, output_path)


def render_body_with_panel_garment(
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
    scene = pyrender.Scene(bg_color=[1, 1, 1, 0])
    scene.add(pyrender.Mesh.from_trimesh(body_mesh, material=_body_material(pyrender), smooth=True))
    scene.add(
        _make_render_mesh(
            pyrender,
            garment_mesh,
            _garment_material(pyrender, wireframe=wireframe),
            wireframe=wireframe,
        )
    )
    _render_scene(pyrender, scene, output_path)


def render_panel_curves(
    *,
    render_helper: ModuleType,
    body_vertices,
    body_faces,
    panel_vertices,
    panel_curves: dict[str, list[int]],
    output_path: Path,
) -> None:
    render_body_only(
        render_helper=render_helper,
        body_vertices=body_vertices,
        body_faces=body_faces,
        output_path=output_path,
    )
    image = Image.open(output_path).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    projector = _make_front_projector(np.vstack((body_vertices, panel_vertices)))
    colors = {
        "neckline_loop": (255, 80, 120, 255),
        "hem_loop": (70, 220, 255, 255),
        "left_armhole_loop": (255, 200, 70, 255),
        "right_armhole_loop": (255, 200, 70, 255),
        "left_sleeve_cuff_loop": (120, 255, 110, 255),
        "right_sleeve_cuff_loop": (120, 255, 110, 255),
        "left_side_seam": (190, 125, 255, 255),
        "right_side_seam": (190, 125, 255, 255),
    }
    for curve_name, color in colors.items():
        indices = panel_curves.get(curve_name, [])
        if len(indices) < 2:
            continue

        points = projector(panel_vertices[np.asarray(indices, dtype=np.int32)])
        for start_index in range(len(points)):
            end_index = (start_index + 1) % len(points)
            if "side_seam" in curve_name and end_index == 0:
                continue

            draw.line(
                [tuple(points[start_index]), tuple(points[end_index])],
                fill=color,
                width=4,
            )

    image.convert("RGB").save(output_path)


def _body_material(pyrender):
    return pyrender.MetallicRoughnessMaterial(
        baseColorFactor=[0.74, 0.70, 0.65, 1.0],
        metallicFactor=0.0,
        roughnessFactor=0.82,
    )


def _garment_material(pyrender, *, wireframe: bool):
    return pyrender.MetallicRoughnessMaterial(
        baseColorFactor=[0.02, 0.02, 0.02, 1.0] if wireframe else [0.07, 0.32, 0.60, 1.0],
        metallicFactor=0.0,
        roughnessFactor=0.78 if wireframe else 0.70,
    )


def _render_scene(pyrender, scene, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)
    camera_pose = np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.15],
            [0.0, 0.0, 1.0, 3.8],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    scene.add(camera, pose=camera_pose)
    scene.add(pyrender.DirectionalLight(color=np.ones(3), intensity=3.0), pose=camera_pose)
    renderer = pyrender.OffscreenRenderer(viewport_width=512, viewport_height=1024)
    color, _ = renderer.render(scene)
    renderer.delete()
    Image.fromarray(color).save(output_path)


def _make_render_mesh(pyrender, garment_mesh, garment_material, *, wireframe: bool):
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


def _rotate_y(vertices: np.ndarray, angle_degrees: float) -> np.ndarray:
    center = vertices.mean(axis=0)
    angle = np.deg2rad(angle_degrees)
    rotation = np.array(
        [
            [np.cos(angle), 0.0, np.sin(angle)],
            [0.0, 1.0, 0.0],
            [-np.sin(angle), 0.0, np.cos(angle)],
        ],
        dtype=np.float64,
    )
    return ((vertices - center) @ rotation.T) + center


def _make_front_projector(vertices: np.ndarray):
    coords = vertices[:, [0, 1]]
    minimum = coords.min(axis=0)
    maximum = coords.max(axis=0)
    span = np.maximum(maximum - minimum, 1e-9)
    image_width = 512
    image_height = 1024
    margin = 70
    scale = min((image_width - (2 * margin)) / span[0], (image_height - (2 * margin)) / span[1])
    scaled = span * scale
    offset = minimum.copy()
    offset[0] -= (image_width - (2 * margin) - scaled[0]) / (2.0 * scale)
    offset[1] -= (image_height - (2 * margin) - scaled[1]) / (2.0 * scale)

    def project(points: np.ndarray) -> np.ndarray:
        projected = (points[:, [0, 1]] - offset) * scale
        projected[:, 0] += margin
        projected[:, 1] = image_height - margin - projected[:, 1]
        return projected

    return project


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
