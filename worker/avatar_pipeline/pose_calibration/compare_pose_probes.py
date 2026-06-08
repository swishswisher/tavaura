from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CURRENT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = CURRENT_DIR / "output"
COMPARISON_PATH = OUTPUT_DIR / "pose_probe_comparison.png"
BODY_POSE_SIZE = 63
THUMBNAIL_SIZE = (190, 380)
LABEL_HEIGHT = 42
GAP = 18
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
    canvas_width = (2 * cell_width) + GAP
    canvas_height = (BODY_POSE_SIZE * cell_height) + GAP
    canvas = Image.new("RGB", (canvas_width, canvas_height), BACKGROUND)
    draw = ImageDraw.Draw(canvas)

    for pose_index in range(BODY_POSE_SIZE):
        y = GAP + (pose_index * cell_height)
        variants = (
            (OUTPUT_DIR / f"pose_{pose_index:02d}_neg.png", f"pose {pose_index:02d} -0.5"),
            (OUTPUT_DIR / f"pose_{pose_index:02d}_pos.png", f"pose {pose_index:02d} +0.5"),
        )
        for column, (image_path, label) in enumerate(variants):
            x = GAP + (column * cell_width)
            with Image.open(image_path) as source:
                thumbnail = _fit_on_background(source.convert("RGBA"))

            canvas.paste(thumbnail, (x, y))
            label_box = draw.textbbox((0, 0), label, font=font)
            label_width = label_box[2] - label_box[0]
            label_x = x + ((THUMBNAIL_SIZE[0] - label_width) // 2)
            label_y = y + THUMBNAIL_SIZE[1] + 10
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
    for pose_index in range(BODY_POSE_SIZE):
        for label in ("pos", "neg"):
            path = OUTPUT_DIR / f"pose_{pose_index:02d}_{label}.png"
            if not path.exists():
                missing_paths.append(path)

    if missing_paths:
        missing = "\n".join(str(path) for path in missing_paths)
        raise FileNotFoundError(
            "Missing pose probe renders. Run pose_probe.py first.\n" + missing
        )


if __name__ == "__main__":
    main()
