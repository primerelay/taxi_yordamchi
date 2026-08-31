"""Barcha bot handlerlari."""
from __future__ import annotations

import asyncio
import logging
import re

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from .. import config, db, keyboards, scheduler, userbot
from ..states import Auth, Compose

log = logging.getLogger(__name__)
router = Router()


# ------------------------------------------------------------------ helpers
async def show_menu(target: Message | CallbackQuery, text: str | None = None) -> None:
    user_id = target.from_user.id
    user = await db.get_user(user_id)
    logged_in = bool(user and user["session"])
    active = bool(user and user["active"])
    body = text or (
        "🚕 <b>Taxi Yordamchi</b>\n\n"
        "Xabaringizni belgilang, guruhlarni tanlang, intervalni sozlang "
        "va «Boshlash» tugmasini bosing."
    )
    kb = keyboards.main_menu(logged_in, active)
    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(body, reply_markup=kb)
        except Exception:  # noqa: BLE001 — bir xil matnni tahrirlashda xato bo'lishi mumkin
            await target.message.answer(body, reply_markup=kb)
    else:
        await target.answer(body, reply_markup=kb)


# --------------------------------------------------------------------- start
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await db.ensure_user(message.from_user.id)
    await show_menu(message)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await userbot.cancel_login(message.from_user.id)
    await show_menu(message, "Bekor qilindi.")


