import io
import os

import PIL.Image
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
        return

    # Open image
    try:
        img: PIL.Image.Image = PIL.Image.open(image_field)
    except Exception:
        return  # Not an image or error opening

    # Convert to RGB (if RGBA/P/CMYK)
    if img.mode in ("RGBA", "P", "CMYK"):
        img = img.convert("RGB")

    # Resize if too large
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), PIL.Image.Resampling.LANCZOS)

    # Save to buffer as WebP
    buffer = io.BytesIO()
    img.save(buffer, format="WEBP", quality=quality, optimize=True)
    new_content = ContentFile(buffer.getvalue())

    # Update filename
    filename = os.path.splitext(image_field.name)[0]
    if not filename.lower().endswith(".webp"):
        filename += ".webp"
    new_name = os.path.basename(filename)

    # Save back to field
    # If it's a Django FieldFile (has .save() method)
    if hasattr(image_field, "save"):
        image_field.save(new_name, new_content, save=False)
    else:
        # For SimpleUploadedFile (in tests) or other file-like objects
        image_field.name = new_name
        image_field.file = buffer
        if hasattr(image_field, "seek"):
            image_field.seek(0)
