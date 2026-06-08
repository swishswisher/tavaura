from __future__ import annotations

import sys
from pathlib import Path

import torch


CURRENT_DIR = Path(__file__).resolve().parent
AVATAR_PIPELINE_DIR = CURRENT_DIR.parent
OUTPUT_DIR = CURRENT_DIR / "output_amplified"

if str(AVATAR_PIPELINE_DIR) not in sys.path:
    sys.path.append(str(AVATAR_PIPELINE_DIR))
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from body_estimation.beta_mapper import estimate_betas_from_profile  # noqa: E402
from body_estimation.morph_amplifier import (  # noqa: E402
    amplify_betas,
    describe_amplification,
)
from render_profiles import (  # noqa: E402
    MODEL_PATH,
    PROFILE_PRESETS,
    _load_smplx_render_helper,
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
        num_betas=10,
        ext="npz",
    )

    for profile_name, profile in PROFILE_PRESETS.items():
        estimated_betas = estimate_betas_from_profile(profile)
        amplified_betas = amplify_betas(estimated_betas, profile)
        beta_tensor = torch.tensor([amplified_betas], dtype=torch.float32)
        output = model(betas=beta_tensor)
        vertices = output.vertices.detach().cpu().numpy().squeeze()
        output_path = OUTPUT_DIR / f"{profile_name}.png"

        render_body(vertices, model.faces, str(output_path))
        print(f"profile: {profile_name}")
        print(f"estimated betas: {estimated_betas}")
        print(f"amplified betas: {amplified_betas}")
        print(f"amplification: {describe_amplification(profile)}")
        print(f"output: {output_path}")


if __name__ == "__main__":
    main()
