"""Admin panel konfiguratsiyasi (.env dan)."""
import os

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "taxi_bot.db")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    raise RuntimeError("ADMIN_PASSWORD .env faylda ko'rsatilmagan")

SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "change-me-please-" + ADMIN_USERNAME)
HOST = os.getenv("ADMIN_HOST", "127.0.0.1")
PORT = int(os.getenv("ADMIN_PORT", "8000"))
CURRENCY = os.getenv("CURRENCY", "so'm")

# React dev serveri uchun CORS (vergul bilan ajratilgan)
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "ADMIN_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if o.strip()
]
