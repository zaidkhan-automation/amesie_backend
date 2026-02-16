# utils/image_processor.py

from PIL import Image
from io import BytesIO

MAX_UPLOAD_SIZE = 1 * 1024 * 1024      # 1MB upload limit
MAX_OUTPUT_SIZE = 30 * 1024            # 30KB final size
MAX_WIDTH = 800                       # Resize cap
WEBP_QUALITIES = [70, 60, 50, 40, 30]


class ImageProcessingError(Exception):
    pass


def process_image_to_webp(file_bytes: bytes) -> tuple[bytes, int, str]:
    """
    Converts image to resized + compressed WEBP ≤ 30KB
    """

    # 1️⃣ Upload guard
    if len(file_bytes) > MAX_UPLOAD_SIZE:
        raise ImageProcessingError("Image exceeds 1MB upload limit")

    # 2️⃣ Open safely
    try:
        img = Image.open(BytesIO(file_bytes))
        img.load()
    except Exception:
        raise ImageProcessingError("Invalid or corrupted image")

    # Convert to RGB safe
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    if img.mode == "RGBA":
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background

    # 3️⃣ Resize aggressively
    width, height = img.size

    if width > MAX_WIDTH:
        ratio = MAX_WIDTH / float(width)
        new_height = int(height * ratio)
        img = img.resize((MAX_WIDTH, new_height), Image.LANCZOS)

    # 4️⃣ Compression loop
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

    raise ImageProcessingError(
        "Unable to compress image below 30KB"
    )
