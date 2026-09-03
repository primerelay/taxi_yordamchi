"""Inline va doimiy reply klaviaturalar (ko'p tilli)."""
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from . import i18n
from .i18n import BUTTONS, LANG_NAMES, t


def _btn(action: str, lang: str) -> KeyboardButton:
    return KeyboardButton(text=BUTTONS[action][i18n.normalize(lang)])


def main_menu(lang: str, logged_in: bool) -> ReplyKeyboardMarkup:
    """Chat pastida doim turadigan asosiy menyu."""
    if not logged_in:
        rows = [[_btn("login", lang)], [_btn("lang", lang), _btn("restart", lang)]]
    else:
        rows = [
            [_btn("message", lang), _btn("groups", lang)],
            [_btn("interval", lang), _btn("status", lang)],
            [_btn("start", lang), _btn("stop", lang)],
            [_btn("lang", lang), _btn("logout", lang)],
            [_btn("restart", lang)],
        ]
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        is_persistent=True,
    )


def phone_request(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "send_phone_btn"), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"setlang:{code}")]
            for code, name in LANG_NAMES.items()
        ]
    )


def groups_keyboard(lang: str, groups: list[dict], selected: set[int]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for g in groups:
        mark = "✅ " if g["chat_id"] in selected else "▫️ "
        rows.append([
            InlineKeyboardButton(
                text=mark + g["title"][:40],
                callback_data=f"g:{g['chat_id']}",
            )
        ])
    rows.append([InlineKeyboardButton(text=t(lang, "done_btn"), callback_data="groups_done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
