import os
import logging
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
TM1 = os.getenv("TM1")
TM2 = os.getenv("TM2")
TM3 = os.getenv("TM3")
TM4 = os.getenv("TM4")
TM5 = os.getenv("TM5")
BOT_TOKENS = {
    "bot1": TOKEN,
    "bot2": TM1,
    "bot3": TM2,
    "bot4": TM3,
    "bot5": TM4,
    "bot6": TM5,
}

missing_tokens = [
    bot_id
    for bot_id, token in BOT_TOKENS.items()
    if not token
]

if missing_tokens:
    raise ValueError(
        f"Missing bot tokens: {', '.join(missing_tokens)}"
    )


WEBHOOK_SECRETS = {
    "bot1": os.getenv("BOT1_WEBHOOK_SECRET"),
    "bot2": os.getenv("BOT2_WEBHOOK_SECRET"),
    "bot3": os.getenv("BOT3_WEBHOOK_SECRET"),
    "bot4": os.getenv("BOT4_WEBHOOK_SECRET"),
    "bot5": os.getenv("BOT5_WEBHOOK_SECRET"),
    "bot6": os.getenv("BOT6_WEBHOOK_SECRET"),
}

missing_secrets = [
    bot_id
    for bot_id, secret in WEBHOOK_SECRETS.items()
    if not secret or len(secret) < 32
]

if missing_secrets:
    raise ValueError(
        f"Missing or weak webhook secrets: {', '.join(missing_secrets)}"
    )

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("CodasthenisAssistant")

