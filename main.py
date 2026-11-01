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
async def scheduled_post(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id  # آی‌دی کانال یا چت مقصد
    
    try:
        # اینجا بعداً می‌توانی متن یا محتوای مورد نظرت را از منبع دلخواهت بگیری
        message_text = "سلام! این یک پست خودکار است که از پس‌زمینه ارسال شده."
        
        # ارسال پیام به کانال
        await context.bot.send_message(chat_id=chat_id, text=message_text)
        print("پست با موفقیت در کانال منتشر شد.")
        
    except Exception as e:
        print(f"خطا در ارسال پست خودکار: {e}")

async def post_init(application: Application):
    # تعیین کانال مقصد (آی‌دی عددی کانال یا یوزرنیم آن مثل @YourChannel)
    target_chat_id = "@codas_universe"
    
    # اضافه کردن تسک به JobQueue
    # مثلاً هر ۳۶۰۰ ثانیه (یک ساعت) یک‌بار اجرا شود
    # first=10 یعنی اولین اجرا ۱۰ ثانیه بعد از روشن شدن ربات باشد
    application.job_queue.run_repeating(
        scheduled_post, 
        interval=360, 
        first=10, 
        chat_id=target_chat_id,
        name="auto_poster"
    )
app = Application.builder().token(TOKEN).post_init(post_init).build()

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
