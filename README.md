# 🚕 Taxi Yordamchi

Taxi haydovchilari uchun Telegram bot. Haydovchi bot ichiga kiradi, xabar yozadi,
guruhlarni tanlaydi va interval belgilaydi — bot esa shu xabarni **haydovchining
o'z akkaunti nomidan** tanlangan guruhlarga belgilangan vaqt oralig'ida yuborib turadi.

> 🚀 Ishlab chiqarishga chiqarish (DigitalOcean + Vercel): **[DEPLOY.md](DEPLOY.md)**.

## Qanday ishlaydi

- **Boshqaruvchi bot** (aiogram) — haydovchi shu bot bilan tugmalar orqali ishlaydi.
- **Userbot** (Telethon) — har bir haydovchi telefon raqami + Telegram kodi bilan
  kiradi. Xabarlar uning **o'z profili** nomidan yuboriladi (oddiy bot buni qila olmaydi).
- **Rejalashtiruvchi** (APScheduler) — belgilangan intervalda tarqatadi.
- **SQLite** — sozlamalar va session'lar shu yerda saqlanadi.

## O'rnatish

### 1. Telegram API kalitlari

1. [my.telegram.org](https://my.telegram.org) → **API development tools** → yangi ilova
   yarating. `API_ID` va `API_HASH` ni oling.
2. [@BotFather](https://t.me/BotFather) da yangi bot yarating va `BOT_TOKEN` oling.

### 2. Sozlash

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env faylni to'ldiring: API_ID, API_HASH, BOT_TOKEN
```

### 3. Ishga tushirish

```bash
python -m bot.main
```

## Foydalanish (haydovchi uchun)

1. Botga `/start` yuboradi.
2. **🔑 Akkauntga kirish** → telefon raqami → kelgan kodni kiritadi
   (kodni `1 2 3 4 5` ko'rinishida — raqamlar orasiga bo'sh joy qo'yib yozish tavsiya etiladi).
   Agar 2FA parol bo'lsa — parolni ham kiritadi.
3. **✍️ Xabarni belgilash** → yuboriladigan matnni yozadi.
4. **👥 Guruhlarni tanlash** → ro'yxatdan kerakli guruhlarni belgilaydi → **Tayyor**.
5. **⏱ Interval belgilash** → necha daqiqada yuborilishini kiritadi.
6. **▶️ Boshlash** — tarqatish boshlanadi. **⏹ To'xtatish** — to'xtatadi.

## 🖥 Admin panel (React + Tailwind)

Boshqaruvchi uchun alohida web panel. Ikki qismdan iborat:
- **Backend** — FastAPI JSON API (`admin/app.py`), token bilan avtorizatsiya.
- **Frontend** — React + Tailwind SPA (`admin/frontend/`), Vite bilan quriladi.

`.env` dagi login/parol bilan kiriladi.

### Ishlab chiqish rejimi (dev)

Ikki terminalda:

```bash
# 1) Backend API (8000-port)
python -m admin.app

# 2) Frontend dev server (5173-port, /api backendga uzatiladi)
cd admin/frontend
npm install
npm run dev
```

Brauzerda: `http://localhost:5173`

### Ishlab chiqarish rejimi (production)

Frontend'ni bir marta build qilasiz — keyin FastAPI hammasini bitta portdan beradi:

```bash
cd admin/frontend && npm install && npm run build   # -> admin/frontend/dist
cd ../.. && python -m admin.app                      # http://127.0.0.1:8000
```

Kirish: `.env` dagi `ADMIN_USERNAME` / `ADMIN_PASSWORD`.

### Imkoniyatlari

- **Boshqaruv paneli:** jami foydalanuvchilar, **kunlik faol (DAU)**, bugun qo'shilganlar,
  akkaunt ulaganlar, hozir tarqatayotganlar; to'lagan/muddati tugagan obunachilar,
  bu oy va jami tushum.
- **Foydalanuvchilar:** ro'yxat + **filtrlar** (to'lagan / muddati tugagan / to'lamagan /
  bugun faol / tarqatyapti / akkaunt ulagan), qidiruv (ID, ism, username, telefon),
  saralash, sahifalash.
- **Foydalanuvchi kartasi:** to'liq ma'lumot, tanlangan guruhlar, xabar, to'lovlar tarixi.
- **Qo'lda to'lov:** summa + necha oy kiritib **to'lovni qayd etasiz** — obuna muddati
  avtomatik uzayadi. Yoki **muddatni qo'lda** (kalendardan) belgilaysiz.
- **To'lovlar / hisob-kitob:** sana bo'yicha filtrlangan to'lovlar ro'yxati va davr tushumi.

> Admin panelni faqat ichki tarmoqda (`127.0.0.1`) yoki reverse-proxy + HTTPS ortida
> ishlating. Internetga to'g'ridan-to'g'ri ochmang.

## ⚠️ Muhim ogohlantirishlar

- **Spam xavfi.** Telegram tez-tez va ko'p guruhga bir xil xabar yuborilsa,
  akkauntni cheklashi yoki bloklashi mumkin. Shu sabab:
  - `MIN_INTERVAL_MINUTES` (standart 5 daqiqa) — minimal interval cheklovi.
  - `SEND_DELAY_SECONDS` (standart 4 sekund) — har guruh orasidagi kechikish.
  - `FloodWait` xatolari avtomatik boshqariladi.
- **Session xavfsizligi.** `session` — bu haydovchi akkauntiga to'liq kirish.
  Ular bazada ochiq saqlanadi. Ishlab chiqarishda bazani shifrlash yoki
  himoyalangan serverda saqlash tavsiya etiladi. `.env` va `*.db` git'ga tushmaydi.
- Faqat qonuniy, o'zingiz a'zo bo'lgan guruhlarda va guruh qoidalariga rioya qilgan
  holda foydalaning.

## Loyiha tuzilmasi

```
bot/
├── main.py            # ishga tushirish nuqtasi
├── config.py          # .env sozlamalari
├── db.py              # SQLite (aiosqlite)
├── userbot.py         # Telethon userbot (login, guruhlar, tarqatish)
├── scheduler.py       # APScheduler interval joblar
├── keyboards.py       # inline/reply klaviaturalar
├── states.py          # FSM holatlari
├── middleware.py      # foydalanuvchi faolligini kuzatish (DAU)
└── handlers/router.py # barcha handlerlar

admin/
├── app.py             # FastAPI JSON API + React build'ni servis qilish
├── config.py          # admin .env sozlamalari (token, CORS)
├── db.py              # statistika, filtrlar, to'lov so'rovlari
└── frontend/          # React + Tailwind SPA (Vite)
    ├── src/pages/     # Login, Dashboard, Users, UserDetail, Payments
    ├── src/api.js     # backend API klienti (token bilan)
    └── src/ui.jsx     # umumiy komponentlar (Card, Badge, ...)
```
