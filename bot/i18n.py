"""Ko'p tilli matnlar (O'zbek / Rus / English). Default — O'zbek."""
from __future__ import annotations

DEFAULT_LANG = "uz"
LANGS = ("uz", "ru", "en")

LANG_NAMES = {
    "uz": "🇺🇿 O'zbekcha",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
}

# ------------------------------------------------ menyu tugmalari (action -> til)
BUTTONS: dict[str, dict[str, str]] = {
    "message":  {"uz": "✍️ Xabar",            "ru": "✍️ Сообщение",      "en": "✍️ Message"},
    "groups":   {"uz": "👥 Guruhlar",         "ru": "👥 Группы",         "en": "👥 Groups"},
    "interval": {"uz": "⏱ Interval",          "ru": "⏱ Интервал",       "en": "⏱ Interval"},
    "status":   {"uz": "ℹ️ Holat",            "ru": "ℹ️ Статус",         "en": "ℹ️ Status"},
    "start":    {"uz": "▶️ Boshlash",         "ru": "▶️ Запустить",      "en": "▶️ Start"},
    "stop":     {"uz": "⏹ To'xtatish",        "ru": "⏹ Остановить",      "en": "⏹ Stop"},
    "login":    {"uz": "🔑 Akkauntga kirish",  "ru": "🔑 Войти",          "en": "🔑 Log in"},
    "logout":   {"uz": "🚪 Chiqish",          "ru": "🚪 Выйти",          "en": "🚪 Log out"},
    "lang":     {"uz": "🌐 Til",              "ru": "🌐 Язык",           "en": "🌐 Language"},
    "restart":  {"uz": "🔄 Qayta boshlash",   "ru": "🔄 Перезапуск",     "en": "🔄 Restart"},
}

