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
# Rasm/video shablonlari saqlanadigan papka (git bilan yuborilmaydi, deploy da saqlanadi).
MEDIA_DIR = os.getenv("MEDIA_DIR", "media")
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

# Broadcast/e'lon yubora oladigan adminlarning Telegram ID lari (vergul bilan)
ADMIN_IDS = {
    int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x.strip()
}

# Admin buyruqlari (/elon, /kunlik, /add_days ...) FAQAT shu guruhda ishlaydi.
# Kunlik hisobot ham shu guruhga yuboriladi. Guruh id manfiy bo'ladi (masalan -1001234567890).
# Bot shu guruhga a'zo bo'lishi va privacy mode O'CHIQ bo'lishi kerak (oddiy xabarlarni ko'rishi uchun).
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID", "0"))

# Kunlik hisobot vaqti (Toshkent) va top ro'yxat uzunligi.
REPORT_HOUR = int(os.getenv("REPORT_HOUR", "9"))
REPORT_TOP_N = int(os.getenv("REPORT_TOP_N", "50"))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Tashkent")
