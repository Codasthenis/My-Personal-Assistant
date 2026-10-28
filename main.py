import re

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from exchange_rate import handle_bitcoin_price, handle_dollar_price, handle_gold_price
from loader import TOKEN, logger
from command_handlers import start_command, help_command
from text_processing import detect_intent
from file_conversion import register_file_conversion_handlers
# =========================================
# 1. Unified message router
# =========================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.message.text:
        return

    result = detect_intent(update.message.text)
    intent = result["intent"]

    if intent == "greeting":
        await update.message.reply_text(
            "سلام! آماده‌ام. چی رو بررسی کنیم؟"
        )
        return

    if intent == "help":
        await help_command(update, context)
        return

    if intent == "unknown":
        await update.message.reply_text(
            "منظورت رو دقیق نگرفتم. "
            "مثلاً بگو «بیتکوین چند؟»، «قیمت دلار» یا «طلا گرمی چنده؟»"
        )
        return

    if intent == "clarify":
        names = {
            "bitcoin": "بیت‌کوین",
            "dollar": "دلار",
            "tether": "تتر",
            "gold": "طلا",
        }

        options = "، ".join(
            names[asset] for asset in result["assets"]
        )

        await update.message.reply_text(
            f"برای اینکه اشتباه نکنم، منظورت کدومه؟ {options}"
        )
        return

    asset = result["asset"]

    if asset == "bitcoin":
        await handle_bitcoin_price(update, context)

    elif asset == "dollar":
        await handle_dollar_price(update, context, "dollar")

    elif asset == "tether":
        await handle_dollar_price(update, context, "tether")

    elif asset == "gold":
        await handle_gold_price(update, context)


# =========================================
# 2. Application
# =========================================

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start_command))
app.add_handler(CommandHandler("help", help_command))
register_file_conversion_handlers(app)
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message,
    )
)
if __name__ == "__main__":
    logger.info("Assistant is running")
    app.run_polling()