# ------------------------------------------------------------------- matnlar
TEXTS: dict[str, dict[str, str]] = {
    "welcome": {
        "uz": "🚕 <b>Taxi Yordamchi</b>\n\nXabaringizni belgilang, guruhlarni tanlang, "
              "intervalni sozlang va «▶️ Boshlash» tugmasini bosing.\n\nMenyudan foydalaning 👇",
        "ru": "🚕 <b>Taxi Yordamchi</b>\n\nЗадайте сообщение, выберите группы, настройте "
              "интервал и нажмите «▶️ Запустить».\n\nИспользуйте меню 👇",
        "en": "🚕 <b>Taxi Yordamchi</b>\n\nSet your message, choose groups, configure the "
              "interval and tap «▶️ Start».\n\nUse the menu 👇",
    },
    "need_login": {
        "uz": "Avval «🔑 Akkauntga kirish» tugmasini bosing.",
        "ru": "Сначала нажмите «🔑 Войти».",
        "en": "Please tap «🔑 Log in» first.",
    },
    "login_prompt": {
        "uz": "📱 Telefon raqamingizni yuboring (pastdagi tugma orqali) yoki +998... ko'rinishida yozing.",
        "ru": "📱 Отправьте номер телефона (кнопкой ниже) или введите в формате +998...",
        "en": "📱 Send your phone number (via the button below) or type it as +998...",
    },
    "logged_out": {
        "uz": "🚪 Chiqdingiz. Akkaunt uzildi.",
        "ru": "🚪 Вы вышли. Аккаунт отключён.",
        "en": "🚪 Logged out. Account disconnected.",
    },
    "msg_prompt": {
        "uz": "✍️ Guruhlarga yuboriladigan xabar matnini yuboring:",
        "ru": "✍️ Отправьте текст сообщения для рассылки в группы:",
        "en": "✍️ Send the message text to broadcast to the groups:",
    },
    "tpl_menu": {
        "uz": "📄 <b>Xabar shablonlari</b>\n\nTayyor xabarni tanlang — u faollashadi (✅ = hozir yuboriladigan). "
              "🗑 — o'chirish. Yangi qo'shish uchun «➕».",
        "ru": "📄 <b>Шаблоны сообщений</b>\n\nВыберите готовое сообщение — оно станет активным (✅ = отправляется сейчас). "
              "🗑 — удалить. Добавить новый — «➕».",
        "en": "📄 <b>Message templates</b>\n\nPick a ready message — it becomes active (✅ = currently sending). "
              "🗑 — delete. Add a new one with «➕».",
    },
    "tpl_active_label": {
        "uz": "📌 Hozir yuboriladigan xabar:",
        "ru": "📌 Сейчас отправляется:",
        "en": "📌 Currently sending:",
    },
    "tpl_none_active": {
        "uz": "⚠️ Hali faol xabar yo'q. Shablon tanlang yoki «➕» bilan yangisini qo'shing.",
        "ru": "⚠️ Активного сообщения пока нет. Выберите шаблон или добавьте новый «➕».",
        "en": "⚠️ No active message yet. Pick a template or add a new one «➕».",
    },
    "tpl_new_btn": {
        "uz": "➕ Yangi shablon",
        "ru": "➕ Новый шаблон",
        "en": "➕ New template",
    },
    "tpl_prompt": {
        "uz": "✍️ Yangi shablon matnini yuboring.\n\nMasalan:\n<i>Farg'ona → Toshkent, 4 o'rin bor 🚕 tel: ...</i>",
        "ru": "✍️ Отправьте текст нового шаблона.\n\nНапример:\n<i>Фергана → Ташкент, 4 места 🚕 тел: ...</i>",
        "en": "✍️ Send the text of the new template.\n\nExample:\n<i>Fergana → Tashkent, 4 seats 🚕 tel: ...</i>",
    },
    "tpl_saved": {
        "uz": "✅ Shablon saqlandi va faollashtirildi.",
        "ru": "✅ Шаблон сохранён и активирован.",
        "en": "✅ Template saved and activated.",
    },
    "tpl_activated": {
        "uz": "✅ Faollashtirildi",
        "ru": "✅ Активировано",
        "en": "✅ Activated",
    },
    "tpl_deleted": {
        "uz": "🗑 O'chirildi",
        "ru": "🗑 Удалено",
        "en": "🗑 Deleted",
    },
    "interval_prompt": {
        "uz": "⏱ Interval necha daqiqada bo'lsin? Raqam yuboring (eng kam {min} daqiqa).",
        "ru": "⏱ Через сколько минут повторять? Отправьте число (минимум {min} мин).",
        "en": "⏱ How many minutes between sends? Send a number (minimum {min} min).",
    },
    "groups_loading": {
        "uz": "⏳ Guruhlar yuklanmoqda...",
        "ru": "⏳ Загрузка групп...",
        "en": "⏳ Loading groups...",
    },
    "session_expired": {
        "uz": "❌ Sessiya eskirgan. Qayta kiring.",
        "ru": "❌ Сессия устарела. Войдите заново.",
        "en": "❌ Session expired. Please log in again.",
    },
    "groups_error": {
        "uz": "❌ Guruhlarni olishda xato: {err}",
        "ru": "❌ Ошибка при получении групп: {err}",
        "en": "❌ Failed to load groups: {err}",
    },
    "no_groups": {
        "uz": "Sizda guruhlar topilmadi.",
        "ru": "Группы не найдены.",
        "en": "No groups found.",
    },
    "groups_select": {
        "uz": "👥 Guruhlarni tanlang (belgilash uchun bosing), so'ng «✔️ Tayyor»:",
        "ru": "👥 Выберите группы (нажмите для отметки), затем «✔️ Готово»:",
        "en": "👥 Select groups (tap to toggle), then «✔️ Done»:",
    },
    "groups_done": {
        "uz": "✅ {count} ta guruh tanlandi.",
        "ru": "✅ Выбрано групп: {count}.",
        "en": "✅ {count} group(s) selected.",
    },
    "start_need": {
        "uz": "⚠️ Avval: {list}.",
        "ru": "⚠️ Сначала: {list}.",
        "en": "⚠️ First: {list}.",
    },
    "prob_login":    {"uz": "akkauntga kirmagansiz", "ru": "вы не вошли",        "en": "you're not logged in"},
    "prob_message":  {"uz": "xabar belgilanmagan",   "ru": "не задано сообщение", "en": "no message set"},
    "prob_interval": {"uz": "interval belgilanmagan","ru": "не задан интервал",   "en": "no interval set"},
    "prob_groups":   {"uz": "guruh tanlanmagan",     "ru": "не выбраны группы",   "en": "no groups selected"},
    "started": {
        "uz": "▶️ Ishga tushdi! Har {min} daqiqada {count} ta guruhga yuboriladi.",
        "ru": "▶️ Запущено! Каждые {min} мин в {count} групп(ы).",
        "en": "▶️ Started! Every {min} min to {count} group(s).",
    },
    "stopped": {
        "uz": "⏹ To'xtatildi.",
        "ru": "⏹ Остановлено.",
        "en": "⏹ Stopped.",
    },
    "status": {
        "uz": "ℹ️ <b>Holat</b>\n\nAkkaunt: {acc}\nInterval: {interval}\nGuruhlar: {groups} ta\n"
              "Holat: {state}\n\nXabar:\n<code>{msg}</code>",
        "ru": "ℹ️ <b>Статус</b>\n\nАккаунт: {acc}\nИнтервал: {interval}\nГруппы: {groups}\n"
              "Состояние: {state}\n\nСообщение:\n<code>{msg}</code>",
        "en": "ℹ️ <b>Status</b>\n\nAccount: {acc}\nInterval: {interval}\nGroups: {groups}\n"
              "State: {state}\n\nMessage:\n<code>{msg}</code>",
    },
    "acc_yes":   {"uz": "✅ kirgan",      "ru": "✅ подключён",  "en": "✅ connected"},
    "acc_no":    {"uz": "❌ yo‘q",        "ru": "❌ нет",        "en": "❌ none"},
    "state_on":  {"uz": "▶️ ishlayapti", "ru": "▶️ работает",   "en": "▶️ running"},
    "state_off": {"uz": "⏹ to‘xtatilgan","ru": "⏹ остановлено", "en": "⏹ stopped"},
    "min_word":  {"uz": "daqiqa",        "ru": "мин",          "en": "min"},
    "dash":      {"uz": "—",             "ru": "—",            "en": "—"},
    "phone_invalid": {
        "uz": "❌ Raqam noto'g'ri. Masalan: +998901234567",
        "ru": "❌ Неверный номер. Например: +998901234567",
        "en": "❌ Invalid number. Example: +998901234567",
    },
    "sending_code": {
        "uz": "⏳ Kod yuborilmoqda...",
        "ru": "⏳ Отправка кода...",
        "en": "⏳ Sending code...",
    },
    "code_pad_prompt": {
        "uz": "✉️ Kelgan kodni pastdagi tugmalar bilan kiriting 👇\n"
              "(shu usulda Telegram kodni bekor qilmaydi — bo'sh joy qo'yish shart emas)",
        "ru": "✉️ Введите полученный код кнопками ниже 👇\n"
              "(так Telegram не аннулирует код — пробелы не нужны)",
        "en": "✉️ Enter the received code using the buttons below 👇\n"
              "(this way Telegram won't invalidate the code — no spaces needed)",
    },
    "code_label": {
        "uz": "🔢 Kod",
        "ru": "🔢 Код",
        "en": "🔢 Code",
    },
    "code_pasted_hint": {
        "uz": "❌ Bu kod qabul qilinmadi.\n\nAgar kodni <b>matn qilib</b> (yozib yoki paste qilib) "
              "yuborgan bo'lsangiz — Telegram uni avtomatik bekor qiladi. Sizga <b>yangi kod</b> yubordik.\n\n"
              "👇 Endi kodni pastdagi tugmalar bilan kiriting — shunda bekor bo'lmaydi.",
        "ru": "❌ Этот код не принят.\n\nЕсли вы отправили код <b>текстом</b> (набрали или вставили) — "
              "Telegram автоматически аннулирует его. Мы отправили вам <b>новый код</b>.\n\n"
              "👇 Теперь введите код кнопками ниже — так он не аннулируется.",
        "en": "❌ This code was not accepted.\n\nIf you sent the code <b>as text</b> (typed or pasted) — "
              "Telegram automatically invalidates it. We've sent you a <b>new code</b>.\n\n"
              "👇 Now enter the code using the buttons below — this way it won't be invalidated.",
    },
    "code_prompt": {
        "uz": "✉️ Kelgan kodni kiriting.\n\n⚠️ <b>Muhim:</b> kodni raqamlar orasiga bo'sh joy "
              "qo'yib yozing, masalan <code>1 2 3 4 5</code> — aks holda Telegram kodni bekor qilishi mumkin.",
        "ru": "✉️ Введите полученный код.\n\n⚠️ <b>Важно:</b> вводите код с пробелами между цифрами, "
              "например <code>1 2 3 4 5</code> — иначе Telegram может аннулировать код.",
        "en": "✉️ Enter the code you received.\n\n⚠️ <b>Important:</b> type the code with spaces between "
              "digits, e.g. <code>1 2 3 4 5</code> — otherwise Telegram may invalidate it.",
    },
    "code_error": {
        "uz": "❌ Kod xato yoki eskirgan: {err}\n/cancel bosib qayta urinib ko'ring.",
        "ru": "❌ Неверный или устаревший код: {err}\nНажмите /cancel и попробуйте снова.",
        "en": "❌ Wrong or expired code: {err}\nTap /cancel and try again.",
    },
    "code_empty": {
        "uz": "❌ Kod topilmadi. Qayta kiriting.",
        "ru": "❌ Код не найден. Введите снова.",
        "en": "❌ No code found. Enter again.",
    },
    "twofa_prompt": {
        "uz": "🔐 Akkauntda ikki bosqichli parol bor. Parolni kiriting:",
        "ru": "🔐 На аккаунте включён облачный пароль (2FA). Введите пароль:",
        "en": "🔐 The account has two-step (2FA) password. Enter the password:",
    },
    "password_error": {
        "uz": "❌ Parol xato: {err}\nQayta kiriting yoki /cancel bosing.",
        "ru": "❌ Неверный пароль: {err}\nВведите снова или нажмите /cancel.",
        "en": "❌ Wrong password: {err}\nEnter again or tap /cancel.",
    },
    "login_success": {
        "uz": "✅ Muvaffaqiyatli kirdingiz!",
        "ru": "✅ Вы успешно вошли!",
        "en": "✅ Logged in successfully!",
    },
    "login_error": {
        "uz": "❌ Xatolik: {err}\n/cancel bosing.",
        "ru": "❌ Ошибка: {err}\nНажмите /cancel.",
        "en": "❌ Error: {err}\nTap /cancel.",
    },
    "msg_saved": {
        "uz": "✅ Xabar saqlandi.",
        "ru": "✅ Сообщение сохранено.",
        "en": "✅ Message saved.",
    },
    "msg_empty": {
        "uz": "❌ Iltimos, matn yuboring.",
        "ru": "❌ Пожалуйста, отправьте текст.",
        "en": "❌ Please send text.",
    },
    "interval_small": {
        "uz": "❌ Eng kam interval {min} daqiqa (akkaunt xavfsizligi uchun).",
        "ru": "❌ Минимальный интервал {min} мин (для безопасности аккаунта).",
        "en": "❌ Minimum interval is {min} min (for account safety).",
    },
    "interval_saved": {
        "uz": "✅ Interval: har {min} daqiqada.",
        "ru": "✅ Интервал: каждые {min} мин.",
        "en": "✅ Interval: every {min} min.",
    },
    "need_number": {
        "uz": "❌ Raqam kiriting.",
        "ru": "❌ Введите число.",
        "en": "❌ Enter a number.",
    },
    "cancelled": {
        "uz": "Bekor qilindi.",
        "ru": "Отменено.",
        "en": "Cancelled.",
    },
    "fallback": {
        "uz": "Menyudan tanlang 👇",
        "ru": "Выберите в меню 👇",
        "en": "Choose from the menu 👇",
    },
    "id_text": {
        "uz": "🆔 Sizning Telegram ID: <code>{id}</code>",
        "ru": "🆔 Ваш Telegram ID: <code>{id}</code>",
        "en": "🆔 Your Telegram ID: <code>{id}</code>",
    },
    "lang_prompt": {
        "uz": "🌐 Tilni tanlang:",
        "ru": "🌐 Выберите язык:",
        "en": "🌐 Choose a language:",
    },
    "lang_changed": {
        "uz": "✅ Til o'zgartirildi.",
        "ru": "✅ Язык изменён.",
        "en": "✅ Language changed.",
    },
    "send_phone_btn": {
        "uz": "📱 Raqamni yuborish",
        "ru": "📱 Отправить номер",
        "en": "📱 Send number",
    },
    "done_btn": {
        "uz": "✔️ Tayyor",
        "ru": "✔️ Готово",
        "en": "✔️ Done",
    },
    # --- kod yetkazish usullari ---
    "code_app": {
        "uz": "📲 Kod Telegram ILOVASIGA yuborildi.\nTelefoningizda Telegramni ochib, «Telegram» "
              "nomli rasmiy chatni (777000) qarang.",
        "ru": "📲 Код отправлен в ПРИЛОЖЕНИЕ Telegram.\nОткройте Telegram и посмотрите официальный "
              "чат «Telegram» (777000).",
        "en": "📲 The code was sent to the Telegram APP.\nOpen Telegram and check the official "
              "«Telegram» chat (777000).",
    },
    "code_sms":    {"uz": "✉️ Kod SMS orqali yuborildi.", "ru": "✉️ Код отправлен по SMS.", "en": "✉️ The code was sent via SMS."},
    "code_call":   {"uz": "📞 Kod qo'ng'iroq orqali aytiladi.", "ru": "📞 Код продиктуют по звонку.", "en": "📞 The code will be dictated by a call."},
    "code_missed": {"uz": "📞 Qo'ng'iroq keladi — kod raqamning oxirgi raqamlari.", "ru": "📞 Будет звонок — код это последние цифры номера.", "en": "📞 A call will come — the code is the last digits of the number."},
    "code_sent":   {"uz": "Kod yuborildi.", "ru": "Код отправлен.", "en": "Code sent."},
}


def normalize(lang: str | None) -> str:
    return lang if lang in LANGS else DEFAULT_LANG


def t(lang: str | None, key: str, **kw) -> str:
    lang = normalize(lang)
    entry = TEXTS.get(key, {})
    s = entry.get(lang) or entry.get(DEFAULT_LANG) or key
    return s.format(**kw) if kw else s


def button_action(text: str | None) -> str | None:
    """Menyu tugmasi matnini (istalgan tilda) harakat kalitiga aylantiradi."""
    if not text:
        return None
    for action, variants in BUTTONS.items():
        if text in variants.values():
            return action
    return None
