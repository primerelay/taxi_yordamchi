"""
Interaktiv userbot login (terminal orqali).

Nega kerak: kodni bot chatiga yozganda Telegram uni ba'zan bekor qiladi.
Bu skript kodni TERMINALDA so'raydi — shuning uchun ishonchliroq.

Ishlatish:
    ./.venv/bin/python login.py

Bosqichlar:
  1) Telefon raqamini kiritasiz (+998...)
  2) Telegram ILOVASIGA kelgan kodni TERMINALGA kiritasiz
  3) (agar bo'lsa) 2FA parolni kiritasiz
  4) Botdagi Telegram ID ni kiritasiz (botga /id yozib olasiz)
     -> sessiya bazaga saqlanadi va bot avtomatik "kirgan" bo'ladi
"""
import asyncio
from getpass import getpass

from telethon import TelegramClient
from telethon.sessions import StringSession

from bot import config, db


async def main() -> None:
    print("=" * 50)
    print("  Taxi Yordamchi — userbot terminal login")
    print("=" * 50)

    phone = input("\n📱 1) TELEFON raqamingiz (+998...): ").strip()

    client = TelegramClient(StringSession(), config.API_ID, config.API_HASH)
    # Har bir bosqichni aniq o'zbekcha so'rov bilan olamiz (chalkashmaslik uchun).
    await client.start(
        phone=lambda: phone,
        code_callback=lambda: input(
            "✉️ 2) Telegram ilovasiga (777000) kelgan KODni kiriting: "
        ).strip(),
        password=lambda: getpass(
            "🔐 3) 2FA parolingiz (bo'lmasa shunchaki Enter): "
        ),
    )

    me = await client.get_me()
    session_str = client.session.save()

    print("\n✅ Muvaffaqiyatli kirdingiz!")
    print(f"   Ism : {me.first_name or ''} {me.last_name or ''}".rstrip())
    print(f"   Tel : {me.phone}")
    print(f"   User: @{me.username}" if me.username else "")

    uid = input(
        "\n🆔 4) Botdagi Telegram ID ni kiriting (botga /id yozib oling)\n"
        "[Enter bosilsa faqat sessiya chop etiladi]: "
    ).strip()

    if uid:
        await db.init()
        await db.ensure_user(int(uid))
        await db.set_session(int(uid), me.phone or "", session_str)
        print(f"\n💾 Sessiya bazaga saqlandi (user_id={uid}).")
        print("   Endi botga o'ting va to'g'ridan-to'g'ri:")
        print("   ✍️ Xabar → 👥 Guruhlar → ⏱ Interval → ▶️ Boshlash")
    else:
        print("\n📋 SESSION (xohlasangiz saqlab qo'ying):")
        print(session_str)

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
