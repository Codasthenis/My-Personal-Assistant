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
if not TOKEN:
    raise ValueError("TOKEN در فایل .env تنظیم نشده است")


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger("CodasthenisAssistant")

