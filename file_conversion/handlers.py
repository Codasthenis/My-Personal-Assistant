
from io import BytesIO
import logging
import re

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

MAX_INPUT_SIZE = 10 * 1024 * 1024
PENDING_IMAGE_KEY = "pending_image_conversion"

# User IDs currently waiting to enter custom dimensions.
AWAITING_DIMENSIONS = set()


def _dimension_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "حفظ ابعاد اصلی",
                callback_data="imgsize:keep",
            ),
        ],
        [
            InlineKeyboardButton(
                "تغییر ابعاد",
                callback_data="imgsize:custom",
            ),
        ],
        [
            InlineKeyboardButton(
                "لغو",
                callback_data="imgsize:cancel",
            ),
        ],
    ])


def _format_keyboard():
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
            InlineKeyboardButton("لغو", callback_data="imgfmt:CANCEL"),
        ],
    ])


async def receive_image(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    message = update.effective_message
    user = update.effective_user

    if message is None or user is None:
        return

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
            "حجم تصویر باید حداکثر ۱۰ مگابایت باشد."
        )
        return

    buffer = BytesIO()

    try:
        await telegram_file.download_to_memory(out=buffer)
        image_data = buffer.getvalue()
    except Exception:
        logger.exception("Failed to download image.")
        await message.reply_text(
            "دریافت تصویر ناموفق بود. لطفاً دوباره امتحان کن."
        )
        return

    if not image_data:
        await message.reply_text("فایل دریافتی خالی است.")
        return

    context.user_data[PENDING_IMAGE_KEY] = {
        "data": image_data,
        "name": original_name,
        "width": None,
        "height": None,
    }

    AWAITING_DIMENSIONS.discard(user.id)

    await message.reply_text(
        "تصویر دریافت شد.\n"
        "می‌خواهی ابعاد تصویر را تغییر بدهی؟",
        reply_markup=_dimension_keyboard(),
    )


async def handle_size_selection(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    user = update.effective_user

    if query is None or user is None:
        return

    await query.answer()
    choice = (query.data or "").partition(":")[2]

    if choice == "cancel":
        context.user_data.pop(PENDING_IMAGE_KEY, None)
        AWAITING_DIMENSIONS.discard(user.id)
        await query.edit_message_text("عملیات تبدیل لغو شد.")
        return

    pending = context.user_data.get(PENDING_IMAGE_KEY)

    if not pending:
        await query.edit_message_text(
            "تصویری برای پردازش پیدا نکردم. لطفاً دوباره بفرست."
        )
        return

    if choice == "keep":
        pending["width"] = None
        pending["height"] = None
        AWAITING_DIMENSIONS.discard(user.id)

        await query.edit_message_text(
            "ابعاد اصلی حفظ می‌شود. حالا فرمت خروجی را انتخاب کن:",
            reply_markup=_format_keyboard(),
        )
        return

    if choice == "custom":
        AWAITING_DIMENSIONS.add(user.id)

        await query.edit_message_text(
            "ابعاد دلخواه را به صورت عرضxارتفاع بفرست.\n\n"
            "مثال‌ها:\n"
            "64x64\n"
            "512x256\n\n"
            "مقادیر باید بین ۱ تا ۴۰۹۶ پیکسل باشند.\n"
            "برای لغو، /cancel را بفرست."
        )


async def receive_dimensions(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    message = update.effective_message
    user = update.effective_user

    if message is None or user is None:
        return

    pending = context.user_data.get(PENDING_IMAGE_KEY)

    if not pending:
        AWAITING_DIMENSIONS.discard(user.id)
        await message.reply_text(
            "تصویری در انتظار تغییر ابعاد نیست. لطفاً عکس را دوباره بفرست."
        )
        return

    # Accept forms such as 64x64, 64 X 64, and 64×64.
    value = message.text.strip().lower()
    value = value.replace("×", "x").replace("х", "x")

    match = re.fullmatch(r"\s*(\d+)\s*x\s*(\d+)\s*", value)

    if not match:
        await message.reply_text(
            "فرمت ابعاد درست نیست. مثلاً این‌طور بفرست: 64x64"
        )
        return

    width, height = map(int, match.groups())

    if not (1 <= width <= 4096 and 1 <= height <= 4096):
        await message.reply_text(
            "عرض و ارتفاع باید بین ۱ تا ۴۰۹۶ پیکسل باشند."
        )
        return

    if width * height > 16_000_000:
        await message.reply_text(
            "تعداد کل پیکسل‌ها بیش از حد مجاز است. "
            "ابعاد کوچک‌تری انتخاب کن."
        )
        return

    pending["width"] = width
    pending["height"] = height
    AWAITING_DIMENSIONS.discard(user.id)

    await message.reply_text(
        f"ابعاد خروجی: {width}×{height} پیکسل\n"
        "حالا فرمت خروجی را انتخاب کن:",
        reply_markup=_format_keyboard(),
    )


async def handle_format_selection(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query is None:
        return

    await query.answer()
    selected_format = (query.data or "").partition(":")[2]

    if selected_format == "CANCEL":
        context.user_data.pop(PENDING_IMAGE_KEY, None)

        user = update.effective_user
        if user:
            AWAITING_DIMENSIONS.discard(user.id)

        await query.edit_message_text("عملیات تبدیل لغو شد.")
        return

    if selected_format not in SUPPORTED_FORMATS:
        await query.edit_message_text("این فرمت پشتیبانی نمی‌شود.")
        return

    pending = context.user_data.get(PENDING_IMAGE_KEY)

    if not pending:
        await query.edit_message_text(
            "تصویری برای تبدیل پیدا نکردم. لطفاً دوباره تصویر را بفرست."
        )
        return

    width = pending.get("width")
    height = pending.get("height")

    if width and height:
        status = f"در حال تبدیل تصویر به {selected_format} با ابعاد {width}×{height}..."
    else:
        status = f"در حال تبدیل تصویر به {selected_format} با ابعاد اصلی..."

    await query.edit_message_text(status)

    try:
        converted_data, filename, mime_type = convert_image(
            pending["data"],
            selected_format,
            width=width,
            height=height,
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
        logger.exception("Failed to send converted image.")
        await query.message.reply_text(
            "تصویر تبدیل شد، اما ارسال فایل ناموفق بود."
        )
    finally:
        context.user_data.pop(PENDING_IMAGE_KEY, None)
        user = update.effective_user
        if user:
            AWAITING_DIMENSIONS.discard(user.id)
        output.close()


async def cancel_conversion(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    user = update.effective_user
    if user:
        AWAITING_DIMENSIONS.discard(user.id)

    context.user_data.pop(PENDING_IMAGE_KEY, None)

    if update.effective_message:
        await update.effective_message.reply_text(
            "عملیات تبدیل لغو شد."
        )


def register_file_conversion_handlers(
    application: Application,
) -> None:
    application.add_handler(
        MessageHandler(
            filters.PHOTO | filters.Document.IMAGE,
            receive_image,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            handle_size_selection,
            pattern=r"^imgsize:(keep|custom|cancel)$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            handle_format_selection,
            pattern=r"^imgfmt:(JPG|PNG|WEBP|BMP|CANCEL)$",
        )
    )

    # Only capture ordinary text when the user is entering dimensions.
    dimension_filter = filters.create(
        lambda message: (
            message.from_user is not None
            and message.from_user.id in AWAITING_DIMENSIONS
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & dimension_filter,
            receive_dimensions,
        )
    )

    application.add_handler(
        MessageHandler(
            filters.COMMAND & filters.Regex(r"^/cancel(?:@\w+)?$"),
            cancel_conversion,
        )
    )
