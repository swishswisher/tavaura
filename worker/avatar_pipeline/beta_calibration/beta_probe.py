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
BETA_COUNT = 10
PROBE_VALUE = 3.0

if str(AVATAR_PIPELINE_DIR) not in sys.path:
    sys.path.append(str(AVATAR_PIPELINE_DIR))

from beta_calibration.mesh_measurements import (  # noqa: E402
    measure_height,
    measure_hip_width,
    measure_leg_length,
    measure_shoulder_width,
    measure_waist_width,
)


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
        num_betas=BETA_COUNT,
        ext="npz",
    )

    neutral_vertices = _generate_vertices(model, [0.0] * BETA_COUNT)
    neutral_output = OUTPUT_DIR / "neutral.png"
    render_body(neutral_vertices, model.faces, str(neutral_output))
    neutral_measurements = _measure_vertices(neutral_vertices)

    print("neutral")
    _print_measurements(neutral_measurements)
    print(f"output: {neutral_output}")

    for beta_index in range(BETA_COUNT):
        print(f"\nbeta_{beta_index}")
        _render_probe_variant(
            model=model,
            render_body=render_body,
            beta_index=beta_index,
            beta_value=PROBE_VALUE,
            label="positive",
        )
        _render_probe_variant(
            model=model,
            render_body=render_body,
            beta_index=beta_index,
            beta_value=-PROBE_VALUE,
            label="negative",
        )


def _render_probe_variant(
    *,
    model,
    render_body,
    beta_index: int,
    beta_value: float,
    label: str,
) -> None:
    betas = [0.0] * BETA_COUNT
    betas[beta_index] = beta_value
    vertices = _generate_vertices(model, betas)
    output_path = OUTPUT_DIR / f"beta_{beta_index}_{label}.png"
    render_body(vertices, model.faces, str(output_path))

    print(f"{label}: beta[{beta_index}]={beta_value}")
    _print_measurements(_measure_vertices(vertices))
    print(f"output: {output_path}")


def _generate_vertices(model, betas: list[float]):
    beta_tensor = torch.tensor([betas], dtype=torch.float32)
    output = model(betas=beta_tensor)
    return output.vertices.detach().cpu().numpy().squeeze()


def _measure_vertices(vertices) -> dict[str, float]:
    return {
        "height": measure_height(vertices),
        "shoulder_width": measure_shoulder_width(vertices),
        "waist_width": measure_waist_width(vertices),
        "hip_width": measure_hip_width(vertices),
        "leg_length": measure_leg_length(vertices),
    }


def _print_measurements(measurements: dict[str, float]) -> None:
    print(
        "measurements: "
        f"height={measurements['height']}, "
        f"shoulder_width={measurements['shoulder_width']}, "
        f"waist_width={measurements['waist_width']}, "
        f"hip_width={measurements['hip_width']}, "
        f"leg_length={measurements['leg_length']}"
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
