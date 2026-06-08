from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import torch


CURRENT_DIR = Path(__file__).resolve().parent
AVATAR_PIPELINE_DIR = CURRENT_DIR.parent
SMPLX_DIR = AVATAR_PIPELINE_DIR / "smplx"
SMPLX_RENDER_HELPER_PATH = SMPLX_DIR / "test_betas.py"
MODEL_PATH = SMPLX_DIR / "models"
OUTPUT_DIR = CURRENT_DIR / "output" / "panel_topology"

if str(AVATAR_PIPELINE_DIR) not in sys.path:
    sys.path.append(str(AVATAR_PIPELINE_DIR))

from archetypes.archetype_library import get_archetype  # noqa: E402
from garment_binding.debug.common import (  # noqa: E402
    DebugMeshState,
    render_seam_edges,
    render_stage_mesh,
    topology_metrics,
    write_json,
)
from garment_binding.garment_proxy import create_tshirt_proxy  # noqa: E402
from garment_binding.surface_fit import fit_garment_to_body  # noqa: E402
from poses.pose_library import get_pose  # noqa: E402


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    render_helper = _load_smplx_render_helper()
    smplx = render_helper.smplx
    model = smplx.create(
        str(MODEL_PATH),
        model_type="smplx",
        gender="female",
        use_face_contour=True,
        num_betas=10,
        ext="npz",
    )
    archetype = get_archetype("slim")
    pose = get_pose("t_pose")
    output = model(
        betas=torch.tensor([archetype.betas], dtype=torch.float32),
        body_pose=torch.tensor([pose.body_pose], dtype=torch.float32),
    )
    body_vertices = output.vertices.detach().cpu().numpy().squeeze()
    body_joints = output.joints.detach().cpu().numpy().squeeze()
    garment = create_tshirt_proxy(body_vertices, model.faces)
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
    state = DebugMeshState(
        body_vertices=body_vertices,
        body_faces=model.faces,
        body_joints=body_joints,
        prefit_vertices=garment.vertices,
        fitted_vertices=fitted_vertices,
        garment_faces=garment.faces,
        regions=garment.regions,
        archetype_name="slim",
        pose_name="t_pose",
    )

    for source_name, vertices in (("pre_fit", garment.vertices), ("post_fit", fitted_vertices)):
        render_stage_mesh(
            state=state,
            garment_vertices=vertices,
            output_path=OUTPUT_DIR / f"{source_name}_front_wireframe.png",
            view="front",
            wireframe=True,
        )
        render_stage_mesh(
            state=state,
            garment_vertices=vertices,
            output_path=OUTPUT_DIR / f"{source_name}_side_wireframe.png",
            view="side",
            wireframe=True,
        )
        render_seam_edges(
            state=state,
            garment_vertices=vertices,
            output_path=OUTPUT_DIR / f"{source_name}_seams.png",
            view="front",
        )

    report = {
        "pre_fit": topology_metrics(garment.vertices, garment.faces),
        "post_fit": topology_metrics(fitted_vertices, garment.faces),
        "validation": {
            "connected_component_count_should_be": 1,
            "nonmanifold_edge_count_should_be": 0,
            "boundary_clusters_should_be": "neckline, hem, left cuff, right cuff",
        },
    }
    write_json(report, OUTPUT_DIR / "panel_topology_report.json")
    print(json.dumps(report, indent=2))
    print(f"panel topology debug: {OUTPUT_DIR}")


def _load_smplx_render_helper():
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
