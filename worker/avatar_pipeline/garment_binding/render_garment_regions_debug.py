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
OUTPUT_DIR = CURRENT_DIR / "output" / "regions"
ARCHETYPE_NAMES = ("slim", "athletic", "curvy", "plus_size")
POSE_NAMES = ("t_pose", "relaxed", "slight_walk")

REGION_COLORS = {
    "TORSO_FRONT": (42, 111, 219, 255),
    "TORSO_BACK": (72, 145, 235, 255),
    "LEFT_SLEEVE": (224, 54, 76, 255),
    "RIGHT_SLEEVE": (68, 170, 84, 255),
    "LEFT_ARMHOLE": (238, 201, 61, 255),
    "RIGHT_ARMHOLE": (238, 176, 61, 255),
    "COLLAR": (211, 71, 211, 255),
    "HEM": (50, 196, 216, 255),
}
REGION_PRIORITY = (
    "COLLAR",
    "LEFT_ARMHOLE",
    "RIGHT_ARMHOLE",
    "HEM",
    "LEFT_SLEEVE",
    "RIGHT_SLEEVE",
    "TORSO_FRONT",
    "TORSO_BACK",
)

if str(AVATAR_PIPELINE_DIR) not in sys.path:
    sys.path.append(str(AVATAR_PIPELINE_DIR))

from archetypes.archetype_library import get_archetype  # noqa: E402
from garment_binding.garment_proxy import GarmentProxyMesh, create_tshirt_proxy  # noqa: E402
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

    for pose_name in POSE_NAMES:
        pose = get_pose(pose_name)
        for archetype_name in ARCHETYPE_NAMES:
            archetype = get_archetype(archetype_name)
            output = model(
                betas=torch.tensor([archetype.betas], dtype=torch.float32),
                body_pose=torch.tensor([pose.body_pose], dtype=torch.float32),
            )
            vertices = output.vertices.detach().cpu().numpy().squeeze()
            garment = create_tshirt_proxy(vertices, model.faces)
            output_pose_name = "neutral" if pose.name == "t_pose" else pose.name
            output_path = OUTPUT_DIR / (
                f"{archetype.name}_tshirt_{output_pose_name}_regions.png"
            )

            render_region_debug(
                render_helper=render_helper,
                body_vertices=vertices,
                body_faces=model.faces,
                garment=garment,
                output_path=output_path,
            )
            print(f"archetype: {archetype.name}")
            print(f"pose: {pose.name}")
            print(f"regions: {_format_region_counts(garment.regions)}")
            print(f"output: {output_path}")


def render_region_debug(
    *,
    render_helper: ModuleType,
    body_vertices,
    body_faces,
    garment: GarmentProxyMesh,
    output_path: Path,
) -> None:
    trimesh = render_helper.trimesh
    pyrender = render_helper.pyrender

    body_mesh = trimesh.Trimesh(body_vertices, body_faces, process=False)
    garment_mesh = trimesh.Trimesh(garment.vertices, garment.faces, process=False)
    garment_mesh.visual.face_colors = _build_face_region_colors(
        garment.faces,
        garment.explicit_regions or garment.regions,
    )

    body_material = pyrender.MetallicRoughnessMaterial(
        baseColorFactor=[0.72, 0.69, 0.64, 1.0],
        metallicFactor=0.0,
        roughnessFactor=0.86,
    )

    scene = pyrender.Scene(bg_color=[1, 1, 1, 0])
    scene.add(pyrender.Mesh.from_trimesh(body_mesh, material=body_material, smooth=True))
    scene.add(pyrender.Mesh.from_trimesh(garment_mesh, smooth=False))

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


def _build_face_region_colors(
    faces: np.ndarray,
    regions: dict[str, list[int]],
) -> np.ndarray:
    vertex_regions = _build_vertex_region_lookup(regions)
    face_colors = np.zeros((len(faces), 4), dtype=np.uint8)
    for face_index, face in enumerate(faces):
        region_name = _classify_face_region(face, vertex_regions)
        face_colors[face_index] = REGION_COLORS[region_name]

    return face_colors


def _build_vertex_region_lookup(regions: dict[str, list[int]]) -> dict[int, str]:
    vertex_regions: dict[int, str] = {}
    for region_name in REGION_PRIORITY:
        for vertex_index in regions.get(region_name, []):
            vertex_regions.setdefault(int(vertex_index), region_name)

    return vertex_regions


def _classify_face_region(
    face: np.ndarray,
    vertex_regions: dict[int, str],
) -> str:
    region_counts = {region_name: 0 for region_name in REGION_PRIORITY}
    for vertex_index in face:
        region_name = vertex_regions.get(int(vertex_index), "TORSO_FRONT")
        region_counts[region_name] += 1

    for region_name in REGION_PRIORITY:
        if region_counts[region_name] > 0:
            return region_name

    return "TORSO_FRONT"


def _format_region_counts(regions: dict[str, list[int]]) -> str:
    return ", ".join(
        f"{region_name}={len(regions.get(region_name, []))}"
        for region_name in REGION_PRIORITY
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
