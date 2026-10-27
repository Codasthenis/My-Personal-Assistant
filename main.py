
import os
import httpx
from dotenv import load_dotenv

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    ContextTypes,
)

load_dotenv()
token = os.getenv("TOKEN")

if not token:
    raise ValueError("متغیر TOKEN در فایل .env تنظیم نشده است")

app = Application.builder().token(token).build()

# ===============================
# تنظیمات API
# ===============================

CRYPTO_API = (
    "https://api.coingecko.com/api/v3/simple/price"
)

MARKET_API = (
    "https://nerkh.jahankhahan.shop/data/live.json"
)


def format_price(value):
    """نمایش عدد با جداکننده هزارگان."""
    return f"{value:,.0f}"


async def get_market_data():
    """دریافت نرخ‌های بازار ایران."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(MARKET_API)
        response.raise_for_status()

        data = response.json()
        rates = data.get("rates", {})

        if not rates:
            raise ValueError("داده نرخ بازار موجود نیست")

        return data


# ===============================
# ۱. قیمت بیت‌کوین
# ===============================

async def handle_bitcoin_price(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                CRYPTO_API,
                params={
                    "ids": "bitcoin",
                    "vs_currencies": "usd",
                },
            )
            response.raise_for_status()

            price_usd = response.json()["bitcoin"]["usd"]

        # نرخ دلار بازار ایران
        market = await get_market_data()
        dollar_toman = market["rates"]["dollar"]

        # محاسبه ارزش تقریبی بیت‌کوین به تومان
        price_toman = price_usd * dollar_toman

        await update.message.reply_text(
            "🪙 <b>قیمت بیت‌کوین</b>\n\n"
            f"💵 دلار: <code>${price_usd:,.2f}</code>\n"
            f"🇮🇷 تومان: <code>{format_price(price_toman)}</code>\n\n"
            "ℹ️ ارزش تومانی بر اساس نرخ دلار بازار محاسبه شده است.",
            parse_mode=ParseMode.HTML,
        )

    except Exception as exc:
        print(f"Bitcoin error: {exc}")
        await update.message.reply_text(
            "دریافت قیمت بیت‌کوین ناموفق بود؛ "
            "کمی بعد دوباره امتحان کن."
        )


# ===============================
# ۲. قیمت دلار و تتر
# ===============================

async def handle_dollar_price(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    try:
        data = await get_market_data()
        rates = data["rates"]

        dollar = rates.get("dollar")
        tether = rates.get("tether")

        if dollar is None:
            raise ValueError("نرخ دلار در پاسخ API موجود نیست")

        message = (
            "💵 <b>قیمت ارز</b>\n\n"
            f"🇺🇸 دلار: <code>{format_price(dollar)}</code> تومان\n"
        )

        if tether is not None:
            message += (
                f"₮ تتر: <code>{format_price(tether)}</code> تومان\n"
            )

        message += (
            "\nℹ️ نرخ‌ها مربوط به منبع بازار انتخاب‌شده‌اند؛ "
            "ممکن است با نرخ صرافی شما تفاوت داشته باشند."
        )

        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
        )

    except Exception as exc:
        print(f"Dollar error: {exc}")
        await update.message.reply_text(
            "دریافت نرخ دلار یا تتر ناموفق بود؛ "
            "بعداً دوباره امتحان کن."
        )


# ===============================
# ۳. قیمت طلا
# ===============================

async def handle_gold_price(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    try:
        data = await get_market_data()
        rates = data["rates"]

        gold_18 = rates.get("gold")
        ounce_usd = data.get("ounce")
        dollar = rates.get("dollar")

        message = "⚖️ <b>قیمت طلا</b>\n\n"

        if gold_18 is not None:
            message += (
                "🟡 طلای ۱۸ عیار، هر گرم:\n"
                f"<code>{format_price(gold_18)}</code> تومان\n\n"
            )

        if ounce_usd is not None:
            message += (
                "🌍 انس جهانی طلا:\n"
                f"<code>${ounce_usd:,.2f}</code>\n"
            )

            if dollar is not None:
                ounce_toman = ounce_usd * dollar
                message += (
                    f"معادل تقریبی: "
                    f"<code>{format_price(ounce_toman)}</code> تومان\n"
                )

        if gold_18 is None and ounce_usd is None:
            raise ValueError("اطلاعات طلا در پاسخ API موجود نیست")

        message += (
            "\nℹ️ قیمت انس به تومان، حاصل ضرب قیمت دلاری انس "
            "در نرخ دلار بازار است. قیمت طلای ۱۸ عیار "
            "از نرخ بازار دریافت می‌شود."
        )

        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
        )

    except Exception as exc:
        print(f"Gold error: {exc}")
        await update.message.reply_text(
            "دریافت قیمت طلا ناموفق بود؛ "
            "کمی بعد دوباره امتحان کن."
        )


# ===============================
# ۴. فیلترها و هندلرها
# ===============================

filter_btc = (
    filters.TEXT
    & ~filters.COMMAND
    & filters.Regex(
        r"(?i)قیمت.*(بیت\s*کوین|بیتکوین)"
    )
)

filter_usd = (
    filters.TEXT
    & ~filters.COMMAND
    & filters.Regex(
        r"(?i)قیمت.*(دلار|تتر)"
    )
)

filter_gold = (
    filters.TEXT
    & ~filters.COMMAND
    & filters.Regex(
        r"(?i)قیمت.*(طلا|سکه|مظنه)"
    )
)

app.add_handler(
    MessageHandler(filter_btc, handle_bitcoin_price)
)

app.add_handler(
    MessageHandler(filter_usd, handle_dollar_price)
)

app.add_handler(
    MessageHandler(filter_gold, handle_gold_price)
)

print("Bot is running...")
app.run_polling()
