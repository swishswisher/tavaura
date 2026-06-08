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
    export_obj,
    render_stage_mesh,
    topology_metrics,
    write_json,
)


STAGES = (
    ("raw_primitives", "prefit", "Current generator output before fitting."),
    ("after_welding", "prefit", "No separate welding stage is exposed; mirrors pre-fit mesh."),
    ("after_seam_bridging", "prefit", "Current seam-bridged mesh before fitting."),
    ("after_smoothing", "prefit", "No separate smoothing stage is exposed; mirrors pre-fit mesh."),
    ("after_remeshing", "prefit", "No remeshing stage is currently present; mirrors pre-fit mesh."),
    ("after_fitting", "fitted", "Mesh after surface_fit.fit_garment_to_body."),
    ("after_shrinkwrap", "fitted", "No separate shrinkwrap stage is exposed; mirrors fitted mesh."),
    ("final_output", "fitted", "Final garment mesh used by current binding tests."),
)


def main() -> None:
    state = build_debug_mesh_state()
    output_dir = OUTPUT_DIR / "topology_stages"
    manifest = []
    for stage_name, source, description in STAGES:
        vertices = state.prefit_vertices if source == "prefit" else state.fitted_vertices
        export_obj(vertices, state.garment_faces, output_dir / f"{stage_name}.obj")
        for view in ("front", "side"):
            render_stage_mesh(
                state=state,
                garment_vertices=vertices,
                output_path=output_dir / f"{stage_name}_{view}_shaded.png",
                view=view,
                wireframe=False,
            )
            render_stage_mesh(
                state=state,
                garment_vertices=vertices,
                output_path=output_dir / f"{stage_name}_{view}_wireframe.png",
                view=view,
                wireframe=True,
            )

        manifest.append(
            {
                "stage": stage_name,
                "source": source,
                "description": description,
                "metrics": topology_metrics(vertices, state.garment_faces),
            }
        )

    write_json(manifest, output_dir / "topology_stage_manifest.json")
    print(f"topology stage captures: {output_dir}")


if __name__ == "__main__":
    main()

