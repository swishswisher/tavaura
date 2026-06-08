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

if str(AVATAR_PIPELINE_DIR) not in sys.path:
    sys.path.append(str(AVATAR_PIPELINE_DIR))

from archetypes.archetype_library import list_archetypes  # noqa: E402


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

    for archetype in list_archetypes():
        beta_tensor = torch.tensor([archetype.betas], dtype=torch.float32)
        output = model(betas=beta_tensor)
        vertices = output.vertices.detach().cpu().numpy().squeeze()
        output_path = OUTPUT_DIR / f"{archetype.name}.png"

        render_body(vertices, model.faces, str(output_path))
        print(f"archetype: {archetype.name}")
        print(f"description: {archetype.description}")
        print(f"betas: {archetype.betas}")
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
