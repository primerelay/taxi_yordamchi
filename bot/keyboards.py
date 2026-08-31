"""Inline va reply klaviaturalar."""
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def main_menu(logged_in: bool, active: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if not logged_in:
        rows.append([InlineKeyboardButton(text="🔑 Akkauntga kirish", callback_data="login")])
    else:
        rows.append([InlineKeyboardButton(text="✍️ Xabarni belgilash", callback_data="set_message")])
        rows.append([InlineKeyboardButton(text="👥 Guruhlarni tanlash", callback_data="pick_groups")])
        rows.append([InlineKeyboardButton(text="⏱ Interval belgilash", callback_data="set_interval")])
        if active:
            rows.append([InlineKeyboardButton(text="⏹ To'xtatish", callback_data="stop")])
        else:
            rows.append([InlineKeyboardButton(text="▶️ Boshlash", callback_data="start")])
        rows.append([InlineKeyboardButton(text="ℹ️ Holat", callback_data="status")])
        rows.append([InlineKeyboardButton(text="🚪 Chiqish", callback_data="logout")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def phone_request() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def groups_keyboard(groups: list[dict], selected: set[int]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for g in groups:
        mark = "✅ " if g["chat_id"] in selected else "▫️ "
        rows.append([
            InlineKeyboardButton(
                text=mark + g["title"][:40],
                callback_data=f"g:{g['chat_id']}",
            )
        ])
    rows.append([InlineKeyboardButton(text="✔️ Tayyor", callback_data="groups_done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Menyu", callback_data="menu")]]
    )
