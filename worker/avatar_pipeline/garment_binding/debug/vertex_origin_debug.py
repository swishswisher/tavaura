from __future__ import annotations

import sys
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
AVATAR_PIPELINE_DIR = CURRENT_DIR.parents[1]
if str(AVATAR_PIPELINE_DIR) not in sys.path:
    sys.path.append(str(AVATAR_PIPELINE_DIR))

from garment_binding.debug.common import (  # noqa: E402
    OUTPUT_DIR,
    build_debug_mesh_state,
    render_vertex_origins,
)


def main() -> None:
    state = build_debug_mesh_state()
    output_dir = OUTPUT_DIR / "vertex_origins"
    render_vertex_origins(
        state=state,
        garment_vertices=state.prefit_vertices,
        output_path=output_dir / "pre_fit_vertex_origins.png",
        view="front",
    )
    render_vertex_origins(
        state=state,
        garment_vertices=state.prefit_vertices,
        output_path=output_dir / "pre_fit_vertex_origins_side.png",
        view="side",
    )
    render_vertex_origins(
        state=state,
        garment_vertices=state.fitted_vertices,
        output_path=output_dir / "post_fit_vertex_origins.png",
        view="front",
    )
    render_vertex_origins(
        state=state,
        garment_vertices=state.fitted_vertices,
        output_path=output_dir / "post_fit_vertex_origins_side.png",
        view="side",
    )
    print(f"vertex origin diagnostics: {output_dir}")


if __name__ == "__main__":
    main()

