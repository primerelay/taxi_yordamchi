"""Barcha bot handlerlari — doimiy (reply) menyu + ko'p tillilik."""
from __future__ import annotations

import asyncio
import logging
import re

from aiogram import F, Router
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from .. import config, db, i18n, keyboards, scheduler, userbot
from ..i18n import button_action, t
from ..states import Auth, Compose

log = logging.getLogger(__name__)
router = Router()


# --------------------------------------------------- menyu tugmasi filtri
class MenuButton(BaseFilter):
    """Har qanday tildagi menyu tugmasini aniqlaydi va 'action' ni inject qiladi."""

    async def __call__(self, message: Message) -> bool | dict:
        action = button_action(message.text)
        return {"action": action} if action else False


# ------------------------------------------------------------------ helpers
async def send_menu(message: Message, text: str) -> None:
    user = await db.get_user(message.from_user.id)
    lang = (user["lang"] if user else None) or "uz"
    logged_in = bool(user and user["session"])
    await message.answer(text, reply_markup=keyboards.main_menu(lang, logged_in))


async def _lang(user_id: int) -> str:
    return await db.get_lang(user_id)


# --------------------------------------------------------------------- start
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await db.ensure_user(message.from_user.id)
    lang = await _lang(message.from_user.id)
    await send_menu(message, t(lang, "welcome"))


@router.message(Command("id"))
async def cmd_id(message: Message) -> None:
    lang = await _lang(message.from_user.id)
    await message.answer(t(lang, "id_text", id=message.from_user.id))


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await userbot.cancel_login(message.from_user.id)
    lang = await _lang(message.from_user.id)
    await send_menu(message, t(lang, "cancelled"))


# ============================ MENYU TUGMALARI (doim ishlaydi) ============================
@router.message(MenuButton())
async def on_menu(message: Message, state: FSMContext, action: str) -> None:
    uid = message.from_user.id
    lang = await _lang(uid)
    await state.clear()  # menyu tugmasi bosilsa har qanday jarayon bekor bo'ladi

    if action == "restart":
        await db.ensure_user(uid)
        await send_menu(message, t(lang, "welcome"))
        return

    if action == "lang":
        await message.answer(t(lang, "lang_prompt"), reply_markup=keyboards.lang_keyboard())
        return

    if action == "login":
        await state.set_state(Auth.waiting_phone)
        await message.answer(t(lang, "login_prompt"), reply_markup=keyboards.phone_request(lang))
        return

    if action == "logout":
        await state.clear()
        scheduler.remove_user_job(uid)
        await db.clear_session(uid)
        await send_menu(message, t(lang, "logged_out"))
        return

    # Quyidagilar uchun akkaunt kerak
    user = await db.get_user(uid)
    if action in ("message", "interval", "groups", "start") and not (user and user["session"]):
        await send_menu(message, t(lang, "need_login"))
        return

    if action == "message":
        await state.set_state(Compose.waiting_message)
        await message.answer(t(lang, "msg_prompt"))

    elif action == "interval":
        await state.set_state(Compose.waiting_interval)
        await message.answer(t(lang, "interval_prompt", min=config.MIN_INTERVAL_MINUTES))

    elif action == "groups":
        await _open_groups(message, state, lang, user)

    elif action == "start":
        await _do_start(message, state, lang, user)

    elif action == "stop":
        await state.clear()
        scheduler.remove_user_job(uid)
        await db.set_active(uid, False)
        await send_menu(message, t(lang, "stopped"))

    elif action == "status":
        await _show_status(message, lang, user)


async def _open_groups(message: Message, state: FSMContext, lang: str, user: dict) -> None:
    await state.clear()
    loading = await message.answer(t(lang, "groups_loading"))
    try:
        groups = await userbot.get_groups(user["session"])
    except PermissionError:
        await db.clear_session(message.from_user.id)
        await send_menu(message, t(lang, "session_expired"))
        return
    except Exception as e:  # noqa: BLE001
        await loading.edit_text(t(lang, "groups_error", err=e))
        return
    if not groups:
        await loading.edit_text(t(lang, "no_groups"))
        return
    await state.update_data(groups=groups)
    selected = await db.get_selected_group_ids(message.from_user.id)
    await loading.edit_text(
        t(lang, "groups_select"),
        reply_markup=keyboards.groups_keyboard(lang, groups, selected),
    )


async def _do_start(message: Message, state: FSMContext, lang: str, user: dict) -> None:
    await state.clear()
    uid = message.from_user.id
    selected = await db.get_selected_group_ids(uid)
    problems = []
    if not user or not user["session"]:
        problems.append(t(lang, "prob_login"))
    if not user or not user["message"]:
        problems.append(t(lang, "prob_message"))
    if not user or not user["interval_minutes"]:
        problems.append(t(lang, "prob_interval"))
    if not selected:
        problems.append(t(lang, "prob_groups"))
    if problems:
        await send_menu(message, t(lang, "start_need", list=", ".join(problems)))
        return

    await db.set_active(uid, True)
    scheduler.add_user_job(uid, user["interval_minutes"])
    asyncio.create_task(scheduler.run_now(uid))
    await send_menu(
        message,
        t(lang, "started", min=user["interval_minutes"], count=len(selected)),
    )


async def _show_status(message: Message, lang: str, user: dict) -> None:
    selected = await db.get_selected_groups(message.from_user.id)
    dash = t(lang, "dash")
    msg = (user["message"] if user else None) or dash
    if len(msg) > 200:
        msg = msg[:200] + "…"
    interval = (
        f"{user['interval_minutes']} {t(lang, 'min_word')}"
        if user and user["interval_minutes"] else dash
    )
    await send_menu(
        message,
        t(
            lang, "status",
            acc=t(lang, "acc_yes") if user and user["session"] else t(lang, "acc_no"),
            interval=interval,
            groups=len(selected),
            state=t(lang, "state_on") if user and user["active"] else t(lang, "state_off"),
            msg=msg,
        ),
    )


