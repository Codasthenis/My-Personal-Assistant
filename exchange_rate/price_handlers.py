from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from .market_api import get_market_data, get_bitcoin_usd
from .text_processing import format_price
import logging

logger = logging.getLogger(__name__)

async def handle_bitcoin_price(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    try:
        price_usd = await get_bitcoin_usd()

        market = await get_market_data()
        dollar = market["rates"].get("dollar")

        message = (
            "₿ <b>بیت‌کوین</b>\n\n"
            f"💵 قیمت دلاری: <code>${format_price(price_usd, 2)}</code>\n"
        )

        if isinstance(dollar, (int, float)):
            price_toman = price_usd * dollar

            message += (
                f"🇮🇷 معادل تومانی: "
                f"<code>{format_price(price_toman)}</code> تومان\n"
            )

        message += "\n<i>قیمت‌ها ممکن است تغییر کنند.</i>"

        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
        )

    except Exception:
        logger.exception("Bitcoin price request failed")

        await update.message.reply_text(
            "الان نتونستم قیمت بیت‌کوین رو دریافت کنم. "
            "بعداً دوباره امتحان کن."
        )


async def handle_dollar_price(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    asset: str = "dollar",
):
    try:
        market = await get_market_data()
        rates = market["rates"]

        key = "tether" if asset == "tether" else "dollar"
        price = rates.get(key)

        if not isinstance(price, (int, float)):
            raise ValueError(f"نرخ {key} در پاسخ API موجود نیست")

        name = "تتر (USDT)" if asset == "tether" else "دلار"

        message = (
            f"💱 <b>قیمت {name}</b>\n\n"
            f"🇮🇷 <code>{format_price(price)}</code> تومان\n\n"
            "<i>نرخ اعلام‌شده مربوط به منبع بازار انتخاب‌شده است.</i>"
        )

        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
        )

    except Exception:
        logger.exception("Currency price request failed")

        await update.message.reply_text(
            "نتونستم نرخ ارز رو دریافت کنم. "
            "کمی بعد دوباره امتحان کن."
        )


async def handle_gold_price(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    try:
        market = await get_market_data()
        rates = market["rates"]

        gold_18 = rates.get("gold")
        ounce_usd = market.get("ounce")
        dollar = rates.get("dollar")

        message = "🟡 <b>قیمت طلا</b>\n\n"

        if isinstance(gold_18, (int, float)):
            message += (
                "طلای ۱۸ عیار، هر گرم:\n"
                f"<code>{format_price(gold_18)}</code> تومان\n\n"
            )

        if isinstance(ounce_usd, (int, float)):
            message += (
                "انس جهانی:\n"
                f"<code>${format_price(ounce_usd, 2)}</code>\n"
            )

            if isinstance(dollar, (int, float)):
                ounce_toman = ounce_usd * dollar

                message += (
                    "معادل انس به تومان:\n"
                    f"<code>{format_price(ounce_toman)}</code> تومان\n"
                )

        if not isinstance(gold_18, (int, float)) and not isinstance(
            ounce_usd, (int, float)
        ):
            raise ValueError("اطلاعات طلا موجود نیست")

        message += (
            "\n<i>قیمت انس جهانی با قیمت هر گرم طلای ۱۸ عیار متفاوت است.</i>"
        )

        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
        )

    except Exception:
        logger.exception("Gold price request failed")

        await update.message.reply_text(
            "الان نتونستم اطلاعات طلا رو دریافت کنم. "
            "بعداً دوباره امتحان کن."
        )

