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
from loader import TOKEN, TM1, TM2, TM3, TM4, TM5, logger
from command_handlers import start_command, help_command
from text_processing import detect_intent
from file_conversion import register_file_conversion_handlers
from background_core import scheduled_post
from background_core import react
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
mini1 = Application.builder().token(TM1).build()
mini2 = Application.builder().token(TM2).build()
mini3 = Application.builder().token(TM3).build()
mini4 = Application.builder().token(TM4).build()
mini5 = Application.builder().token(TM5).build()
target_chat_id = "@codas_universe"
# app.job_queue.run_repeating(
#         scheduled_post, 
#         interval=3600, 
#         first=10, 
#         chat_id=target_chat_id,
#         name="auto_poster"
#     )
app.add_handler(MessageHandler(filters.ChatType.CHANNEL, react("🤣")))
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CommandHandler("help", help_command))
register_file_conversion_handlers(app)
# برای هر ربات، هندلر جداگانه بساز

mini1.add_handler(MessageHandler(filters.ChatType.CHANNEL, react("🔥")))
mini2.add_handler(MessageHandler(filters.ChatType.CHANNEL, react("👍")))
mini3.add_handler(MessageHandler(filters.ChatType.CHANNEL, react("🤣")))
mini4.add_handler(MessageHandler(filters.ChatType.CHANNEL, react("💯")))
mini5.add_handler(MessageHandler(filters.ChatType.CHANNEL, react("👏")))
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message,
    )
)

BOT_APPLICATIONS = {
    "bot1": app,
    "bot2": mini1,
    "bot3": mini2,
    "bot4": mini3,
    "bot5": mini4,
    "bot6": mini5,
}