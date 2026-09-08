"""SQLite ma'lumotlar bazasi (aiosqlite)."""
from __future__ import annotations

from typing import Optional

import aiosqlite

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id          INTEGER PRIMARY KEY,   -- haydovchining Telegram ID si
    phone            TEXT,
    session          TEXT,                  -- Telethon StringSession
    message          TEXT,
    interval_minutes INTEGER,               -- eski (endi ishlatilmaydi)
    interval_seconds INTEGER,
    active           INTEGER NOT NULL DEFAULT 0,
    full_name        TEXT,
    username         TEXT,
    lang             TEXT NOT NULL DEFAULT 'uz',
    last_active      TEXT,                  -- oxirgi faollik (DAU uchun)
    paid_until       TEXT,                  -- to'lov amal qilish sanasi (YYYY-MM-DD)
    referred_by      INTEGER,               -- kim taklif qilgan (referral)
    onboarded        INTEGER NOT NULL DEFAULT 0,  -- birinchi /start bosilganmi
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS selected_groups (
    user_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    title   TEXT,
    PRIMARY KEY (user_id, chat_id)
);

CREATE TABLE IF NOT EXISTS payments (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount  REAL NOT NULL,
    months  INTEGER,
    paid_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    note    TEXT
);

CREATE TABLE IF NOT EXISTS templates (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    text       TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# Mavjud bazaga yangi ustunlarni qo'shish (migratsiya).
_MIGRATIONS = {
    "full_name": "ALTER TABLE users ADD COLUMN full_name TEXT",
    "username": "ALTER TABLE users ADD COLUMN username TEXT",
    "lang": "ALTER TABLE users ADD COLUMN lang TEXT NOT NULL DEFAULT 'uz'",
    "last_active": "ALTER TABLE users ADD COLUMN last_active TEXT",
    "paid_until": "ALTER TABLE users ADD COLUMN paid_until TEXT",
    "interval_seconds": "ALTER TABLE users ADD COLUMN interval_seconds INTEGER",
    "referred_by": "ALTER TABLE users ADD COLUMN referred_by INTEGER",
    "onboarded": "ALTER TABLE users ADD COLUMN onboarded INTEGER NOT NULL DEFAULT 0",
}


async def init() -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")  # admin panel bilan bir vaqtda o'qish
        await db.executescript(_SCHEMA)
        # Eski bazalarga yetishmayotgan ustunlarni qo'shamiz.
        cur = await db.execute("PRAGMA table_info(users)")
        existing = {row[1] for row in await cur.fetchall()}
        for column, sql in _MIGRATIONS.items():
            if column not in existing:
                await db.execute(sql)
                if column == "onboarded":
                    # mavjud (eski) userlar allaqachon start bosgan — referral bermaslik uchun
                    await db.execute("UPDATE users SET onboarded = 1")
        # Obunasi umuman belgilanmagan (eski) foydalanuvchilarga bir martalik sinov.
        await db.execute(
            "UPDATE users SET paid_until = date('now', 'localtime', ?) WHERE paid_until IS NULL",
            (f"+{config.TRIAL_DAYS} days",),
        )
        # Eski interval (daqiqa) -> soniyaga o'tkazish (bir martalik).
        await db.execute(
            "UPDATE users SET interval_seconds = interval_minutes * 60 "
            "WHERE interval_seconds IS NULL AND interval_minutes IS NOT NULL"
        )
        await db.commit()


async def touch_user(
    user_id: int, full_name: str | None = None, username: str | None = None
) -> None:
    """Har bir muloqotda chaqiriladi — profilni yangilaydi va faollikni belgilaydi."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await _grant_trial_if_new(db, user_id)
        await db.execute(
            "UPDATE users SET last_active = datetime('now', 'localtime'), "
            "full_name = COALESCE(?, full_name), username = COALESCE(?, username) "
            "WHERE user_id = ?",
            (full_name, username, user_id),
        )
        await db.commit()


async def _grant_trial_if_new(db: aiosqlite.Connection, user_id: int) -> None:
    """Foydalanuvchi birinchi marta yaratilsa, unga sinov muddatini beradi."""
    cur = await db.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,)
    )
    if cur.rowcount == 1:  # yangi foydalanuvchi
        await db.execute(
            "UPDATE users SET paid_until = date('now', 'localtime', ?) WHERE user_id = ?",
            (f"+{config.TRIAL_DAYS} days", user_id),
        )


async def ensure_user(user_id: int) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await _grant_trial_if_new(db, user_id)
        await db.commit()


async def add_subscription_days(user_id: int, days: int) -> None:
    """Obunaga kun qo'shadi: paid_until = max(bugun, paid_until) + days."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "UPDATE users SET paid_until = date("
            "  CASE WHEN paid_until IS NULL OR paid_until < date('now','localtime') "
            "       THEN date('now','localtime') ELSE paid_until END, ?) "
            "WHERE user_id = ?",
            (f"+{days} days", user_id),
        )
        await db.commit()


