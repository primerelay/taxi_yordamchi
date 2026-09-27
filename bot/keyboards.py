"""Inline va doimiy reply klaviaturalar (ko'p tilli)."""
from urllib.parse import quote

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
        rows = [
            [_btn("login", lang)],
            [_btn("invite", lang)],
            [_btn("sub", lang), _btn("lang", lang)],
            [_btn("restart", lang)],
        ]
    else:
        rows = [
            [_btn("message", lang), _btn("groups", lang)],
            [_btn("interval", lang), _btn("status", lang)],
            [_btn("start", lang), _btn("stop", lang)],
            [_btn("invite", lang)],
            [_btn("sub", lang), _btn("lang", lang)],
            [_btn("logout", lang), _btn("restart", lang)],
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


def interval_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Tayyor interval variantlari (2 tadan qatorda)."""
    buttons = [
        InlineKeyboardButton(text=i18n.fmt_interval(lang, s), callback_data=f"iv:{s}")
        for s in i18n.INTERVAL_PRESETS
    ]
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton(text=t(lang, "interval_custom_btn"), callback_data="iv_custom")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def code_pad() -> InlineKeyboardMarkup:
    """Kod kiritish uchun raqamli klaviatura (kod chatga matn sifatida yozilmaydi)."""
    def d(n):
        return InlineKeyboardButton(text=str(n), callback_data=f"cd:{n}")
    return InlineKeyboardMarkup(inline_keyboard=[
        [d(1), d(2), d(3)],
        [d(4), d(5), d(6)],
        [d(7), d(8), d(9)],
        [
            InlineKeyboardButton(text="⌫", callback_data="cd:back"),
            d(0),
            InlineKeyboardButton(text="✅", callback_data="cd:ok"),
        ],
    ])


def share_keyboard(lang: str, link: str) -> InlineKeyboardMarkup:
    """Referral havolasini ulashish tugmasi (Telegram share dialogini ochadi)."""
    share_url = (
        "https://t.me/share/url?url=" + quote(link, safe="")
        + "&text=" + quote(t(lang, "invite_share_text"), safe="")
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t(lang, "invite_share_btn"), url=share_url)]]
    )


def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"setlang:{code}")]
            for code, name in LANG_NAMES.items()
        ]
    )


_MEDIA_ICON = {"photo": "🖼", "video": "🎬"}


def templates_keyboard(
    lang: str, templates: list[dict], active_id: int | None
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for tp in templates:
        icon = _MEDIA_ICON.get(tp.get("media_type") or "", "")
        first_line = tp["text"].splitlines()[0][:32] if tp.get("text") else ""
        label = f"{icon} {first_line}".strip() or "—"
        mark = "✅ " if active_id is not None and tp["id"] == active_id else "▫️ "
        rows.append([
            InlineKeyboardButton(text=mark + label, callback_data=f"tpl:{tp['id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"tpldel:{tp['id']}"),
        ])
    rows.append([InlineKeyboardButton(text=t(lang, "tpl_new_btn"), callback_data="tplnew")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# Bir sahifada nechta guruh ko'rsatiladi (Telegram inline-klaviatura limiti uchun).
GROUPS_PER_PAGE = 8


def groups_page_count(total: int) -> int:
    """Guruhlar soniga qarab sahifalar sonini qaytaradi (kamida 1)."""
    return max(1, (total + GROUPS_PER_PAGE - 1) // GROUPS_PER_PAGE)


def groups_keyboard(
    lang: str, groups: list[dict], selected: set[int], page: int = 0
) -> InlineKeyboardMarkup:
    """Guruhlar ro'yxati — sahifalab ko'rsatiladi (har sahifada GROUPS_PER_PAGE ta)."""
    pages = groups_page_count(len(groups))
    page = max(0, min(page, pages - 1))
    start = page * GROUPS_PER_PAGE
    chunk = groups[start:start + GROUPS_PER_PAGE]

    rows: list[list[InlineKeyboardButton]] = []
    for g in chunk:
        mark = "✅ " if g["chat_id"] in selected else "▫️ "
        rows.append([
            InlineKeyboardButton(
                text=mark + g["title"][:40],
                callback_data=f"g:{g['chat_id']}",
            )
        ])

    # Navigatsiya qatori — faqat bir nechta sahifa bo'lganda.
    if pages > 1:
        nav: list[InlineKeyboardButton] = []
        if page > 0:
            nav.append(InlineKeyboardButton(text=t(lang, "prev_btn"), callback_data=f"gpage:{page - 1}"))
        nav.append(InlineKeyboardButton(text=f"{page + 1}/{pages}", callback_data="gnop"))
        if page < pages - 1:
            nav.append(InlineKeyboardButton(text=t(lang, "next_btn"), callback_data=f"gpage:{page + 1}"))
        rows.append(nav)

    rows.append([InlineKeyboardButton(text=t(lang, "done_btn"), callback_data="groups_done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
