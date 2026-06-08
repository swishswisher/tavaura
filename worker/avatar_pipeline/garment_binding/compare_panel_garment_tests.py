from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


CURRENT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = CURRENT_DIR / "output" / "panel_garments"
ARCHETYPE_NAMES = ("slim", "athletic", "curvy", "plus_size")
POSE_NAMES = ("neutral", "relaxed", "slight_walk")
COLUMNS = ("body", "prefit_wireframe", "postfit_wireframe", "seams", "fitted", "side")


def main() -> None:
    groups = []
    for archetype_name in ARCHETYPE_NAMES:
        for pose_name in POSE_NAMES:
            case_name = f"{archetype_name}_{pose_name}"
            paths = [OUTPUT_DIR / f"{case_name}_{column}.png" for column in COLUMNS]
            if all(path.exists() for path in paths):
                groups.append((case_name, paths))

    if not groups:
        raise RuntimeError(f"No panel garment renders found in {OUTPUT_DIR}")

    cell_width = 240
    cell_height = 520
    label_height = 38
    gap = 18
    canvas_width = (len(COLUMNS) * cell_width) + ((len(COLUMNS) + 1) * gap)
    canvas_height = (len(groups) * (cell_height + label_height)) + ((len(groups) + 1) * gap)
    canvas = Image.new("RGB", (canvas_width, canvas_height), "#f6f3ee")
    draw = ImageDraw.Draw(canvas)

    for row_index, (case_name, paths) in enumerate(groups):
        y = gap + (row_index * (cell_height + label_height + gap))
        for column_index, path in enumerate(paths):
            x = gap + (column_index * (cell_width + gap))
            image = Image.open(path).convert("RGB")
            image.thumbnail((cell_width, cell_height), Image.Resampling.LANCZOS)
            canvas.paste(image, (x + ((cell_width - image.width) // 2), y))
            draw.text((x + 8, y + cell_height + 10), f"{case_name} {COLUMNS[column_index]}", fill="#2d2823")

    output_path = OUTPUT_DIR / "panel_garment_comparison.png"
    canvas.save(output_path)
    print(f"panel comparison: {output_path}")


if __name__ == "__main__":
    main()
