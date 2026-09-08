"""Barcha bot handlerlari — doimiy (reply) menyu + ko'p tillilik."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import date, datetime

from aiogram import F, Router
from aiogram.filters import BaseFilter, Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from .. import config, db, i18n, keyboards, scheduler, userbot
from ..i18n import button_action, fmt_interval, t
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
def _parse_ref(args: str | None) -> int | None:
    """"ref_1357290180" yoki "ref_1357290180_abc" dan referrer ID ni ajratadi."""
    if not args or not args.startswith("ref_"):
        return None
    try:
        return int(args.split("_")[1])
    except (IndexError, ValueError):
        return None


async def _process_referral(message: Message, user: dict, args: str | None) -> None:
    """Birinchi /start da referralni hisoblaydi (taklif qilgan userga bonus)."""
    uid = message.from_user.id
    ref_id = _parse_ref(args)
    if ref_id and ref_id != uid and not user.get("referred_by"):
        referrer = await db.get_user(ref_id)
        if referrer:
            await db.add_subscription_days(ref_id, config.REFERRAL_DAYS)
            await db.mark_onboarded(uid, referred_by=ref_id)
            try:  # taklif qilgan userga xabar berish
                await message.bot.send_message(
                    ref_id,
                    t(referrer["lang"], "referral_earned", days=config.REFERRAL_DAYS),
                )
            except Exception:  # noqa: BLE001
                pass
            return
    await db.mark_onboarded(uid)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, command: CommandObject) -> None:
    await state.clear()
    await db.ensure_user(message.from_user.id)
    user = await db.get_user(message.from_user.id)
    lang = (user["lang"] if user else None) or "uz"

    # Referral — faqat birinchi marta start bosilganda
    if user and not user["onboarded"]:
        await _process_referral(message, user, command.args)

    await send_menu(
        message,
        t(lang, "welcome") + "\n\n" + t(lang, "trial_note", days=config.TRIAL_DAYS),
    )


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


# ============================ ADMIN: BROADCAST / E'LON ============================
def _is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


async def _broadcast(bot, users: list[dict], text_fn, kb_fn=None) -> tuple[int, int]:
    """Barcha userlarga yuboradi. Bloklagan/o'chirgan userlar o'tkazib yuboriladi."""
    sent = failed = 0
    for u in users:
        try:
            await bot.send_message(
                u["user_id"], text_fn(u),
                reply_markup=(kb_fn(u) if kb_fn else None),
            )
            sent += 1
        except Exception:  # noqa: BLE001 — bloklagan/deaktiv userlar
            failed += 1
        await asyncio.sleep(0.05)  # Telegram limitidan oshmaslik uchun (~20/sek)
    return sent, failed


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject) -> None:
    if not _is_admin(message.from_user.id):
        return
    text = command.args
    if not text and message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption
    if not text:
        await message.answer(
            "📢 Foydalanish: <code>/broadcast xabar matni</code>\n"
            "(yoki biror xabarga reply qilib /broadcast yozing)"
        )
        return
    users = await db.get_all_users()
    await message.answer(f"⏳ {len(users)} ta foydalanuvchiga yuborilyapti...")
    sent, failed = await _broadcast(message.bot, users, lambda u: text)
    await message.answer(f"✅ Yuborildi: {sent} ta\n❌ Yuborilmadi: {failed} ta")


@router.message(Command("announce_referral"))
async def cmd_announce_referral(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    users = await db.get_all_users()
    me = await message.bot.get_me()
    await message.answer(f"⏳ Referral e'loni {len(users)} ta userga yuborilyapti...")

    def _link(u):
        return f"https://t.me/{me.username}?start=ref_{u['user_id']}"

    sent, failed = await _broadcast(
        message.bot, users,
        text_fn=lambda u: t(u["lang"], "referral_announce", days=config.REFERRAL_DAYS, link=_link(u)),
        kb_fn=lambda u: keyboards.share_keyboard(u["lang"], _link(u)),
    )
    await message.answer(f"✅ Yuborildi: {sent} ta\n❌ Yuborilmadi: {failed} ta")


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

    if action == "sub":
        user = await db.get_user(uid)
        await send_menu(message, _sub_view(lang, user))
        return

    if action == "invite":
        me = await message.bot.get_me()
        link = f"https://t.me/{me.username}?start=ref_{uid}"
        count = await db.count_referrals(uid)
        await message.answer(
            t(lang, "invite_text", link=link, days=config.REFERRAL_DAYS,
              count=count, bonus=count * config.REFERRAL_DAYS),
            reply_markup=keyboards.share_keyboard(lang, link),
        )
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
        text, kb = await _templates_view(uid, lang)
        await message.answer(text, reply_markup=kb)

    elif action == "interval":
        await state.set_state(Compose.waiting_interval)
        await message.answer(
            t(lang, "interval_choose"),
            reply_markup=keyboards.interval_keyboard(lang),
        )

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


def _preview(text: str, limit: int = 120) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[:limit] + "…"


async def _templates_view(user_id: int, lang: str) -> tuple[str, object]:
    """Shablonlar menyusi matni + inline klaviaturasini qaytaradi."""
    user = await db.get_user(user_id)
    active = (user["message"] if user else None) or None
    templates = await db.list_templates(user_id)
    text = t(lang, "tpl_menu")
    if active:
        text += f"\n\n{t(lang, 'tpl_active_label')}\n<code>{_preview(active)}</code>"
    else:
        text += f"\n\n{t(lang, 'tpl_none_active')}"
    return text, keyboards.templates_keyboard(lang, templates, active)


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


def _days_left(paid_until: str | None) -> int:
    try:
        d = datetime.strptime(paid_until, "%Y-%m-%d").date()
        return max(0, (d - date.today()).days)
    except Exception:  # noqa: BLE001
        return 0


def _sub_view(lang: str, user: dict | None) -> str:
    paid = user.get("paid_until") if user else None
    admin = config.SUPPORT_USERNAME
    if db.subscription_ok(paid):
        return t(lang, "sub_active", date=paid, days=_days_left(paid), admin=admin)
    return t(lang, "sub_expired", date=paid or "—", admin=admin)


async def _do_start(message: Message, state: FSMContext, lang: str, user: dict) -> None:
    await state.clear()
    uid = message.from_user.id
    # Obuna tekshiruvi — muddat tugagan bo'lsa ishga tushirmaymiz
    if not db.subscription_ok(user["paid_until"] if user else None):
        await send_menu(message, t(lang, "expired_cant_start", admin=config.SUPPORT_USERNAME))
        return
    selected = await db.get_selected_group_ids(uid)
    problems = []
    if not user or not user["session"]:
        problems.append(t(lang, "prob_login"))
    if not user or not user["message"]:
        problems.append(t(lang, "prob_message"))
    if not user or not user["interval_seconds"]:
        problems.append(t(lang, "prob_interval"))
    if not selected:
        problems.append(t(lang, "prob_groups"))
    if problems:
        await send_menu(message, t(lang, "start_need", list=", ".join(problems)))
        return

    await db.set_active(uid, True)
    scheduler.add_user_job(uid, user["interval_seconds"])  # darhol yuboradi + interval loop
    await send_menu(
        message,
        t(lang, "started", interval=fmt_interval(lang, user["interval_seconds"]), count=len(selected)),
    )


async def _show_status(message: Message, lang: str, user: dict) -> None:
    selected = await db.get_selected_groups(message.from_user.id)
    dash = t(lang, "dash")
    msg = (user["message"] if user else None) or dash
    if len(msg) > 200:
        msg = msg[:200] + "…"
    interval = (
        fmt_interval(lang, user["interval_seconds"])
        if user and user["interval_seconds"] else dash
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
        delivery_key, code_len = await userbot.start_login(message.from_user.id, phone)
    except Exception as e:  # noqa: BLE001
        await message.answer(t(lang, "login_error", err=e))
        return

    await state.update_data(phone=phone, code_buf="", code_len=code_len, delivery_key=delivery_key)
    await state.set_state(Auth.waiting_code)
    await message.answer(
        _code_msg(lang, delivery_key, "", code_len),
        reply_markup=keyboards.code_pad(),
    )


def _code_msg(lang: str, delivery_key: str, buf: str, length: int) -> str:
    shown = " ".join(list(buf) + ["•"] * max(0, length - len(buf)))
    return (
        f"{t(lang, delivery_key)}\n\n"
        f"{t(lang, 'code_pad_prompt')}\n\n"
        f"{t(lang, 'code_label')}:  {shown}"
    )


@router.callback_query(Auth.waiting_code, F.data.startswith("cd:"))
async def cb_code_pad(cb: CallbackQuery, state: FSMContext) -> None:
    lang = await _lang(cb.from_user.id)
    data = await state.get_data()
    buf = data.get("code_buf", "")
    length = data.get("code_len", 5)
    delivery_key = data.get("delivery_key", "code_sent")
    key = cb.data.split(":", 1)[1]

    if key == "back":
        buf = buf[:-1]
    elif key.isdigit() and len(buf) < length:
        buf += key
    await state.update_data(code_buf=buf)

    # Yuborish: ✅ bosilganda yoki kod to'lganda
    if key != "ok" and len(buf) < length:
        try:
            await cb.message.edit_text(
                _code_msg(lang, delivery_key, buf, length),
                reply_markup=keyboards.code_pad(),
            )
        except Exception:  # noqa: BLE001
            pass
        await cb.answer()
        return

    if not buf:
        await cb.answer()
        return

    # Kodni tekshirish
    try:
        status, session = await userbot.confirm_code(cb.from_user.id, buf)
    except Exception as e:  # noqa: BLE001
        await state.update_data(code_buf="")
        try:
            await cb.message.edit_text(
                f"❌ {e}\n\n" + _code_msg(lang, delivery_key, "", length),
                reply_markup=keyboards.code_pad(),
            )
        except Exception:  # noqa: BLE001
            pass
        await cb.answer(t(lang, "code_empty"), show_alert=False)
        return

    if status == "password":
        await state.set_state(Auth.waiting_password)
        await cb.message.answer(t(lang, "twofa_prompt"))
        await cb.answer()
        return

    await db.set_session(cb.from_user.id, data.get("phone", ""), session)
    await state.clear()
    try:
        await cb.message.edit_text(t(lang, "login_success"))
    except Exception:  # noqa: BLE001
        pass
    await cb.message.answer(
        t(lang, "welcome"),
        reply_markup=keyboards.main_menu(lang, True),
    )
    await cb.answer()


@router.message(Auth.waiting_code)
async def on_code(message: Message, state: FSMContext) -> None:
    """Matn bilan kiritilgan kod. Bo'sh joy bilan bo'lsa ishlaydi; matn-raqam bo'lsa
    Telegram bekor qilgan bo'ladi — yangi kod yuborib, tugmalarga yo'naltiramiz."""
    uid = message.from_user.id
    lang = await _lang(uid)
    code = re.sub(r"\D", "", message.text or "")
    if not code:
        await message.answer(t(lang, "code_empty"))
        return

    try:
        status, session = await userbot.confirm_code(uid, code)
    except Exception:  # noqa: BLE001 — kod bekor bo'lgan yoki xato
        data = await state.get_data()
        phone = data.get("phone", "")
        try:
            delivery_key, code_len = await userbot.start_login(uid, phone)  # yangi kod
        except Exception as e:  # noqa: BLE001
            await message.answer(t(lang, "login_error", err=e))
            return
        await state.update_data(code_buf="", code_len=code_len, delivery_key=delivery_key)
        await message.answer(
            t(lang, "code_pasted_hint") + "\n\n" + _code_msg(lang, delivery_key, "", code_len),
            reply_markup=keyboards.code_pad(),
        )
        return

    if status == "password":
        await state.set_state(Auth.waiting_password)
        await message.answer(t(lang, "twofa_prompt"))
        return

    data = await state.get_data()
    await db.set_session(uid, data.get("phone", ""), session)
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


# ============================ XABAR SHABLONLARI ============================
@router.callback_query(F.data == "tplnew")
async def cb_tpl_new(cb: CallbackQuery, state: FSMContext) -> None:
    lang = await _lang(cb.from_user.id)
    await state.set_state(Compose.waiting_template)
    await cb.message.answer(t(lang, "tpl_prompt"))
    await cb.answer()


@router.callback_query(F.data.startswith("tpl:"))
async def cb_tpl_activate(cb: CallbackQuery, state: FSMContext) -> None:
    lang = await _lang(cb.from_user.id)
    tpl_id = int(cb.data.split(":", 1)[1])
    tp = await db.get_template(cb.from_user.id, tpl_id)
    if not tp:
        await cb.answer()
        return
    await db.set_message(cb.from_user.id, tp["text"])  # faollashtirish
    text, kb = await _templates_view(cb.from_user.id, lang)
    try:
        await cb.message.edit_text(text, reply_markup=kb)
    except Exception:  # noqa: BLE001
        pass
    await cb.answer(t(lang, "tpl_activated"))


@router.callback_query(F.data.startswith("tpldel:"))
async def cb_tpl_delete(cb: CallbackQuery, state: FSMContext) -> None:
    lang = await _lang(cb.from_user.id)
    tpl_id = int(cb.data.split(":", 1)[1])
    await db.delete_template(cb.from_user.id, tpl_id)
    text, kb = await _templates_view(cb.from_user.id, lang)
    try:
        await cb.message.edit_text(text, reply_markup=kb)
    except Exception:  # noqa: BLE001
        pass
    await cb.answer(t(lang, "tpl_deleted"))


@router.message(Compose.waiting_template)
async def on_template_text(message: Message, state: FSMContext) -> None:
    lang = await _lang(message.from_user.id)
    text = message.text or message.caption
    if not text:
        await message.answer(t(lang, "msg_empty"))
        return
    await db.add_template(message.from_user.id, text)
    await db.set_message(message.from_user.id, text)  # yangi shablonni darhol faollashtirish
    await state.clear()
    await message.answer(t(lang, "tpl_saved"))
    view_text, kb = await _templates_view(message.from_user.id, lang)
    await message.answer(view_text, reply_markup=kb)


@router.callback_query(F.data == "iv_custom")
async def cb_interval_custom(cb: CallbackQuery, state: FSMContext) -> None:
    lang = await _lang(cb.from_user.id)
    await state.set_state(Compose.waiting_interval)
    await cb.message.answer(
        t(lang, "interval_custom_prompt", min=config.MIN_INTERVAL_SECONDS)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("iv:"))
async def cb_interval_preset(cb: CallbackQuery, state: FSMContext) -> None:
    lang = await _lang(cb.from_user.id)
    seconds = int(cb.data.split(":", 1)[1])
    await db.set_interval(cb.from_user.id, seconds)
    await state.clear()
    try:
        await cb.message.edit_text(t(lang, "interval_saved", interval=fmt_interval(lang, seconds)))
    except Exception:  # noqa: BLE001
        pass
    await cb.answer(t(lang, "interval_saved", interval=fmt_interval(lang, seconds)))


@router.message(Compose.waiting_interval)
async def on_interval(message: Message, state: FSMContext) -> None:
    lang = await _lang(message.from_user.id)
    digits = re.sub(r"\D", "", message.text or "")
    if not digits:
        await message.answer(t(lang, "need_number"))
        return
    seconds = int(digits)
    if seconds < config.MIN_INTERVAL_SECONDS:
        await message.answer(t(lang, "interval_small", min=config.MIN_INTERVAL_SECONDS))
        return
    await db.set_interval(message.from_user.id, seconds)
    await state.clear()
    await send_menu(message, t(lang, "interval_saved", interval=fmt_interval(lang, seconds)))


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
