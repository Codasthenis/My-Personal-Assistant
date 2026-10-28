import httpx

CRYPTO_API = "https://api.coingecko.com/api/v3/simple/price"
MARKET_API = "https://nerkh.jahankhahan.shop/data/live.json"


async def get_market_data() -> dict:
    """دریافت اطلاعات بازار."""

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(MARKET_API)
        response.raise_for_status()

        data = response.json()

    rates = data.get("rates")

    if not isinstance(rates, dict):
        raise ValueError("ساختار پاسخ API بازار معتبر نیست")

    return data


async def get_bitcoin_usd() -> float:
    """قیمت بیت‌کوین به دلار."""

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            CRYPTO_API,
            params={
                "ids": "bitcoin",
                "vs_currencies": "usd",
            },
        )

        response.raise_for_status()
        data = response.json()

    price = data["bitcoin"]["usd"]

    if not isinstance(price, (int, float)):
        raise ValueError("قیمت بیت‌کوین معتبر نیست")

    return float(price)