from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CURRENT_DIR = Path(__file__).resolve().parent
ORIGINAL_DIR = CURRENT_DIR / "output"
AMPLIFIED_DIR = CURRENT_DIR / "output_amplified"
COMPARISON_PATH = AMPLIFIED_DIR / "original_vs_amplified.png"
PROFILE_ORDER = (
    "slim_light",
    "athletic",
    "soft_average",
    "broad_heavy",
    "tall_slim",
    "compact_strong",
)
THUMBNAIL_SIZE = (280, 560)
LABEL_HEIGHT = 48
GAP = 28
BACKGROUND = "#f6f3ee"
TEXT_COLOR = "#2f2a24"


def main() -> None:
    _validate_inputs()
    AMPLIFIED_DIR.mkdir(parents=True, exist_ok=True)
    comparison = build_original_vs_amplified_sheet()
    comparison.save(COMPARISON_PATH, format="PNG")
    print(f"comparison: {COMPARISON_PATH}")


def build_original_vs_amplified_sheet() -> Image.Image:
    font = ImageFont.load_default()
    cell_width = THUMBNAIL_SIZE[0] + GAP
    cell_height = THUMBNAIL_SIZE[1] + LABEL_HEIGHT + GAP
    canvas_width = (2 * cell_width) + GAP
    canvas_height = (len(PROFILE_ORDER) * cell_height) + GAP
    canvas = Image.new("RGB", (canvas_width, canvas_height), BACKGROUND)
    draw = ImageDraw.Draw(canvas)

    for row, profile_name in enumerate(PROFILE_ORDER):
        y = GAP + (row * cell_height)
        pairs = (
            (ORIGINAL_DIR / f"{profile_name}.png", f"{profile_name} original"),
            (AMPLIFIED_DIR / f"{profile_name}.png", f"{profile_name} amplified"),
        )
        for column, (image_path, label) in enumerate(pairs):
            x = GAP + (column * cell_width)
            with Image.open(image_path) as source:
                thumbnail = _fit_on_background(source.convert("RGBA"))

            canvas.paste(thumbnail, (x, y))
            label_box = draw.textbbox((0, 0), label, font=font)
            label_width = label_box[2] - label_box[0]
            label_x = x + ((THUMBNAIL_SIZE[0] - label_width) // 2)
            label_y = y + THUMBNAIL_SIZE[1] + 14
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
    for profile_name in PROFILE_ORDER:
        original_path = ORIGINAL_DIR / f"{profile_name}.png"
        amplified_path = AMPLIFIED_DIR / f"{profile_name}.png"
        if not original_path.exists():
            missing_paths.append(original_path)
        if not amplified_path.exists():
            missing_paths.append(amplified_path)

    if missing_paths:
        missing = "\n".join(str(path) for path in missing_paths)
        raise FileNotFoundError(
            "Missing profile renders. Run render_profiles.py and "
            f"render_amplified_profiles.py first.\n{missing}"
        )


if __name__ == "__main__":
    main()
