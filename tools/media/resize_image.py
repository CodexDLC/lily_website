"""
Resizes a specific image to a given width while maintaining aspect ratio.
Saves the result with a suffix (e.g., -mobile).

Usage:
    python tools/media/resize_image.py <path_to_image> <width> [--suffix -mobile] [--quality 80]

Example:
    python tools/media/resize_image.py src/backend_django/static/img/5.webp 400 --suffix -mobile
"""

import argparse
from pathlib import Path

from PIL import Image


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def resize_image(image_path_str: str, target_width: int, suffix: str = "-mobile", quality: int = 80):
    project_root = get_project_root()
    img_path = (project_root / image_path_str).resolve()

    if not img_path.exists() or not img_path.is_file():
        print(f"Error: '{img_path}' is not a valid file.")
        return

    try:
        with Image.open(img_path) as img:
            original_width, original_height = img.size

            # Calculate new height maintaining aspect ratio
            ratio = target_width / original_width
            target_height = int(original_height * ratio)

            print(f"Original size: {original_width}x{original_height}")
            print(f"Target size: {target_width}x{target_height} (Ratio: {ratio:.2f})")

            # Resize using high-quality LANCZOS filter
            resized_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

            # Construct new filename: image-mobile.webp
            new_filename = f"{img_path.stem}{suffix}{img_path.suffix}"
            output_path = img_path.parent / new_filename

            # Save with optimization
            resized_img.save(output_path, quality=quality, optimize=True)

            print(f"Successfully saved: {output_path.name} ({output_path.stat().st_size / 1024:.1f} KB)")

    except Exception as e:
        print(f"Error processing image: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resize image maintaining aspect ratio.")
    parser.add_argument("path", type=str, help="Path to image relative to project root.")
    parser.add_argument("width", type=int, help="Target width in pixels.")
    parser.add_argument("--suffix", type=str, default="-mobile", help="Suffix for the new file (default: -mobile).")
    parser.add_argument("--quality", type=int, default=80, help="JPEG/WebP quality (default: 80).")

    args = parser.parse_args()
    resize_image(args.path, args.width, args.suffix, args.quality)
