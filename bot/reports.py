"""Kunlik hisobot — har kuni soat REPORT_HOUR (Toshkent) da admin guruhga yuboriladi.

Loyihaning uslubiga mos ravishda APScheduler EMAS — oddiy asyncio loop:
keyingi 09:00 (Toshkent) gacha uxlaydi → yuboradi → takrorlaydi.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot

from . import config, db

log = logging.getLogger(__name__)

_TZ = ZoneInfo(config.TIMEZONE)
_UTC = ZoneInfo("UTC")
_MONTHS_UZ = ["yan", "fev", "mar", "apr", "may", "iyn",
              "iyl", "avg", "sen", "okt", "noy", "dek"]


def _yesterday_window() -> tuple[str, str, str, str]:
    """Kecha (Toshkent) uchun: (day, start_utc, end_utc, label)."""
    now_tk = datetime.now(_TZ)
    today = now_tk.date()
    yesterday = today - timedelta(days=1)
    start_tk = datetime.combine(yesterday, time.min, _TZ)
    end_tk = datetime.combine(today, time.min, _TZ)
    fmt = "%Y-%m-%d %H:%M:%S"
    start_utc = start_tk.astimezone(_UTC).strftime(fmt)
    end_utc = end_tk.astimezone(_UTC).strftime(fmt)
    label = f"{yesterday.day}-{_MONTHS_UZ[yesterday.month - 1]} {yesterday.year}"
    return yesterday.isoformat(), start_utc, end_utc, label


def _fmt_money(amount: int) -> str:
    """1234567 -> '1 234 567'."""
    return f"{amount:,}".replace(",", " ")


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


async def build_report() -> tuple[str, str]:
    """Hisobot matnini (HTML) va qisqa xulosani qaytaradi."""
    day, start_utc, end_utc, label = _yesterday_window()
    d = await db.report_data(day, start_utc, end_utc, config.REPORT_TOP_N)

    lines = [
        f"📊 <b>Kunlik hisobot</b> — {label}",
        "",
        f"🆕 Yangi foydalanuvchilar: <b>{d['new_users']}</b> ta",
        f"👥 Kecha faol: <b>{d['active_yesterday']}</b> ta",
        f"📤 Hozir tarqatayotgan: <b>{d['broadcasting_now']}</b> ta",
        f"🔑 Kirgan akkauntlar: <b>{d['logged_in']}</b> ta",
        f"👤 Jami foydalanuvchilar: <b>{d['total_users']}</b> ta",
        f"💰 Kecha tushgan pul: <b>{_fmt_money(d['revenue'])}</b> so'm "
        f"({d['payments_count']} ta to'lov)",
    ]

    if d["top_payers"]:
        lines.append("")
        lines.append(f"🏆 <b>Kecha top to'lovchilar</b>:")
        for i, p in enumerate(d["top_payers"], 1):
            name = _esc((p.get("full_name") or "Nomaʼlum").strip())
            handle = f"@{p['username']}" if p.get("username") else f"<code>{p['user_id']}</code>"
            lines.append(f"{i}. {name} — {handle} — <b>{_fmt_money(int(p['total']))}</b> so'm")

    summary = (
        f"{d['new_users']} yangi, {d['active_yesterday']} faol, "
        f"{_fmt_money(d['revenue'])} so'm"
    )
    return "\n".join(lines), summary


async def send_report(bot: Bot) -> str:
    """Hisobotni admin guruhga yuboradi. Qisqa xulosani qaytaradi."""
    text, summary = await build_report()
    if len(text) > 4000:  # Telegram limiti 4096
        text = text[:3990] + "\n…"
    await bot.send_message(
        config.ADMIN_GROUP_ID, text, disable_web_page_preview=True
    )
    log.info("kunlik hisobot yuborildi: %s", summary)
    return summary


def _seconds_until_next_report() -> float:
    now = datetime.now(_TZ)
    target = now.replace(hour=config.REPORT_HOUR, minute=0, second=0, microsecond=0)
    if now >= target:
        target += timedelta(days=1)
    return (target - now).total_seconds()


async def daily_report_loop(bot: Bot) -> None:
    """Har kuni REPORT_HOUR (Toshkent) da hisobot yuboradigan doimiy loop."""
    if not config.ADMIN_GROUP_ID:
        log.warning("ADMIN_GROUP_ID yo'q — kunlik hisobot o'chirilgan")
        return
    log.info("kunlik hisobot loop boshlandi (soat %s, %s)", config.REPORT_HOUR, config.TIMEZONE)
    while True:
        await asyncio.sleep(_seconds_until_next_report())
        try:
            await send_report(bot)
        except Exception:  # noqa: BLE001 — xato loopni o'ldirmasin
            log.exception("kunlik hisobot yuborishda xato")
        # 09:00:00 da uyg'onganda darhol qayta yubormaslik uchun kichik pauza.
        await asyncio.sleep(60)
