"""Konfiguratsiya — .env fayldan o'qiladi."""
import os

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} .env faylda ko'rsatilmagan")
    return value


API_ID = int(_require("API_ID"))
API_HASH = _require("API_HASH")
BOT_TOKEN = _require("BOT_TOKEN")

DB_PATH = os.getenv("DB_PATH", "taxi_bot.db")
MIN_INTERVAL_MINUTES = int(os.getenv("MIN_INTERVAL_MINUTES", "5"))
SEND_DELAY_SECONDS = float(os.getenv("SEND_DELAY_SECONDS", "4"))