async def mark_onboarded(user_id: int, referred_by: Optional[int] = None) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        if referred_by:
            await db.execute(
                "UPDATE users SET onboarded = 1, referred_by = ? WHERE user_id = ?",
                (referred_by, user_id),
            )
        else:
            await db.execute(
                "UPDATE users SET onboarded = 1 WHERE user_id = ?", (user_id,)
            )
        await db.commit()


async def count_referrals(user_id: int) -> int:
    async with aiosqlite.connect(config.DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM users WHERE referred_by = ?", (user_id,)
        )
        return (await cur.fetchone())[0]


def subscription_ok(paid_until: Optional[str]) -> bool:
    """Obuna amal qilyaptimi (paid_until >= bugun)."""
    if not paid_until:
        return False
    from datetime import date
    return paid_until >= date.today().isoformat()


async def get_user(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def set_session(user_id: int, phone: str, session: str) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "UPDATE users SET phone = ?, session = ? WHERE user_id = ?",
            (phone, session, user_id),
        )
        await db.commit()


async def clear_session(user_id: int) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "UPDATE users SET session = NULL, active = 0 WHERE user_id = ?",
            (user_id,),
        )
        await db.commit()


async def get_lang(user_id: int) -> str:
    async with aiosqlite.connect(config.DB_PATH) as db:
        cur = await db.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        return (row[0] if row and row[0] else "uz")


async def set_lang(user_id: int, lang: str) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
        await db.commit()


async def set_message(user_id: int, message: str) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "UPDATE users SET message = ? WHERE user_id = ?", (message, user_id)
        )
        await db.commit()


async def add_template(user_id: int, text: str) -> int:
    async with aiosqlite.connect(config.DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO templates (user_id, text) VALUES (?, ?)", (user_id, text)
        )
        await db.commit()
        return cur.lastrowid


async def list_templates(user_id: int) -> list[dict]:
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT id, text FROM templates WHERE user_id = ? ORDER BY id", (user_id,)
        )
        return [dict(r) for r in await cur.fetchall()]


async def get_template(user_id: int, tpl_id: int) -> Optional[dict]:
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT id, text FROM templates WHERE user_id = ? AND id = ?",
            (user_id, tpl_id),
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def delete_template(user_id: int, tpl_id: int) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "DELETE FROM templates WHERE user_id = ? AND id = ?", (user_id, tpl_id)
        )
        await db.commit()


async def set_interval(user_id: int, seconds: int) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "UPDATE users SET interval_seconds = ? WHERE user_id = ?",
            (seconds, user_id),
        )
        await db.commit()


async def set_active(user_id: int, active: bool) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "UPDATE users SET active = ? WHERE user_id = ?",
            (1 if active else 0, user_id),
        )
        await db.commit()


async def toggle_group(user_id: int, chat_id: int, title: str) -> bool:
    """Guruhni tanlangan/tanlanmaganga o'zgartiradi. True = endi tanlangan."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        cur = await db.execute(
            "SELECT 1 FROM selected_groups WHERE user_id = ? AND chat_id = ?",
            (user_id, chat_id),
        )
        exists = await cur.fetchone()
        if exists:
            await db.execute(
                "DELETE FROM selected_groups WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id),
            )
            await db.commit()
            return False
        await db.execute(
            "INSERT INTO selected_groups (user_id, chat_id, title) VALUES (?, ?, ?)",
            (user_id, chat_id, title),
        )
        await db.commit()
        return True


async def get_selected_group_ids(user_id: int) -> set[int]:
    async with aiosqlite.connect(config.DB_PATH) as db:
        cur = await db.execute(
            "SELECT chat_id FROM selected_groups WHERE user_id = ?", (user_id,)
        )
        rows = await cur.fetchall()
        return {r[0] for r in rows}


async def get_selected_groups(user_id: int) -> list[dict]:
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT chat_id, title FROM selected_groups WHERE user_id = ?",
            (user_id,),
        )
        return [dict(r) for r in await cur.fetchall()]


async def get_active_users() -> list[dict]:
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE active = 1")
        return [dict(r) for r in await cur.fetchall()]