# ============================ TIL TANLASH (inline) ============================
@router.callback_query(F.data.startswith("setlang:"))
async def cb_setlang(cb: CallbackQuery, state: FSMContext) -> None:
    lang = cb.data.split(":", 1)[1]
    await db.set_lang(cb.from_user.id, i18n.normalize(lang))
    try:
        await cb.message.delete()
    except Exception:  # noqa: BLE001
        pass
    user = await db.get_user(cb.from_user.id)
    await cb.message.answer(
        t(lang, "lang_changed"),
        reply_markup=keyboards.main_menu(lang, bool(user and user["session"])),
    )
    await cb.answer()


# ============================ AUTH JARAYONI (state) ============================
@router.message(Auth.waiting_phone)
async def on_phone(message: Message, state: FSMContext) -> None:
    lang = await _lang(message.from_user.id)
    phone = message.contact.phone_number if message.contact else (message.text or "").strip()
    if not re.match(r"^\+?\d{7,15}$", phone):
        await message.answer(t(lang, "phone_invalid"))
        return
    if not phone.startswith("+"):
        phone = "+" + phone

    await message.answer(t(lang, "sending_code"))
    try:
        delivery_key = await userbot.start_login(message.from_user.id, phone)
    except Exception as e:  # noqa: BLE001
        await message.answer(t(lang, "login_error", err=e))
        return

    await state.update_data(phone=phone)
    await state.set_state(Auth.waiting_code)
    await message.answer(f"{t(lang, delivery_key)}\n\n{t(lang, 'code_prompt')}")


@router.message(Auth.waiting_code)
async def on_code(message: Message, state: FSMContext) -> None:
    lang = await _lang(message.from_user.id)
    code = re.sub(r"\D", "", message.text or "")
    if not code:
        await message.answer(t(lang, "code_empty"))
        return
    try:
        status, session = await userbot.confirm_code(message.from_user.id, code)
    except Exception as e:  # noqa: BLE001
        await message.answer(t(lang, "code_error", err=e))
        return

    if status == "password":
        await state.set_state(Auth.waiting_password)
        await message.answer(t(lang, "twofa_prompt"))
        return

    data = await state.get_data()
    await db.set_session(message.from_user.id, data.get("phone", ""), session)
    await state.clear()
    await send_menu(message, t(lang, "login_success"))


@router.message(Auth.waiting_password)
async def on_password(message: Message, state: FSMContext) -> None:
    lang = await _lang(message.from_user.id)
    try:
        session = await userbot.confirm_password(message.from_user.id, message.text or "")
    except Exception as e:  # noqa: BLE001
        await message.answer(t(lang, "password_error", err=e))
        return
    data = await state.get_data()
    await db.set_session(message.from_user.id, data.get("phone", ""), session)
    await state.clear()
    await send_menu(message, t(lang, "login_success"))


# ============================ MATN KIRITISH (state) ============================
@router.message(Compose.waiting_message)
async def on_message_text(message: Message, state: FSMContext) -> None:
    lang = await _lang(message.from_user.id)
    text = message.text or message.caption
    if not text:
        await message.answer(t(lang, "msg_empty"))
        return
    await db.set_message(message.from_user.id, text)
    await state.clear()
    await send_menu(message, t(lang, "msg_saved"))


@router.message(Compose.waiting_interval)
async def on_interval(message: Message, state: FSMContext) -> None:
    lang = await _lang(message.from_user.id)
    digits = re.sub(r"\D", "", message.text or "")
    if not digits:
        await message.answer(t(lang, "need_number"))
        return
    minutes = int(digits)
    if minutes < config.MIN_INTERVAL_MINUTES:
        await message.answer(t(lang, "interval_small", min=config.MIN_INTERVAL_MINUTES))
        return
    await db.set_interval(message.from_user.id, minutes)
    await state.clear()
    await send_menu(message, t(lang, "interval_saved", min=minutes))


# ============================ GURUH TANLASH (inline) ============================
@router.callback_query(F.data.startswith("g:"))
async def cb_toggle_group(cb: CallbackQuery, state: FSMContext) -> None:
    lang = await _lang(cb.from_user.id)
    chat_id = int(cb.data[2:])
    data = await state.get_data()
    groups = data.get("groups", [])
    title = next((g["title"] for g in groups if g["chat_id"] == chat_id), str(chat_id))
    await db.toggle_group(cb.from_user.id, chat_id, title)
    selected = await db.get_selected_group_ids(cb.from_user.id)
    try:
        await cb.message.edit_reply_markup(
            reply_markup=keyboards.groups_keyboard(lang, groups, selected)
        )
    except Exception:  # noqa: BLE001
        pass
    await cb.answer()


@router.callback_query(F.data == "groups_done")
async def cb_groups_done(cb: CallbackQuery, state: FSMContext) -> None:
    lang = await _lang(cb.from_user.id)
    selected = await db.get_selected_groups(cb.from_user.id)
    try:
        await cb.message.edit_text(t(lang, "groups_done", count=len(selected)))
    except Exception:  # noqa: BLE001
        pass
    await cb.answer()


# ============================ FALLBACK ============================
@router.message()
async def fallback(message: Message, state: FSMContext) -> None:
    lang = await _lang(message.from_user.id)
    await send_menu(message, t(lang, "fallback"))
