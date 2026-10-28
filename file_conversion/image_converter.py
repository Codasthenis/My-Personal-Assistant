
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
    width: int | None = None,
    height: int | None = None,
) -> tuple[bytes, str, str]:
    """Convert an image, optionally resizing it."""

    target_format = target_format.upper()

    if target_format not in SUPPORTED_FORMATS:
        raise ImageConversionError("فرمت مقصد پشتیبانی نمی‌شود.")

    if (width is None) != (height is None):
        raise ImageConversionError("عرض و ارتفاع باید هر دو مشخص شوند.")

    if width is not None and height is not None:
        if not (1 <= width <= 4096 and 1 <= height <= 4096):
            raise ImageConversionError(
                "عرض و ارتفاع باید بین ۱ تا ۴۰۹۶ پیکسل باشند."
            )

        if width * height > 16_000_000:
            raise ImageConversionError(
                "ابعاد انتخاب‌شده بیش از حد بزرگ است."
            )

    try:
        with Image.open(BytesIO(image_data)) as source:
            image = ImageOps.exif_transpose(source)
            image.load()

            # Keep only the first frame of animated images.
            has_alpha = "A" in image.getbands()

            if has_alpha:
                image = image.convert("RGBA")
            else:
                image = image.convert("RGB")

            if width is not None and height is not None:
                image = image.resize(
                    (width, height),
                    Image.Resampling.LANCZOS,
                )

            output = BytesIO()
            settings = {}

            if target_format == "JPG":
                if image.mode == "RGBA":
                    background = Image.new(
                        "RGB",
                        image.size,
                        (255, 255, 255),
                    )
                    background.paste(
                        image,
                        mask=image.getchannel("A"),
                    )
                    image = background
                else:
                    image = image.convert("RGB")

                settings = {"quality": 90, "optimize": True}

            elif target_format == "BMP":
                if image.mode == "RGBA":
                    background = Image.new(
                        "RGB",
                        image.size,
                        (255, 255, 255),
                    )
                    background.paste(
                        image,
                        mask=image.getchannel("A"),
                    )
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

            info = SUPPORTED_FORMATS[target_format]
            filename = f"converted.{info['extension']}"

            return output.getvalue(), filename, info["mime_type"]

    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ImageConversionError(
            "ابعاد تصویر ورودی بیش از حد بزرگ است."
        ) from None
    except (Image.UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageConversionError(
            "فایل ورودی تصویر معتبر یا قابل پردازش نیست."
        ) from exc
