# utils/image_processor.py

from PIL import Image
from io import BytesIO
import os

MAX_UPLOAD_SIZE = 2 * 1024 * 1024      # 2MB
MAX_OUTPUT_SIZE = 500 * 1024           # 500KB
WEBP_QUALITIES = [85, 80, 75, 70]


class ImageProcessingError(Exception):
    pass


def process_image_to_webp(file_bytes: bytes) -> tuple[bytes, int, str]:
    """
    Converts any image to compressed WEBP ≤ 500KB.

    Returns:
        (webp_bytes, size_in_bytes, mime_type)
    """

    # ─────────────────────────────
    # 1️⃣ Upload size guard
    # ─────────────────────────────
    if len(file_bytes) > MAX_UPLOAD_SIZE:
        raise ImageProcessingError("Image exceeds 2MB upload limit")

    # ─────────────────────────────
    # 2️⃣ Load image safely
    # ─────────────────────────────
    try:
        img = Image.open(BytesIO(file_bytes))
        img.load()
    except Exception:
        raise ImageProcessingError("Invalid or corrupted image")

    # Convert to RGB (WEBP safe)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    if img.mode == "RGBA":
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background

    # ─────────────────────────────
    # 3️⃣ Compress loop
    # ─────────────────────────────
    for quality in WEBP_QUALITIES:
        buffer = BytesIO()
        img.save(
            buffer,
            format="WEBP",
            quality=quality,
            optimize=True,
            method=6
        )

        size = buffer.tell()
        if size <= MAX_OUTPUT_SIZE:
            return buffer.getvalue(), size, "image/webp"

    # ─────────────────────────────
    # 4️⃣ Fail if cannot compress
    # ─────────────────────────────
    raise ImageProcessingError(
        "Unable to compress image below 500KB without quality loss"
    )
