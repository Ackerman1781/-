import os
from urllib.parse import quote

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_USERNAME = os.getenv("TELEGRAM_USERNAME", "Desa_iz").lstrip("@")
TELEGRAM_URL = f"https://t.me/@Desa_iz}"
SITE_URL = os.getenv("SITE_URL", "http://127.0.0.1:5000").rstrip("/")
SHOP_NAME = os.getenv("SHOP_NAME", "TREIL ZOOM")


def telegram_order_link(text: str) -> str:
    return f"{TELEGRAM_URL}?text={quote(text)}"
