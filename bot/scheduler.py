"""Interval bo'yicha xabar tarqatish — har bir user uchun alohida asyncio loop.

Nega APScheduler emas: APScheduler intervalda ishga tushirganda, agar yuborish
intervaldan uzoq cho'zilsa (ko'p guruh yoki FloodWait), sikllar ustma-ust kelib
tashlab yuboriladi ("uxlab qolish"). Bu yerda esa har bir yuborishdan KEYIN
interval kutiladi — shuning uchun sikllar hech qachon tushib qolmaydi.
"""
from __future__ import annotations

import asyncio
import logging

from . import db, userbot

log = logging.getLogger(__name__)

# {user_id: asyncio.Task}
_tasks: dict[int, asyncio.Task] = {}


async def _run_once(user_id: int) -> bool:
    """Bir marta tarqatadi. False qaytarsa — to'xtatish kerak (obuna yo'q/tayyor emas)."""
    user = await db.get_user(user_id)
    if not user or not user["active"] or not user["session"] or not user["message"]:
        return True  # hali tayyor emas, lekin loop davom etaveradi
    if not db.subscription_ok(user["paid_until"]):
        log.info("user=%s obuna tugagan — yuborilmadi", user_id)
        return True
    chat_ids = list(await db.get_selected_group_ids(user_id))
    if not chat_ids:
        return True
    result = await userbot.broadcast(user["session"], chat_ids, user["message"])
    log.info(
        "user=%s yuborildi=%s xato=%s", user_id, result["sent"], len(result["failed"])
    )
    return True


async def _user_loop(user_id: int) -> None:
    log.info("user=%s tarqatish sikli boshlandi", user_id)
    try:
        while True:
            try:
                await _run_once(user_id)
            except PermissionError:
                # Session yaroqsiz — tarqatishni butunlay to'xtatamiz.
                log.warning("user=%s session yaroqsiz — to'xtatildi", user_id)
                await db.set_active(user_id, False)
                break
            except Exception:  # noqa: BLE001 — bitta xato sikni o'ldirmasin
                log.exception("user=%s tarqatishda xato", user_id)

            # Keyingi yuborishgacha kutamiz. Har safar bazadan o'qiladi:
            # interval o'zgarsa yoki to'xtatilsa — darhol hisobga olinadi.
            user = await db.get_user(user_id)
            if not user or not user["active"]:
                break
            interval = user["interval_seconds"] or 60
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        pass
    finally:
        # Faqat o'zimizni tozalaymiz (yangi task bilan almashtirilmagan bo'lsa).
        if _tasks.get(user_id) is asyncio.current_task():
            _tasks.pop(user_id, None)
        log.info("user=%s tarqatish sikli to'xtadi", user_id)


def add_user_job(user_id: int, interval_seconds: int) -> None:
    """Foydalanuvchi uchun tarqatish sikini boshlaydi (darhol birinchi yuborish + interval)."""
    old = _tasks.get(user_id)
    if old:
        old.cancel()
    _tasks[user_id] = asyncio.create_task(_user_loop(user_id))


def remove_user_job(user_id: int) -> None:
    task = _tasks.pop(user_id, None)
    if task:
        task.cancel()


async def run_now(user_id: int) -> None:
    """Moslik uchun — endi alohida kerak emas (loop darhol yuboradi)."""
    try:
        await _run_once(user_id)
    except Exception:  # noqa: BLE001
        log.exception("run_now xato user=%s", user_id)


async def restore_jobs() -> None:
    """Bot qayta ishga tushganda faol foydalanuvchilar tarqatishini tiklaydi."""
    for user in await db.get_active_users():
        if user["interval_seconds"]:
            add_user_job(user["user_id"], user["interval_seconds"])
    log.info("tiklandi: %s faol tarqatish", len(_tasks))


def start() -> None:
    """asyncio loop uchun alohida start kerak emas (moslik uchun qoldirilgan)."""
