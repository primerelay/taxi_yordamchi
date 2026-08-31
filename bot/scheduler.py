"""Interval bo'yicha xabar tarqatuvchi rejalashtiruvchi (APScheduler)."""
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from . import db, userbot

log = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler()


def _job_id(user_id: int) -> str:
    return f"mail:{user_id}"


async def _run_broadcast(user_id: int) -> None:
    """Bitta foydalanuvchi uchun bir marta tarqatish (interval har safar chaqiradi)."""
    user = await db.get_user(user_id)
    if not user or not user["active"] or not user["session"] or not user["message"]:
        return
    chat_ids = list(await db.get_selected_group_ids(user_id))
    if not chat_ids:
        return
    try:
        result = await userbot.broadcast(user["session"], chat_ids, user["message"])
        log.info(
            "user=%s yuborildi=%s xato=%s",
            user_id, result["sent"], len(result["failed"]),
        )
    except PermissionError:
        # Session yaroqsiz — tarqatishni to'xtatamiz.
        log.warning("user=%s session yaroqsiz, to'xtatildi", user_id)
        await db.set_active(user_id, False)
        remove_user_job(user_id)
    except Exception:  # noqa: BLE001
        log.exception("user=%s tarqatishda xato", user_id)


def add_user_job(user_id: int, interval_minutes: int) -> None:
    _scheduler.add_job(
        _run_broadcast,
        trigger="interval",
        minutes=interval_minutes,
        id=_job_id(user_id),
        args=[user_id],
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        next_run_time=None,  # birinchi yuborish interval o'tgach
    )


def remove_user_job(user_id: int) -> None:
    try:
        _scheduler.remove_job(_job_id(user_id))
    except Exception:  # noqa: BLE001
        pass


async def restore_jobs() -> None:
    """Bot qayta ishga tushganda faol foydalanuvchilar ishini tiklaydi."""
    for user in await db.get_active_users():
        if user["interval_minutes"]:
            add_user_job(user["user_id"], user["interval_minutes"])
    log.info("tiklandi: %s faol job", len(_scheduler.get_jobs()))


async def run_now(user_id: int) -> None:
    """Darhol bir marta tarqatish (Boshlash bosilganda birinchi yuborish)."""
    await _run_broadcast(user_id)


def start() -> None:
    _scheduler.start()
