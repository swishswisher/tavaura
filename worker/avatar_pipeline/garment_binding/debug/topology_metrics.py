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
    region_density_metrics,
    topology_metrics,
    write_json,
)


def main() -> None:
    state = build_debug_mesh_state()
    report = {
        "case": {
            "archetype": state.archetype_name,
            "pose": state.pose_name,
        },
        "pre_fit": topology_metrics(state.prefit_vertices, state.garment_faces),
        "post_fit": topology_metrics(state.fitted_vertices, state.garment_faces),
        "pre_fit_region_density": region_density_metrics(
            state.prefit_vertices,
            state.garment_faces,
            state.regions,
        ),
        "post_fit_region_density": region_density_metrics(
            state.fitted_vertices,
            state.garment_faces,
            state.regions,
        ),
        "notes": [
            "Topology metrics use edge-connected face components, not visual overlap.",
            "Fitting currently preserves face topology and only moves vertices.",
        ],
    }
    output_path = OUTPUT_DIR / "topology_report.json"
    write_json(report, output_path)
    print(f"topology metrics report: {output_path}")


if __name__ == "__main__":
    main()
