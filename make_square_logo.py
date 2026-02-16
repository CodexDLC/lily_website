#!/usr/bin/env python3
"""
Script to convert a wide image to square format by adding letterbox bars.
Usage: python make_square_logo.py input_image.png output_image.png [hex_color]
"""

import os
import sys

from PIL import Image


def make_square_with_letterbox(input_path: str, output_path: str, bg_color: str = "#002822"):
    """
    Convert a wide image to square by adding letterbox bars.
    """
    if not os.path.exists(input_path):
        print(f"✗ Error: Input file not found at {input_path}")
        return False

    # Open the input image
    try:
        img = Image.open(input_path)
        # Ensure image is in a mode that supports transparency if needed
        if img.mode != "RGBA":
            img = img.convert("RGBA")
    except Exception as e:
        print(f"✗ Error: Could not open image. {e}")
        return False

    original_width, original_height = img.size
    print(f"→ Original size: {original_width}x{original_height} (Mode: {img.mode})")

    # Determine the square size
    square_size = max(original_width, original_height)

    # Convert hex color to RGB
    try:
        color = bg_color.lstrip("#")
        bg_rgb = tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))
    except Exception:
        print(f"! Warning: Invalid hex color '{bg_color}'. Using default #002822")
        bg_rgb = (0, 40, 34)

    # Create a new square image with the background color
    # We use RGB for the final output unless you specifically need transparency in the bars
    square_img = Image.new("RGB", (square_size, square_size), bg_rgb)

    # Calculate position to paste (centered)
    x_offset = (square_size - original_width) // 2
    y_offset = (square_size - original_height) // 2

    # Paste the original image using its own alpha channel as a mask
    square_img.paste(img, (x_offset, y_offset), img)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save the result
    try:
        # If output is webp, we can save as webp, otherwise png/jpg
        ext = os.path.splitext(output_path)[1].lower()
        if ext == ".webp":
            square_img.save(output_path, "WEBP", quality=95, lossless=True)
        else:
            square_img.save(output_path, quality=95)

        print(f"✓ Square image created: {square_size}x{square_size}")
        print(f"✓ Saved to: {os.path.abspath(output_path)}")
        return True
    except Exception as e:
        print(f"✗ Error saving image: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("\nUsage: python make_square_logo.py <input_path> <output_path> [hex_color]")
        print("Example: python make_square_logo.py logo.webp logo_square.png #002822\n")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    color = sys.argv[3] if len(sys.argv) > 3 else "#002822"

    if make_square_with_letterbox(input_file, output_file, color):
        print("Done!")
    else:
        sys.exit(1)
