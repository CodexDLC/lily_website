import io
import os

import PIL.Image
from core.logger import log
from django.core.files.base import ContentFile


def optimize_image(image_field, max_width=1920, quality=85):
    """
    Optimizes an image:
    - Resizes to max_width (keeping aspect ratio)
    - Converts to WebP
    - Compresses

    Usage in model.save():
        if self.image and (not self.pk or 'image' in self.get_dirty_fields()):
            optimize_image(self.image)
    """
    if not image_field:
        log.debug("Service: ImageService | Action: Optimize | status=Skipped | reason=NoImage")
        return

    log.debug(
        f"Service: ImageService | Action: Optimize | name={image_field.name} | size={image_field.size if hasattr(image_field, 'size') else 'unknown'}"
    )

    # Open image
    try:
        img: PIL.Image.Image = PIL.Image.open(image_field)
    except Exception as e:
        log.error(f"Service: ImageService | Action: OptimizeFailed | name={image_field.name} | error={e}")
        return  # Not an image or error opening

    # Convert to RGB (if RGBA/P/CMYK)
    if img.mode in ("RGBA", "P", "CMYK"):
        log.debug(f"Service: ImageService | Action: ConvertMode | from={img.mode} | to=RGB")
        img = img.convert("RGB")

    # Resize if too large
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        log.debug(
            f"Service: ImageService | Action: Resize | from={img.width}x{img.height} | to={max_width}x{new_height}"
        )
        img = img.resize((max_width, new_height), PIL.Image.Resampling.LANCZOS)

    # Save to buffer as WebP
    try:
        buffer = io.BytesIO()
        img.save(buffer, format="WEBP", quality=quality, optimize=True)
        new_content = ContentFile(buffer.getvalue())
        log.debug(f"Service: ImageService | Action: SaveWebP | quality={quality} | new_size={len(buffer.getvalue())}")
    except Exception as e:
        log.error(f"Service: ImageService | Action: SaveFailed | name={image_field.name} | error={e}")
        return

    # Update filename
    filename = os.path.splitext(image_field.name)[0]
    if not filename.lower().endswith(".webp"):
        filename += ".webp"
    new_name = os.path.basename(filename)

    # Save back to field
    # If it's a Django FieldFile (has .save() method)
    if hasattr(image_field, "save"):
        image_field.save(new_name, new_content, save=False)
        log.info(f"Service: ImageService | Action: Success | name={new_name}")
    else:
        # For SimpleUploadedFile (in tests) or other file-like objects
        image_field.name = new_name
        image_field.file = buffer
        if hasattr(image_field, "seek"):
            image_field.seek(0)
        log.debug(f"Service: ImageService | Action: SuccessTest | name={new_name}")
