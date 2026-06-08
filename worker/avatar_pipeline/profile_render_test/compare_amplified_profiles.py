from __future__ import annotations

import sys
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = CURRENT_DIR / "output_amplified"
COMPARISON_PATH = OUTPUT_DIR / "profiles_amplified_comparison.png"
GENERATED_COMPARISON_NAMES = {
    "profiles_amplified_comparison.png",
    "original_vs_amplified.png",
}

if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from compare_profiles import build_comparison_sheet  # noqa: E402


def main() -> None:
    profile_images = sorted(
        path
        for path in OUTPUT_DIR.glob("*.png")
        if path.name not in GENERATED_COMPARISON_NAMES
    )
    if not profile_images:
        raise FileNotFoundError(
            f"No amplified profile PNGs found in {OUTPUT_DIR}. "
            "Run render_amplified_profiles.py first."
        )

    comparison = build_comparison_sheet(profile_images)
    comparison.save(COMPARISON_PATH, format="PNG")
    print(f"comparison: {COMPARISON_PATH}")


if __name__ == "__main__":
    main()
