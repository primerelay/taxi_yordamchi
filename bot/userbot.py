"""Telethon userbot qatlami — haydovchining o'z akkaunti orqali ishlaydi."""
from __future__ import annotations

import asyncio
import logging

from telethon import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from telethon.sessions import StringSession

from . import config

log = logging.getLogger(__name__)

# Login jarayonida (kod kutilayotganda) mijozlar shu yerda saqlanadi.
# {user_id: (client, phone, phone_code_hash)}
_login_clients: dict[int, tuple[TelegramClient, str, str]] = {}


def _new_client(session: str = "") -> TelegramClient:
    return TelegramClient(StringSession(session), config.API_ID, config.API_HASH)


# ---------------------------------------------------------------- login flow
async def start_login(user_id: int, phone: str) -> None:
    """Telefon raqamiga Telegram tasdiqlash kodini yuboradi."""
    # Oldingi urinish qolgan bo'lsa tozalaymiz.
    await cancel_login(user_id)

    client = _new_client()
    await client.connect()
    sent = await client.send_code_request(phone)
    _login_clients[user_id] = (client, phone, sent.phone_code_hash)


async def confirm_code(user_id: int, code: str) -> tuple[str, str | None]:
    """
    Kodni tekshiradi.
    Qaytaradi: ("ok", session_str) yoki ("password", None) — 2FA kerak bo'lsa.
    """
    client, phone, phone_code_hash = _login_clients[user_id]
    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
    except SessionPasswordNeededError:
        return "password", None

    session_str = client.session.save()
    await _finish_login(user_id, client)
    return "ok", session_str


async def confirm_password(user_id: int, password: str) -> str:
    """2FA parolini tekshiradi va session stringni qaytaradi."""
    client, _phone, _hash = _login_clients[user_id]
    await client.sign_in(password=password)
    session_str = client.session.save()
    await _finish_login(user_id, client)
    return session_str


async def _finish_login(user_id: int, client: TelegramClient) -> None:
    await client.disconnect()
    _login_clients.pop(user_id, None)


async def cancel_login(user_id: int) -> None:
    entry = _login_clients.pop(user_id, None)
    if entry:
        try:
            await entry[0].disconnect()
        except Exception:  # noqa: BLE001
            pass


def is_awaiting_password(user_id: int) -> bool:
    return user_id in _login_clients


# ------------------------------------------------------------- groups & send
async def get_groups(session: str) -> list[dict]:
    """Foydalanuvchi a'zo bo'lgan guruhlar ro'yxati."""
    client = _new_client(session)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            raise PermissionError("session yaroqsiz")
        groups: list[dict] = []
        async for dialog in client.iter_dialogs():
            # Faqat guruhlar (oddiy va super-guruhlar).
            if dialog.is_group:
                groups.append({"chat_id": dialog.id, "title": dialog.name or str(dialog.id)})
        return groups
    finally:
        await client.disconnect()


async def broadcast(session: str, chat_ids: list[int], text: str) -> dict:
    """
    Berilgan guruhlarga xabar yuboradi.
    Guruhlar orasida kechikish qo'yiladi, FloodWait boshqariladi.
    Qaytaradi: {"sent": int, "failed": [(chat_id, sabab), ...]}
    """
    client = _new_client(session)
    await client.connect()
    sent = 0
    failed: list[tuple[int, str]] = []
    try:
        if not await client.is_user_authorized():
            raise PermissionError("session yaroqsiz")

        for chat_id in chat_ids:
            try:
                await client.send_message(chat_id, text)
                sent += 1
            except FloodWaitError as e:
                # Telegram kutishni talab qildi — kutamiz va qayta urinamiz.
                log.warning("FloodWait %ss (chat %s)", e.seconds, chat_id)
                await asyncio.sleep(e.seconds + 1)
                try:
                    await client.send_message(chat_id, text)
                    sent += 1
                except Exception as e2:  # noqa: BLE001
                    failed.append((chat_id, str(e2)))
            except Exception as e:  # noqa: BLE001
                failed.append((chat_id, str(e)))

            await asyncio.sleep(config.SEND_DELAY_SECONDS)
    finally:
        await client.disconnect()

    return {"sent": sent, "failed": failed}
