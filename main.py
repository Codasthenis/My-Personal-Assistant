import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TOKEN")

from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram import Update

app = Application.builder().token(token).build()

import httpx
from telegram.constants import ParseMode

# ===============================
# ۱. ماژول استعلام بیت‌کوین
# ===============================
async def handle_bitcoin_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
            price = res.json()["bitcoin"]["usd"]
            
            await update.message.reply_text(
                "رصد شبکه کریپتو تموم شد... 🖥️\n\n"
                f"🪙 <b>بیت‌کوین:</b> <code>${price:,}</code> دلار",
                parse_mode=ParseMode.HTML
            )
    except Exception:
        await update.message.reply_text(
            "ارتباط با سرور کریپتو قطع شد، ولی خط به خط حلش می‌کنیم! ⚡️",
            parse_mode=ParseMode.HTML
        )

# ===============================
# ۲. ماژول استعلام دلار / تتر
# ===============================
async def handle_dollar_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with httpx.AsyncClient() as client:
            # دریافت نرخ لحظه‌ای تتر (معادل دلار بازار آزاد) از نوبیتکس
            res = await client.get("https://api.nobitex.ir/v2/orderbook/USDTIRT")
            data = res.json()
            # قیمت به ریال است، تقسیم بر ۱۰ برای تبدیل به تومان
            price_toman = int(float(data.get("lastTradePrice", 0)) / 10)
            
            await update.message.reply_text(
                "دفتر سفارشات ارز بررسی شد... 💵\n\n"
                f"📈 <b>نرخ دلار (تتر):</b> <code>{price_toman:,}</code> تومان",
                parse_mode=ParseMode.HTML
            )
    except Exception:
        await update.message.reply_text(
            "هوووم، ارتباط با مارکت ارز برقرار نشد. خط به خط حلش می‌کنیم! ⚡️",
            parse_mode=ParseMode.HTML
        )

# ===============================
# ۳. ماژول استعلام طلا
# ===============================
async def handle_gold_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # اینجا API یا وب‌سرویس اختصاصی طلا قرار می‌گیرد
        await update.message.reply_text(
            "در حال استعلام مظنه و گرم طلای ۱۸ عیار... ⚖️\n\n"
            "<i>(ماژول نرخ طلا به‌زودی فعال می‌شود)</i>",
            parse_mode=ParseMode.HTML
        )
    except Exception:
        await update.message.reply_text(
            "مشکلی در دریافت مظنه طلا پیش آمد. خط به خط حلش می‌کنیم! ⚡️",
            parse_mode=ParseMode.HTML
        )

# فیلترهای Regex جداگانه و هوشمند
filter_btc = filters.TEXT & ~filters.COMMAND & filters.Regex(r"(?i)قیمت.*بیت\s*کوین|قیمت.*بیتکوین")
filter_usd = filters.TEXT & ~filters.COMMAND & filters.Regex(r"(?i)قیمت.*دلار|قیمت.*تتر")
filter_gold = filters.TEXT & ~filters.COMMAND & filters.Regex(r"(?i)قیمت.*طلا|قیمت.*سکه|مظنه")

# اضافه کردن هر Handler به صورت کاملاً مستقل
app.add_handler(MessageHandler(filter_btc, handle_bitcoin_price))
app.add_handler(MessageHandler(filter_usd, handle_dollar_price))
app.add_handler(MessageHandler(filter_gold, handle_gold_price))

app.run_polling()