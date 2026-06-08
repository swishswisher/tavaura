from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import torch


CURRENT_DIR = Path(__file__).resolve().parent
AVATAR_PIPELINE_DIR = CURRENT_DIR.parent
SMPLX_DIR = AVATAR_PIPELINE_DIR / "smplx"
SMPLX_RENDER_HELPER_PATH = SMPLX_DIR / "test_betas.py"
MODEL_PATH = SMPLX_DIR / "models"
OUTPUT_DIR = CURRENT_DIR / "output"
BODY_POSE_SIZE = 63
PROBE_VALUE = 0.5


def main() -> None:
    render_helper = _load_smplx_render_helper()
    smplx = render_helper.smplx
    render_body = render_helper.render_body

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model = smplx.create(
        str(MODEL_PATH),
        model_type="smplx",
        gender="female",
        use_face_contour=True,
        num_betas=10,
        ext="npz",
    )

    for pose_index in range(BODY_POSE_SIZE):
        _render_probe_variant(
            model=model,
            render_body=render_body,
            pose_index=pose_index,
            value=PROBE_VALUE,
            label="pos",
        )
        _render_probe_variant(
            model=model,
            render_body=render_body,
            pose_index=pose_index,
            value=-PROBE_VALUE,
            label="neg",
        )


def _render_probe_variant(
    *,
    model,
    render_body,
    pose_index: int,
    value: float,
    label: str,
) -> None:
    body_pose = [0.0] * BODY_POSE_SIZE
    body_pose[pose_index] = value
    output = model(body_pose=torch.tensor([body_pose], dtype=torch.float32))
    vertices = output.vertices.detach().cpu().numpy().squeeze()
    output_path = OUTPUT_DIR / f"pose_{pose_index:02d}_{label}.png"
    render_body(vertices, model.faces, str(output_path))

    print(f"index: {pose_index}")
    print(f"value: {value}")
    print(f"output: {output_path}")


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
