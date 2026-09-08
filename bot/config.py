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
# Minimal interval (soniyada). Juda kichik qilsangiz akkaunt bloklanishi mumkin.
MIN_INTERVAL_SECONDS = int(os.getenv("MIN_INTERVAL_SECONDS", "30"))
SEND_DELAY_SECONDS = float(os.getenv("SEND_DELAY_SECONDS", "4"))

# Yangi foydalanuvchiga beriladigan bepul sinov kunlari
TRIAL_DAYS = int(os.getenv("TRIAL_DAYS", "3"))

# Do'st taklif qilgani uchun beriladigan bonus kunlar (har bir yangi user uchun)
REFERRAL_DAYS = int(os.getenv("REFERRAL_DAYS", "3"))

# To'lov uchun bog'lanadigan admin username (masalan @taxi_admin)
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@admin")
if SUPPORT_USERNAME and not SUPPORT_USERNAME.startswith("@"):
    SUPPORT_USERNAME = "@" + SUPPORT_USERNAME
