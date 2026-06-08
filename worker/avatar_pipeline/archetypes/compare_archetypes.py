from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CURRENT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = CURRENT_DIR / "output"
COMPARISON_PATH = OUTPUT_DIR / "archetype_comparison.png"
COLUMN_COUNT = 3
THUMBNAIL_SIZE = (300, 600)
LABEL_HEIGHT = 52
GAP = 28
BACKGROUND = "#f6f3ee"
TEXT_COLOR = "#2f2a24"


def main() -> None:
    archetype_images = sorted(
        path
        for path in OUTPUT_DIR.glob("*.png")
        if path.name != COMPARISON_PATH.name
    )
    if not archetype_images:
        raise FileNotFoundError(
            f"No archetype PNGs found in {OUTPUT_DIR}. Run render_archetypes.py first."
        )

    comparison = build_comparison_sheet(archetype_images)
    comparison.save(COMPARISON_PATH, format="PNG")
    print(f"comparison: {COMPARISON_PATH}")


def build_comparison_sheet(archetype_images: list[Path]) -> Image.Image:
    font = ImageFont.load_default()
    row_count = (len(archetype_images) + COLUMN_COUNT - 1) // COLUMN_COUNT
    cell_width = THUMBNAIL_SIZE[0] + GAP
    cell_height = THUMBNAIL_SIZE[1] + LABEL_HEIGHT + GAP
    canvas_width = (COLUMN_COUNT * cell_width) + GAP
    canvas_height = (row_count * cell_height) + GAP
    canvas = Image.new("RGB", (canvas_width, canvas_height), BACKGROUND)
    draw = ImageDraw.Draw(canvas)

    for index, image_path in enumerate(archetype_images):
        row = index // COLUMN_COUNT
        column = index % COLUMN_COUNT
        origin_x = GAP + (column * cell_width)
        origin_y = GAP + (row * cell_height)

        with Image.open(image_path) as source:
            thumbnail = _fit_on_background(source.convert("RGBA"))

        canvas.paste(thumbnail, (origin_x, origin_y))
        label = image_path.stem
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


if __name__ == "__main__":
    main()
