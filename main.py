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
app.job_queue.run_repeating(
        scheduled_post, 
        interval=3600, 
        first=10, 
        chat_id=target_chat_id,
        name="auto_poster"
    )

app.add_handler(CommandHandler("start", start_command))
app.add_handler(CommandHandler("help", help_command))
register_file_conversion_handlers(app)
# برای هر ربات، هندلر جداگانه بساز
mini1.add_handler(MessageHandler(filters.ChatType.CHANNEL, react("🔥")))
mini2.add_handler(MessageHandler(filters.ChatType.CHANNEL, react("👍")))
mini3.add_handler(MessageHandler(filters.ChatType.CHANNEL, react("❤️")))
mini4.add_handler(MessageHandler(filters.ChatType.CHANNEL, react("💯")))
mini5.add_handler(MessageHandler(filters.ChatType.CHANNEL, react("👏")))
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message,
    )
)

import asyncio
from telegram.error import NetworkError

async def safe_init(bot_app, name):
    for attempt in range(1, 4):
        try:
            await bot_app.initialize()
            await bot_app.start()
            logger.info(f"{name} initialized successfully.")
            return
        except NetworkError as e:
            logger.warning(f"Network error on {name} (attempt {attempt}/3): {e}. Retrying in 2 seconds...")
            await asyncio.sleep(2)
    # اگر بعد از ۳ بار هم نشد، خطا را بالا بفرست
    await bot_app.initialize()
    await bot_app.start()

async def run_all_bots():
    # راه‌اندازی با فاصله و امن
    await safe_init(app, "Main App")
    await asyncio.sleep(1)
    await safe_init(mini1, "Mini 1")
    await asyncio.sleep(1)
    await safe_init(mini2, "Mini 2")
    await asyncio.sleep(1)
    await safe_init(mini3, "Mini 3")
    await asyncio.sleep(1)
    await safe_init(mini4, "Mini 4")
    await asyncio.sleep(1)
    await safe_init(mini5, "Mini 5")
    # شروع دریافت پیام‌ها
    await app.updater.start_polling()
    await mini1.updater.start_polling()
    await mini2.updater.start_polling()
    await mini3.updater.start_polling()
    await mini4.updater.start_polling()
    await mini5.updater.start_polling()
    logger.info("All 3 bots are polling concurrently...")

    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        logger.info("Stopping bots...")
        for b in [app, mini1, mini2, mini3, mini4, mini5]:
            if b.updater and b.updater.running:
                await b.updater.stop()
            await b.stop()
            await b.shutdown()

def main():
    asyncio.run(run_all_bots())

if __name__ == "__main__":
    logger.info("Assistant is running")
    main()
