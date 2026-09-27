"""Foydalanuvchi faolligini kuzatuvchi middleware (DAU va profil uchun)."""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from . import db


class ActivityMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        chat = data.get("event_chat")
        # Faqat shaxsiy chatdagi (haydovchi) foydalanuvchilarni hisobga olamiz —
        # admin guruhdagi xabarlar DAU/user statistikasini ifloslantirmasin.
        if user and not user.is_bot and (chat is None or chat.type == "private"):
            await db.touch_user(user.id, user.full_name, user.username)
        return await handler(event, data)