@router.callback_query(F.data == "menu")
async def cb_menu(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show_menu(cb)
    await cb.answer()


# ---------------------------------------------------------------- login flow
@router.callback_query(F.data == "login")
async def cb_login(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Auth.waiting_phone)
    await cb.message.answer(
        "📱 Telefon raqamingizni yuboring (pastdagi tugma orqali) "
        "yoki +998... ko'rinishida yozing.",
        reply_markup=keyboards.phone_request(),
    )
    await cb.answer()


@router.message(Auth.waiting_phone)
async def on_phone(message: Message, state: FSMContext) -> None:
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = (message.text or "").strip()
    if not re.match(r"^\+?\d{7,15}$", phone):
        await message.answer("❌ Raqam noto'g'ri. Masalan: +998901234567")
        return
    if not phone.startswith("+"):
        phone = "+" + phone

    await message.answer("⏳ Kod yuborilmoqda...")
    try:
        await userbot.start_login(message.from_user.id, phone)
    except Exception as e:  # noqa: BLE001
        await message.answer(f"❌ Xatolik: {e}\n/cancel bosing.")
        return

    await state.update_data(phone=phone)
    await state.set_state(Auth.waiting_code)
    await message.answer(
        "✉️ Telegramga kelgan kodni kiriting.\n\n"
        "⚠️ <b>Muhim:</b> kodni raqamlar orasiga bo'sh joy qo'yib yozing, "
        "masalan <code>1 2 3 4 5</code> — aks holda Telegram kodni bekor qilishi mumkin."
    )


@router.message(Auth.waiting_code)
async def on_code(message: Message, state: FSMContext) -> None:
    code = re.sub(r"\D", "", message.text or "")
    if not code:
        await message.answer("❌ Kod topilmadi. Qayta kiriting.")
        return
    try:
        status, session = await userbot.confirm_code(message.from_user.id, code)
    except Exception as e:  # noqa: BLE001
        await message.answer(f"❌ Kod xato yoki eskirgan: {e}\n/cancel bosib qayta urinib ko'ring.")
        return

    if status == "password":
        await state.set_state(Auth.waiting_password)
        await message.answer("🔐 Akkauntda ikki bosqichli parol bor. Parolni kiriting:")
        return

    data = await state.get_data()
    await db.set_session(message.from_user.id, data.get("phone", ""), session)
    await state.clear()
    await message.answer("✅ Muvaffaqiyatli kirdingiz!")
    await show_menu(message)


@router.message(Auth.waiting_password)
async def on_password(message: Message, state: FSMContext) -> None:
    try:
        session = await userbot.confirm_password(message.from_user.id, message.text or "")
    except Exception as e:  # noqa: BLE001
        await message.answer(f"❌ Parol xato: {e}\nQayta kiriting yoki /cancel bosing.")
        return
    data = await state.get_data()
    await db.set_session(message.from_user.id, data.get("phone", ""), session)
    await state.clear()
    await message.answer("✅ Muvaffaqiyatli kirdingiz!")
    await show_menu(message)


@router.callback_query(F.data == "logout")
async def cb_logout(cb: CallbackQuery, state: FSMContext) -> None:
    scheduler.remove_user_job(cb.from_user.id)
    await db.clear_session(cb.from_user.id)
    await show_menu(cb, "🚪 Chiqdingiz. Session o'chirildi.")
    await cb.answer()


# ------------------------------------------------------------------- message
@router.callback_query(F.data == "set_message")
async def cb_set_message(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Compose.waiting_message)
    await cb.message.answer("✍️ Guruhlarga yuboriladigan xabar matnini yuboring:")
    await cb.answer()


@router.message(Compose.waiting_message)
async def on_message_text(message: Message, state: FSMContext) -> None:
    text = message.text or message.caption
    if not text:
        await message.answer("❌ Iltimos, matn yuboring.")
        return
    await db.set_message(message.from_user.id, text)
    await state.clear()
    await message.answer("✅ Xabar saqlandi.")
    await show_menu(message)


# -------------------------------------------------------------------- groups
@router.callback_query(F.data == "pick_groups")
async def cb_pick_groups(cb: CallbackQuery, state: FSMContext) -> None:
    user = await db.get_user(cb.from_user.id)
    if not user or not user["session"]:
        await cb.answer("Avval akkauntga kiring", show_alert=True)
        return
    await cb.answer("⏳ Guruhlar yuklanmoqda...")
    try:
        groups = await userbot.get_groups(user["session"])
    except PermissionError:
        await db.clear_session(cb.from_user.id)
        await show_menu(cb, "❌ Session eskirgan. Qayta kiring.")
        return
    except Exception as e:  # noqa: BLE001
        await cb.message.answer(f"❌ Guruhlarni olishda xato: {e}")
        return

    if not groups:
        await cb.message.answer("Sizda guruhlar topilmadi.")
        return

    await state.update_data(groups=groups)
    selected = await db.get_selected_group_ids(cb.from_user.id)
    await cb.message.answer(
        "👥 Guruhlarni tanlang (belgilash uchun bosing), so'ng «Tayyor»:",
        reply_markup=keyboards.groups_keyboard(groups, selected),
    )


@router.callback_query(F.data.startswith("g:"))
async def cb_toggle_group(cb: CallbackQuery, state: FSMContext) -> None:
    chat_id = int(cb.data[2:])
    data = await state.get_data()
    groups = data.get("groups", [])
    title = next((g["title"] for g in groups if g["chat_id"] == chat_id), str(chat_id))
    await db.toggle_group(cb.from_user.id, chat_id, title)
    selected = await db.get_selected_group_ids(cb.from_user.id)
    try:
        await cb.message.edit_reply_markup(
            reply_markup=keyboards.groups_keyboard(groups, selected)
        )
    except Exception:  # noqa: BLE001
        pass
    await cb.answer()


@router.callback_query(F.data == "groups_done")
async def cb_groups_done(cb: CallbackQuery, state: FSMContext) -> None:
    selected = await db.get_selected_groups(cb.from_user.id)
    await show_menu(cb, f"✅ {len(selected)} ta guruh tanlandi.")
    await cb.answer()


# ------------------------------------------------------------------ interval
@router.callback_query(F.data == "set_interval")
async def cb_set_interval(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Compose.waiting_interval)
    await cb.message.answer(
        f"⏱ Interval necha daqiqada bo'lsin? Raqam yuboring "
        f"(eng kam {config.MIN_INTERVAL_MINUTES} daqiqa)."
    )
    await cb.answer()


@router.message(Compose.waiting_interval)
async def on_interval(message: Message, state: FSMContext) -> None:
    try:
        minutes = int(re.sub(r"\D", "", message.text or ""))
    except ValueError:
        await message.answer("❌ Raqam kiriting.")
        return
    if minutes < config.MIN_INTERVAL_MINUTES:
        await message.answer(
            f"❌ Eng kam interval {config.MIN_INTERVAL_MINUTES} daqiqa "
            f"(akkaunt xavfsizligi uchun)."
        )
        return
    await db.set_interval(message.from_user.id, minutes)
    await state.clear()
    await message.answer(f"✅ Interval: har {minutes} daqiqada.")
    await show_menu(message)


# ------------------------------------------------------------- start / stop
@router.callback_query(F.data == "start")
async def cb_start(cb: CallbackQuery, state: FSMContext) -> None:
    user = await db.get_user(cb.from_user.id)
    selected = await db.get_selected_group_ids(cb.from_user.id)
    problems = []
    if not user or not user["session"]:
        problems.append("akkauntga kirmagansiz")
    if not user or not user["message"]:
        problems.append("xabar belgilanmagan")
    if not user or not user["interval_minutes"]:
        problems.append("interval belgilanmagan")
    if not selected:
        problems.append("guruh tanlanmagan")
    if problems:
        await cb.answer("Avval: " + ", ".join(problems), show_alert=True)
        return

    await db.set_active(cb.from_user.id, True)
    scheduler.add_user_job(cb.from_user.id, user["interval_minutes"])
    # Birinchi tarqatishni darhol fonda ishga tushiramiz.
    asyncio.create_task(scheduler.run_now(cb.from_user.id))
    await show_menu(
        cb,
        f"▶️ Ishga tushdi! Har {user['interval_minutes']} daqiqada "
        f"{len(selected)} ta guruhga yuboriladi.",
    )
    await cb.answer()


@router.callback_query(F.data == "stop")
async def cb_stop(cb: CallbackQuery, state: FSMContext) -> None:
    scheduler.remove_user_job(cb.from_user.id)
    await db.set_active(cb.from_user.id, False)
    await show_menu(cb, "⏹ To'xtatildi.")
    await cb.answer()


@router.callback_query(F.data == "status")
async def cb_status(cb: CallbackQuery, state: FSMContext) -> None:
    user = await db.get_user(cb.from_user.id)
    selected = await db.get_selected_groups(cb.from_user.id)
    msg = (user["message"] if user else None) or "—"
    if len(msg) > 200:
        msg = msg[:200] + "…"
    text = (
        "ℹ️ <b>Holat</b>\n\n"
        f"Akkaunt: {'✅ kirgan' if user and user['session'] else '❌ yo‘q'}\n"
        f"Interval: {user['interval_minutes'] if user and user['interval_minutes'] else '—'} daqiqa\n"
        f"Guruhlar: {len(selected)} ta\n"
        f"Holat: {'▶️ ishlayapti' if user and user['active'] else '⏹ to‘xtatilgan'}\n\n"
        f"Xabar:\n<code>{msg}</code>"
    )
    await show_menu(cb, text)
    await cb.answer()
