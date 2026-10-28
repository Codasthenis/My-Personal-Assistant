
from io import BytesIO
import logging

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from file_conversion.image_converter import (
    ImageConversionError,
    SUPPORTED_FORMATS,
    convert_image,
)


logger = logging.getLogger(__name__)

MAX_INPUT_SIZE = 10 * 1024 * 1024  # 10 MB
PENDING_IMAGE_KEY = "pending_image_conversion"


def _format_keyboard() -> InlineKeyboardMarkup:
    """Build the target-format selection keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("JPG", callback_data="imgfmt:JPG"),
            InlineKeyboardButton("PNG", callback_data="imgfmt:PNG"),
        ],
        [
            InlineKeyboardButton("WEBP", callback_data="imgfmt:WEBP"),
            InlineKeyboardButton("BMP", callback_data="imgfmt:BMP"),
        ],
        [
            InlineKeyboardButton(
                "لغو",
                callback_data="imgfmt:CANCEL",
            ),
        ],
    ])


async def receive_image(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Receive an image and ask which format to use."""
    message = update.effective_message
    if message is None:
        return

    # Telegram photos may have multiple resolutions.
    if message.photo:
        telegram_file = await message.photo[-1].get_file()
        original_name = "image"
        file_size = telegram_file.file_size or 0

    elif message.document:
        document = message.document
        mime_type = document.mime_type or ""

        if not mime_type.startswith("image/"):
            await message.reply_text(
                "فعلاً فقط فایل‌های تصویری را می‌پذیرم."
            )
            return

        telegram_file = await document.get_file()
        original_name = document.file_name or "image"
        file_size = document.file_size or telegram_file.file_size or 0

    else:
        return

    if file_size > MAX_INPUT_SIZE:
        await message.reply_text(
            "حجم تصویر بیش از حد مجاز است. "
            "لطفاً تصویری کوچک‌تر از ۱۰ مگابایت بفرست."
        )
        return

    buffer = BytesIO()

    try:
        await telegram_file.download_to_memory(out=buffer)
        image_data = buffer.getvalue()
    except Exception:
        logger.exception("Failed to download an image from Telegram.")
        await message.reply_text(
            "دریافت تصویر ناموفق بود. لطفاً دوباره امتحان کن."
        )
        return

    if not image_data:
        await message.reply_text("فایل دریافتی خالی است.")
        return

    # Keep the image in memory for this user's next button press.
    context.user_data[PENDING_IMAGE_KEY] = {
        "data": image_data,
        "name": original_name,
    }

    await message.reply_text(
        "تصویر دریافت شد. فرمت خروجی را انتخاب کن:",
        reply_markup=_format_keyboard(),
    )


async def handle_format_selection(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Convert the pending image after a format button is pressed."""
    query = update.callback_query
    if query is None:
        return

    await query.answer()

    selected_format = (query.data or "").partition(":")[2]

    if selected_format == "CANCEL":
        context.user_data.pop(PENDING_IMAGE_KEY, None)
        await query.edit_message_text("تبدیل تصویر لغو شد.")
        return

    if selected_format not in SUPPORTED_FORMATS:
        await query.edit_message_text(
            "این فرمت پشتیبانی نمی‌شود. دوباره تصویر را بفرست."
        )
        return

    pending = context.user_data.get(PENDING_IMAGE_KEY)
    if not pending:
        await query.edit_message_text(
            "تصویری برای تبدیل پیدا نکردم. لطفاً دوباره تصویر را بفرست."
        )
        return

    await query.edit_message_text(
        f"در حال تبدیل تصویر به {selected_format}..."
    )

    try:
        converted_data, filename, mime_type = convert_image(
            pending["data"],
            selected_format,
        )
    except ImageConversionError as exc:
        context.user_data.pop(PENDING_IMAGE_KEY, None)
        await query.message.reply_text(str(exc))
        return
    except Exception:
        logger.exception("Unexpected image conversion error.")
        context.user_data.pop(PENDING_IMAGE_KEY, None)
        await query.message.reply_text(
            "هنگام تبدیل تصویر خطایی رخ داد. لطفاً دوباره امتحان کن."
        )
        return

    output = BytesIO(converted_data)
    output.name = filename

    try:
        await query.message.reply_document(
            document=output,
            filename=filename,
            read_timeout=60,
            write_timeout=60,
            connect_timeout=20,
            pool_timeout=20,
            caption=f"تبدیل تصویر به {selected_format} انجام شد.",
        )
    except Exception:
        logger.exception("Failed to send the converted image.")
        await query.message.reply_text(
            "تصویر تبدیل شد، اما ارسال فایل ناموفق بود."
        )
    finally:
        context.user_data.pop(PENDING_IMAGE_KEY, None)
        output.close()


def register_file_conversion_handlers(
    application: Application,
) -> None:
    """Register all handlers for the file conversion feature."""
    application.add_handler(
        MessageHandler(
            filters.PHOTO | filters.Document.IMAGE,
            receive_image,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            handle_format_selection,
            pattern=r"^imgfmt:(JPG|PNG|WEBP|BMP|CANCEL)$",
        )
    )
