
from io import BytesIO

from PIL import Image, ImageOps


SUPPORTED_FORMATS = {
    "JPG": {
        "pillow_format": "JPEG",
        "extension": "jpg",
        "mime_type": "image/jpeg",
    },
    "PNG": {
        "pillow_format": "PNG",
        "extension": "png",
        "mime_type": "image/png",
    },
    "WEBP": {
        "pillow_format": "WEBP",
        "extension": "webp",
        "mime_type": "image/webp",
    },
    "BMP": {
        "pillow_format": "BMP",
        "extension": "bmp",
        "mime_type": "image/bmp",
    },
}


class ImageConversionError(Exception):
    """Raised when an image cannot be converted."""


def convert_image(
    image_data: bytes,
    target_format: str,
) -> tuple[bytes, str, str]:
    """
    Convert image bytes to a supported format.

    Returns:
        (converted_bytes, output_filename, mime_type)
    """
    target_format = target_format.upper()

    if target_format not in SUPPORTED_FORMATS:
        raise ImageConversionError("فرمت مقصد پشتیبانی نمی‌شود.")

    try:
        with Image.open(BytesIO(image_data)) as source:
            # Apply EXIF rotation, if the image contains orientation metadata.
            image = ImageOps.exif_transpose(source)
            image.load()

            # Keep only the first frame of animated images.
            # This converter produces a single-frame output.
            if image.mode not in ("RGB", "RGBA"):
                if "A" in image.getbands():
                    image = image.convert("RGBA")
                else:
                    image = image.convert("RGB")

            output = BytesIO()
            settings = {}

            if target_format == "JPG":
                # JPEG does not support transparency.
                if image.mode == "RGBA":
                    background = Image.new(
                        "RGB",
                        image.size,
                        (255, 255, 255),
                    )
                    background.paste(image, mask=image.getchannel("A"))
                    image = background
                else:
                    image = image.convert("RGB")

                settings = {"quality": 90, "optimize": True}

            elif target_format == "BMP":
                # Use RGB for broad BMP compatibility.
                if image.mode == "RGBA":
                    background = Image.new(
                        "RGB",
                        image.size,
                        (255, 255, 255),
                    )
                    background.paste(image, mask=image.getchannel("A"))
                    image = background
                else:
                    image = image.convert("RGB")

            elif target_format == "PNG":
                settings = {"optimize": True}

            elif target_format == "WEBP":
                settings = {"quality": 90, "method": 4}

            image.save(
                output,
                format=SUPPORTED_FORMATS[target_format]["pillow_format"],
                **settings,
            )

            output_info = SUPPORTED_FORMATS[target_format]
            filename = f"converted.{output_info['extension']}"

            return (
                output.getvalue(),
                filename,
                output_info["mime_type"],
            )

    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ImageConversionError(
            "ابعاد تصویر بیش از حد بزرگ است."
        ) from None
    except (Image.UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageConversionError(
            "فایل ورودی تصویر معتبر یا قابل پردازش نیست."
        ) from exc
