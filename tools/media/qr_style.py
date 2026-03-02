"""
QR Code Style — singleton for project-branded QR codes.

Generated: 2026-02-27 23:45
Generator: python tools/media/qr_generator.py

Usage:
    from tools.media.qr_style import qr_style

    # PIL Image
    img = qr_style.generate("https://example.com")
    img.save("qr.png")

    # Custom size
    img = qr_style.generate("https://t.me/mybot", size=200)

    # Bytes for bot/API
    data = qr_style.to_bytes("https://example.com", fmt="webp")
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

import segno
from PIL import Image, ImageDraw

if TYPE_CHECKING:
    from pathlib import Path


class QRStyle:
    """Singleton with fixed QR code style for the project."""

    _instance = None

    # ── Style settings (locked at export) ──
    FOREGROUND = "#edd071"
    BACKGROUND = "#003831"
    ERROR_CORRECTION = "H"
    DEFAULT_SIZE = 400

    def __new__(cls) -> QRStyle:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def generate(
        self,
        data: str,
        *,
        size: int | None = None,
        logo: str | Path | None = None,
    ) -> Image.Image:
        """Generate QR code in project style.

        Args:
            data: Text or URL to encode.
            size: Output size in pixels (default: DEFAULT_SIZE).
            logo: Path to logo image (optional).

        Returns:
            PIL Image in RGBA.
        """
        _size = size or self.DEFAULT_SIZE

        qr = segno.make(data, error=self.ERROR_CORRECTION)
        modules = qr.symbol_size()[0]
        scale = max(1, _size // modules)

        buf = io.BytesIO()
        qr.save(
            buf,
            kind="png",
            dark=self.FOREGROUND,
            light=self.BACKGROUND,
            scale=scale,
            border=2,
        )
        buf.seek(0)
        img = Image.open(buf).convert("RGBA")

        if img.size[0] != _size:
            img = img.resize((_size, _size), Image.Resampling.LANCZOS)

        if logo:
            logo_img = Image.open(logo).convert("RGBA")
            logo_s = _size // 4
            logo_img = logo_img.resize((logo_s, logo_s), Image.Resampling.LANCZOS)

            mask = Image.new("RGBA", (logo_s + 20, logo_s + 20), (0, 0, 0, 0))
            draw = ImageDraw.Draw(mask)
            draw.ellipse([0, 0, logo_s + 19, logo_s + 19], fill=(255, 255, 255, 255))

            pos_m = ((_size - logo_s - 20) // 2, (_size - logo_s - 20) // 2)
            img.paste(mask, pos_m, mask)
            pos_l = ((_size - logo_s) // 2, (_size - logo_s) // 2)
            img.paste(logo_img, pos_l, logo_img)

        return img

    def to_bytes(
        self,
        data: str,
        *,
        fmt: str = "png",
        size: int | None = None,
        logo: str | Path | None = None,
    ) -> bytes:
        """Generate QR and return bytes (for bot/API).

        Args:
            data: Text or URL.
            fmt: Format — "png" or "webp".
            size: Output size in pixels.
            logo: Path to logo image.

        Returns:
            Image bytes.
        """
        img = self.generate(data, size=size, logo=logo)
        buf = io.BytesIO()
        if fmt == "webp":
            img.convert("RGB").save(buf, "WebP", quality=90)
        else:
            img.save(buf, "PNG")
        return buf.getvalue()


# Singleton instance
qr_style = QRStyle()
