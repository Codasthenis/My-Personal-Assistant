from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "سلام! من دستیار فنی توام؛ سریع، دقیق و بدون حاشیه.\n\n"
        "هر طور راحتی درخواستت رو بنویس.\n"
        "مثلاً:\n"
        "• بیت‌کوین چند؟\n"
        "• دلار امروز چنده؟\n"
        "• تتر چند شده؟\n"
        "• قیمت طلای ۱۸ عیار\n\n"
        "• تبدیل تصویر به فرمت مورد نظر\n"
        "• تبدیل تصویر به سایز مورد نظر\n"
        "برای دیدن راهنما، /help رو بزن."
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "🧭 <b>چه کارهایی بلدم؟</b>\n\n"
        "₿ قیمت بیت‌کوین به دلار و تومان\n"
        "💵 قیمت دلار\n"
        "₮ قیمت تتر\n"
        "🟡 قیمت طلای ۱۸ عیار و انس جهانی\n\n"
        "لازم نیست دستور خاصی حفظ کنی؛ "
        "کافیه طبیعی بنویسی چی می‌خوای."
        "• تبدیل تصویر به فرمت مورد نظر\n"
        "اگرم میخوای تصویرت رو تبدیل کنم، به راحتی میتونی عکست رو بفرستی و به راحتی تبدیل کنی.",
        parse_mode=ParseMode.HTML,
    )

