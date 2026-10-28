import re

ASSETS = {
    "bitcoin": [
        r"بیت\s*کوین",
        r"\bbitcoin\b",
        r"\bbtc\b",
    ],
    "tether": [
        r"تتر",
        r"\btether\b",
        r"\busdt\b",
    ],
    "dollar": [
        r"دلار",
        r"\bdollar\b",
        r"\busd\b",
    ],
    "gold": [
        r"طلا",
        r"طلای\s*\d+",
        r"سکه",
        r"مظنه",
        r"\bgold\b",
    ],
}


def detect_assets(text: str) -> list[str]:
    """تشخیص دارایی‌های ذکرشده در پیام."""

    found = []

    for asset, patterns in ASSETS.items():
        if any(re.search(p, text) for p in patterns):
            found.append(asset)

    return found


def format_price(value: float, decimals: int = 0) -> str:
    """قالب‌بندی قیمت."""

    if decimals:
        return f"{value:,.{decimals}f}"

    return f"{value:,.0f}"

