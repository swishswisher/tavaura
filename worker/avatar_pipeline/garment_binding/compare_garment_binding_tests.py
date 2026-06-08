from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CURRENT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = CURRENT_DIR / "output"
COMPARISON_PATH = OUTPUT_DIR / "garment_structure_comparison.png"
ARCHETYPE_NAMES = ("slim", "athletic", "curvy", "plus_size")
POSE_NAMES = ("neutral", "relaxed", "slight_walk")
THUMBNAIL_SIZE = (300, 600)
LABEL_HEIGHT = 52
GAP = 28
BACKGROUND = "#f6f3ee"
TEXT_COLOR = "#2f2a24"


def main() -> None:
    _validate_inputs()
    comparison = build_comparison_sheet()
    comparison.save(COMPARISON_PATH, format="PNG")
    print(f"comparison: {COMPARISON_PATH}")


def build_comparison_sheet() -> Image.Image:
    font = ImageFont.load_default()
    cell_width = THUMBNAIL_SIZE[0] + GAP
    cell_height = THUMBNAIL_SIZE[1] + LABEL_HEIGHT + GAP
    canvas_width = (len(ARCHETYPE_NAMES) * cell_width) + GAP
    canvas_height = (len(POSE_NAMES) * cell_height) + GAP
    canvas = Image.new("RGB", (canvas_width, canvas_height), BACKGROUND)
    draw = ImageDraw.Draw(canvas)

    for row, pose_name in enumerate(POSE_NAMES):
        for column, archetype_name in enumerate(ARCHETYPE_NAMES):
            image_path = OUTPUT_DIR / f"{archetype_name}_tshirt_{pose_name}.png"
            origin_x = GAP + (column * cell_width)
            origin_y = GAP + (row * cell_height)

            with Image.open(image_path) as source:
                thumbnail = _fit_on_background(source.convert("RGBA"))

            canvas.paste(thumbnail, (origin_x, origin_y))
            label = f"{archetype_name} {pose_name}"
            label_box = draw.textbbox((0, 0), label, font=font)
            label_width = label_box[2] - label_box[0]
            label_x = origin_x + ((THUMBNAIL_SIZE[0] - label_width) // 2)
            label_y = origin_y + THUMBNAIL_SIZE[1] + 14
            draw.text((label_x, label_y), label, fill=TEXT_COLOR, font=font)

    return canvas


def _fit_on_background(image: Image.Image) -> Image.Image:
    image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
    background = Image.new("RGBA", THUMBNAIL_SIZE, BACKGROUND)
    x = (THUMBNAIL_SIZE[0] - image.width) // 2
    y = (THUMBNAIL_SIZE[1] - image.height) // 2
    background.alpha_composite(image, (x, y))
    return background.convert("RGB")


def _validate_inputs() -> None:
    missing_paths: list[Path] = []
    for pose_name in POSE_NAMES:
        for archetype_name in ARCHETYPE_NAMES:
            path = OUTPUT_DIR / f"{archetype_name}_tshirt_{pose_name}.png"
            if not path.exists():
                missing_paths.append(path)

    if missing_paths:
        missing = "\n".join(str(path) for path in missing_paths)
        raise FileNotFoundError(
            "Missing garment binding renders. Run render_garment_binding_tests.py first.\n"
            + missing
        )


if __name__ == "__main__":
    main()
