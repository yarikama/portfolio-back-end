"""
WebP variants of uploaded images, made in the background by the image
worker (worker.py). An original at covers/20260205/230ac736.png gets
covers/20260205/230ac736.w640.webp and .w1600.webp next to it; the site
asks for them with srcset and falls back to the original until they exist.
Design: homelab docs/13-background-jobs.md.
"""

import io
import re

from PIL import Image, ImageOps

# Card and phone widths, and full-width on a large screen.
WIDTHS = (640, 1600)
QUALITY = 80
# GIFs are left alone: they may be animated.
PROCESSABLE = re.compile(r"\.(jpe?g|png|webp)$", re.IGNORECASE)
VARIANT = re.compile(r"\.w\d+\.webp$")
# A decompression bomb (a small file that decodes to gigapixels) fails
# the job instead of exhausting the worker's memory. 40 MP is well above
# any camera photo.
Image.MAX_IMAGE_PIXELS = 40_000_000


# The largest image the admin may upload; api/body_limit.py refuses larger
# request bodies before they are read.
MAX_UPLOAD_BYTES = 20 * 1024 * 1024

# What an upload may be, by what Pillow finds in the bytes, never by the
# file name or the type the browser claims: the stored extension and
# Content-Type come from here.
UPLOAD_FORMATS = {
    "JPEG": ("jpg", "image/jpeg"),
    "PNG": ("png", "image/png"),
    "GIF": ("gif", "image/gif"),
    "WEBP": ("webp", "image/webp"),
}


class NotAnImageError(ValueError):
    """The bytes are not a JPEG, PNG, GIF or WebP image Pillow can read."""


def identify_upload(data: bytes) -> tuple[str, str]:
    """The extension and Content-Type to store an upload under."""
    try:
        with Image.open(io.BytesIO(data)) as opened:
            image_format = opened.format
            opened.verify()  # reads the file through; catches truncation
    except (Image.DecompressionBombError, OSError, SyntaxError, ValueError) as err:
        raise NotAnImageError(str(err)) from err
    if image_format not in UPLOAD_FORMATS:
        raise NotAnImageError(f"unsupported format {image_format}")
    return UPLOAD_FORMATS[image_format]


def is_original(key: str) -> bool:
    return bool(PROCESSABLE.search(key)) and not VARIANT.search(key)


def variant_key(key: str, width: int) -> str:
    stem = key.rsplit(".", 1)[0]
    return f"{stem}.w{width}.webp"


def make_variants(data: bytes) -> dict[int, bytes]:
    """
    One WebP per width. Never upscales: an image narrower than a width is
    stored at its own size under that width's name, so every original has
    the same set of variants.
    """
    with Image.open(io.BytesIO(data)) as opened:
        # Phones store rotation in EXIF; bake it in, since the variant
        # keeps no EXIF.
        image = ImageOps.exif_transpose(opened)
        image.load()
    if image.mode not in ("RGB", "RGBA"):
        has_alpha = image.mode in ("LA", "PA") or "transparency" in image.info
        image = image.convert("RGBA" if has_alpha else "RGB")

    variants = {}
    for width in WIDTHS:
        resized = image
        if image.width > width:
            height = round(image.height * width / image.width)
            resized = image.resize((width, height), Image.Resampling.LANCZOS)
        out = io.BytesIO()
        resized.save(out, "WEBP", quality=QUALITY, method=4)
        variants[width] = out.getvalue()
    return variants
