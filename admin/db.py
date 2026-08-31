"""Admin panel uchun ma'lumotlar bazasi so'rovlari (sync sqlite3)."""
from __future__ import annotations

import calendar
import sqlite3
from datetime import date, datetime
from typing import Optional

from . import config


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    day = min(d.day, calendar.monthrange(y, m)[1])
    return date(y, m, day)


# ------------------------------------------------------------------ statistika
def get_stats() -> dict:
    today = _today()
    month = datetime.now().strftime("%Y-%m")
    with _conn() as c:
        def scalar(sql: str, params: tuple = ()) -> float:
            row = c.execute(sql, params).fetchone()
            return row[0] if row and row[0] is not None else 0

        return {
            "total_users": scalar("SELECT COUNT(*) FROM users"),
            "dau": scalar(
                "SELECT COUNT(*) FROM users WHERE date(last_active) = ?", (today,)
            ),
            "new_today": scalar(
                "SELECT COUNT(*) FROM users WHERE date(created_at) = ?", (today,)
            ),
            "logged_in": scalar(
                "SELECT COUNT(*) FROM users WHERE session IS NOT NULL AND session <> ''"
            ),
            "mailing_now": scalar("SELECT COUNT(*) FROM users WHERE active = 1"),
            "paying": scalar(
                "SELECT COUNT(*) FROM users WHERE paid_until IS NOT NULL AND paid_until >= ?",
                (today,),
            ),
            "expired": scalar(
                "SELECT COUNT(*) FROM users WHERE paid_until IS NOT NULL AND paid_until < ?",
                (today,),
            ),
            "revenue_total": scalar("SELECT SUM(amount) FROM payments"),
            "revenue_month": scalar(
                "SELECT SUM(amount) FROM payments WHERE strftime('%Y-%m', paid_at) = ?",
                (month,),
            ),
            "payments_count": scalar("SELECT COUNT(*) FROM payments"),
        }


# ------------------------------------------------------------ foydalanuvchilar
def list_users(
    search: str = "",
    status: str = "all",
    sort: str = "last_active",
    page: int = 1,
    per_page: int = 25,
) -> tuple[list[dict], int]:
    today = _today()
    where: list[str] = []
    params: list = []

    if search:
        where.append(
            "(CAST(user_id AS TEXT) LIKE ? OR full_name LIKE ? OR username LIKE ? OR phone LIKE ?)"
        )
        like = f"%{search}%"
        params += [like, like, like, like]

    if status == "paid":
        where.append("paid_until IS NOT NULL AND paid_until >= ?")
        params.append(today)
    elif status == "expired":
        where.append("paid_until IS NOT NULL AND paid_until < ?")
        params.append(today)
    elif status == "unpaid":
        where.append("(paid_until IS NULL OR paid_until = '')")
    elif status == "mailing":
        where.append("active = 1")
    elif status == "logged_in":
        where.append("session IS NOT NULL AND session <> ''")
    elif status == "active_today":
        where.append("date(last_active) = ?")
        params.append(today)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    sort_map = {
        "last_active": "last_active DESC",
        "created_at": "created_at DESC",
        "paid_until": "paid_until DESC",
    }
    order_sql = sort_map.get(sort, "last_active DESC")

    with _conn() as c:
        total = c.execute(
            f"SELECT COUNT(*) FROM users {where_sql}", params
        ).fetchone()[0]

        offset = (page - 1) * per_page
        rows = c.execute(
            f"""
            SELECT u.*,
                   (SELECT COUNT(*) FROM selected_groups g WHERE g.user_id = u.user_id) AS groups_count
            FROM users u
            {where_sql}
            ORDER BY {order_sql}
            LIMIT ? OFFSET ?
            """,
            params + [per_page, offset],
        ).fetchall()

    users = [_decorate(dict(r), today) for r in rows]
    return users, total


def _decorate(u: dict, today: str) -> dict:
    pu = u.get("paid_until")
    if pu:
        u["pay_status"] = "paid" if pu >= today else "expired"
    else:
        u["pay_status"] = "unpaid"
    return u


def get_user(user_id: int) -> Optional[dict]:
    today = _today()
    with _conn() as c:
        row = c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            return None
        u = _decorate(dict(row), today)
        u["groups"] = [
            dict(r)
            for r in c.execute(
                "SELECT chat_id, title FROM selected_groups WHERE user_id = ?",
                (user_id,),
            ).fetchall()
        ]
        u["payments"] = [
            dict(r)
            for r in c.execute(
                "SELECT * FROM payments WHERE user_id = ? ORDER BY paid_at DESC",
                (user_id,),
            ).fetchall()
        ]
        u["paid_total"] = sum(p["amount"] for p in u["payments"])
        return u


# -------------------------------------------------------------------- to'lovlar
def set_paid_until(user_id: int, paid_until: str) -> None:
    with _conn() as c:
        c.execute(
            "UPDATE users SET paid_until = ? WHERE user_id = ?",
            (paid_until or None, user_id),
        )
        c.commit()


def add_payment(
    user_id: int, amount: float, months: int, note: str = ""
) -> None:
    """To'lovni qayd etadi va paid_until sanasini months ga uzaytiradi."""
    today = date.today()
    with _conn() as c:
        row = c.execute(
            "SELECT paid_until FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        current = row["paid_until"] if row else None
        base = today
        if current:
            try:
                cur_date = datetime.strptime(current, "%Y-%m-%d").date()
                if cur_date > today:
                    base = cur_date
            except ValueError:
                pass
        new_until = add_months(base, months) if months else base
        c.execute(
            "INSERT INTO payments (user_id, amount, months, note) VALUES (?, ?, ?, ?)",
            (user_id, amount, months, note),
        )
        c.execute(
            "UPDATE users SET paid_until = ? WHERE user_id = ?",
            (new_until.isoformat(), user_id),
        )
        c.commit()


def list_payments(
    date_from: str = "", date_to: str = ""
) -> tuple[list[dict], float]:
    where: list[str] = []
    params: list = []
    if date_from:
        where.append("date(p.paid_at) >= ?")
        params.append(date_from)
    if date_to:
        where.append("date(p.paid_at) <= ?")
        params.append(date_to)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    with _conn() as c:
        rows = c.execute(
            f"""
            SELECT p.*, u.full_name, u.username, u.phone
            FROM payments p
            LEFT JOIN users u ON u.user_id = p.user_id
            {where_sql}
            ORDER BY p.paid_at DESC
            """,
            params,
        ).fetchall()
    payments = [dict(r) for r in rows]
    total = sum(p["amount"] for p in payments)
    return payments, total
