from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import numpy as np
import torch
from PIL import Image


CURRENT_DIR = Path(__file__).resolve().parent
AVATAR_PIPELINE_DIR = CURRENT_DIR.parent
SMPLX_DIR = AVATAR_PIPELINE_DIR / "smplx"
SMPLX_RENDER_HELPER_PATH = SMPLX_DIR / "test_betas.py"
MODEL_PATH = SMPLX_DIR / "models"
OUTPUT_DIR = CURRENT_DIR / "output" / "archetypes"
ARCHETYPE_NAMES = ("slim", "athletic", "curvy", "plus_size")
DEBUG_CASES = (
    ("front", "t_pose", 0.0, False),
    ("side", "t_pose", -90.0, False),
    ("perspective", "t_pose", -28.0, False),
    ("wireframe", "t_pose", -20.0, True),
)

if str(AVATAR_PIPELINE_DIR) not in sys.path:
    sys.path.append(str(AVATAR_PIPELINE_DIR))

from archetypes.archetype_library import get_archetype  # noqa: E402
from garment_binding.garment_proxy import create_tshirt_proxy  # noqa: E402
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
        for case_name, pose_name, angle_degrees, wireframe in DEBUG_CASES:
            pose = get_pose(pose_name)
            output = model(
                betas=torch.tensor([archetype.betas], dtype=torch.float32),
                body_pose=torch.tensor([pose.body_pose], dtype=torch.float32),
            )
            body_vertices = output.vertices.detach().cpu().numpy().squeeze()
            garment = create_tshirt_proxy(body_vertices, model.faces)
            center = body_vertices.mean(axis=0)
            output_path = OUTPUT_DIR / f"{archetype.name}_tshirt_{case_name}.png"

            render_body_with_structured_tshirt(
                render_helper=render_helper,
                body_vertices=_rotate_y(body_vertices, angle_degrees, center),
                body_faces=model.faces,
                garment_vertices=_rotate_y(garment.vertices, angle_degrees, center),
                garment_faces=garment.faces,
                output_path=output_path,
                wireframe=wireframe,
            )
            print(f"archetype: {archetype.name}")
            print(f"case: {case_name}")
            print(f"pose: {pose.name}")
            print(f"angle: {angle_degrees}")
            print(f"regions: {_format_region_counts(garment.regions)}")
            print(f"output: {output_path}")


def render_body_with_structured_tshirt(
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
        roughnessFactor=0.84,
    )
    garment_material = pyrender.MetallicRoughnessMaterial(
        baseColorFactor=[0.02, 0.02, 0.02, 1.0] if wireframe else [0.075, 0.31, 0.58, 1.0],
        metallicFactor=0.0,
        roughnessFactor=0.78 if wireframe else 0.68,
    )

    scene = pyrender.Scene(bg_color=[1, 1, 1, 0])
    scene.add(pyrender.Mesh.from_trimesh(body_mesh, material=body_material, smooth=True))
    scene.add(_make_render_mesh(pyrender, garment_mesh, garment_material, wireframe=wireframe))

    camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)
    camera_pose = np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.15],
            [0.0, 0.0, 1.0, 3.8],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    scene.add(camera, pose=camera_pose)
    scene.add(
        pyrender.DirectionalLight(color=np.ones(3), intensity=3.0),
        pose=camera_pose,
    )

    renderer = pyrender.OffscreenRenderer(viewport_width=512, viewport_height=1024)
    color, _ = renderer.render(scene)
    renderer.delete()
    Image.fromarray(color).save(output_path)


def _rotate_y(
    vertices: np.ndarray,
    angle_degrees: float,
    center: np.ndarray,
) -> np.ndarray:
    if abs(angle_degrees) < 1e-9:
        return vertices

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


def _format_region_counts(regions: dict[str, list[int]]) -> str:
    return ", ".join(
        f"{region_name}={len(regions.get(region_name, []))}"
        for region_name in (
            "TORSO_FRONT",
            "TORSO_BACK",
            "LEFT_SLEEVE",
            "RIGHT_SLEEVE",
            "COLLAR",
            "LEFT_ARMHOLE",
            "RIGHT_ARMHOLE",
            "HEM",
        )
    )


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
