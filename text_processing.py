import re
from exchange_rate import detect_assets

def normalize_text(text: str) -> str:
    """یکسان‌سازی متن فارسی و انگلیسی."""

    text = text.lower().strip()
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = text.replace("\u200c", " ")
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def detect_intent(text: str) -> dict:
    """تشخیص منظور اصلی کاربر."""

    text = normalize_text(text)

    if not text:
        return {"intent": "unknown"}

    # پیام خوش‌آمدگویی
    greetings = [
        "سلام",
        "درود",
        "صبح بخیر",
        "شب بخیر",
        "hello",
        "hi",
        "hey",
    ]

    if text in greetings:
        return {"intent": "greeting"}

    # راهنما
    if text in ["راهنما", "کمک", "help", "چه کارهایی بلدی"]:
        return {"intent": "help"}

    assets = detect_assets(text)

    if not assets:
        return {"intent": "unknown"}

    # درخواست بیت‌کوین به دلار نباید به‌اشتباه
    # درخواست قیمت دلار تشخیص داده شود.
    if "bitcoin" in assets and "dollar" in assets:
        assets.remove("dollar")

    # اگر چند دارایی مستقل مطرح شده باشند، سؤال بپرس.
    if len(assets) > 1:
        return {
            "intent": "clarify",
            "assets": assets,
        }

    asset = assets[0]

    # تشخیص واحد موردنظر
    if re.search(r"تومان|تومن", text):
        currency = "toman"
    elif re.search(r"دلار|دلاری|usd", text):
        currency = "usd"
    else:
        currency = "default"

    return {
        "intent": "price",
        "asset": asset,
        "currency": currency,
    }
