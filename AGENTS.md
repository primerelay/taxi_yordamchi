# Taxi Yordamchi — Agent / Developer Guide

Context file for AI assistants (Claude Code, Codex, etc.) and developers.
Read this first before working on the project. User-facing communication is in **Uzbek**.

---

## 1. What this is

A Telegram service for **taxi drivers** to auto-advertise rides in Telegram groups.
A driver logs into the bot **with their own Telegram account**, saves message templates,
picks groups, sets an interval — and the bot posts the message to those groups
**as the driver's own account**, repeatedly, on that interval.

Monetization: 3-day free trial, then a manual (admin-managed) subscription. Referral bonus.

---

## 2. Architecture

```
                       ┌──────────────────────────────────────────┐
   Telegram  ◀─polling─│  CONTROL BOT (aiogram)  — bot/            │
   (drivers)           │    driver taps buttons: login, message,  │
                       │    groups, interval, start/stop          │
                       │            │                             │
                       │            ▼                             │
                       │   USERBOT (Telethon, per-driver session) │
                       │    logs in as the driver's account,      │
                       │    reads their groups, sends messages    │
                       │            │                             │
                       │            ▼                             │
                       │   SQLite  taxi_bot.db  (WAL)             │
                       │            ▲                             │
   Browser ◀──HTTPS────│  ADMIN (FastAPI JSON API + React SPA)    │
   (admin)             │    admin/  — stats, users, payments      │
                       └──────────────────────────────────────────┘
```

- **Control bot** (`bot/`, aiogram 3.x): the UI drivers interact with (persistent reply
  keyboard menu). Long-polling, no inbound port.
- **Userbot** (`bot/userbot.py`, Telethon 1.44): authenticates each driver's account via
  phone + login code, stores a `StringSession` **in the DB**, sends messages on their behalf.
- **Admin** (`admin/`): FastAPI JSON API + React/Tailwind SPA. Same SQLite DB as the bot
  (this is why bot + admin must live on the **same machine**).
- **DB**: SQLite file `taxi_bot.db`. Both bot and admin read/write it.

---

## 3. Tech stack

- Python 3.12+ (server) — bot & admin backend
- aiogram 3.x (control bot), Telethon 1.44 (userbot)
- FastAPI + uvicorn + itsdangerous (admin API, token auth)
- aiosqlite (bot) / sqlite3 (admin) over one SQLite file
- React 18 + Vite 6 + Tailwind 4 (admin frontend)
- Node 20 (server, for building the frontend)
- Deployment: Contabo VPS + nginx + certbot; CI/CD via GitHub Actions

---

## 4. Repo structure

```
bot/
├── main.py            # entrypoint: aiogram Dispatcher + ActivityMiddleware + scheduler
├── config.py          # env vars (API_ID/HASH, BOT_TOKEN, admin, trial/referral, intervals)
├── db.py              # aiosqlite: schema, migrations, all queries, subscription helpers
├── userbot.py         # Telethon: login (send_code/confirm), get_groups, broadcast
├── scheduler.py       # per-user asyncio loop that broadcasts on interval (see §8)
├── keyboards.py       # reply menu + inline keyboards (code pad, groups, interval, lang, share)
├── i18n.py            # 3-language texts + BUTTONS map + t()/button_action()/fmt_interval()
├── states.py          # FSM states (Auth, Compose)
├── middleware.py      # ActivityMiddleware: touch_user on every update (DAU, trial grant)
└── handlers/router.py # ALL handlers (commands, menu dispatch, auth, templates, groups, admin)

admin/
├── app.py             # FastAPI JSON API (token auth) + serves React build (dist)
├── config.py          # admin env (ADMIN_USERNAME/PASSWORD/SECRET_KEY, CORS, port)
├── db.py              # sqlite3 (sync) queries: stats, list_users, payments, set_paid_until
└── frontend/          # React + Vite + Tailwind SPA
    ├── src/api.js     # API client (Bearer token; VITE_API_BASE for cross-origin)
    ├── src/Layout.jsx # top nav + mobile bottom tab bar
    ├── src/pages/     # Login, Dashboard, Users, UserDetail, Payments
    ├── src/ui.jsx     # Card, Badge, Spinner, button classes
    └── vercel.json    # SPA rewrites (only if hosting frontend on Vercel — NOT used now)

login.py               # standalone interactive terminal login (fallback session generator)
requirements.txt       # Python deps
.github/workflows/deploy.yml  # CI/CD (auto-deploy on push)
.env / .env.example    # secrets (.env gitignored)
DEPLOY.md              # deployment guide (DigitalOcean-oriented; actual deploy = Contabo, see §11)
```

---

## 5. Features

- **Login** as the driver's own Telegram account (Telethon). Code entered via an **inline
  numeric pad** (so the code is never sent as chat text → Telegram won't invalidate it).
  2FA password supported. Paste-fallback: if a code is pasted as text and fails, the bot
  auto-requests a new code and points to the pad.
- **Message templates**: save multiple messages (e.g. "Farg'ona→Toshkent"), activate one
  with a tap (✅), delete with 🗑, add new with ➕. Active template = `users.message`.
- **Group selection**: inline checklist of the driver's groups (✅/▫️), "Done".
- **Interval** in **seconds** (min `MIN_INTERVAL_SECONDS`, default 30): preset buttons
  (30s / 1 / 2 / 5 / 10 / 30 min / 1h) + "✏️ Custom time".
- **Start / Stop** broadcasting. Persistent reply-keyboard menu (always visible).
- **3 languages** (uz default / ru / en), per-user, switchable via 🌐 menu.
- **Subscription**: new users get `TRIAL_DAYS` free (default 3). When `paid_until < today`,
  broadcasting stops (but the job stays — resumes automatically when admin extends).
  "💳 Obuna" button shows days left + payment contact (`SUPPORT_USERNAME`).
- **Referral**: "🎁 Invite friends" → link `https://t.me/<bot>?start=ref_<user_id>`.
  A new user's **first** `/start` via that link credits the referrer `+REFERRAL_DAYS`.
- **Admin broadcast**: `/broadcast <text>` and `/announce_referral` (admins in `ADMIN_IDS`).
- **Admin panel**: dashboard (total users, DAU, logged-in, mailing, paying/expired, revenue),
  users list with filters + search, user detail with payment history, manual payment /
  set paid-until, payments/accounting page. Mobile-responsive.

---

## 6. Database schema (`taxi_bot.db`)

`users` — one row per driver (Telegram id of the control-bot user):
- `user_id` PK, `phone`, `session` (Telethon StringSession — sensitive!),
- `message` (active broadcast text), `interval_minutes` (legacy, unused),
  `interval_seconds`, `active` (0/1),
- `full_name`, `username`, `lang` ('uz'|'ru'|'en'),
- `last_active` (DAU), `paid_until` (YYYY-MM-DD; trial/subscription),
- `referred_by` (referrer user_id), `onboarded` (0/1, first /start done),
- `created_at`.

`selected_groups` — (user_id, chat_id, title) — groups chosen per user.
`templates` — (id, user_id, text, created_at) — saved message templates.
`payments` — (id, user_id, amount, months, paid_at, note) — manual payment log (admin).

Migrations are automatic in `db.init()` (ALTER TABLE for missing columns). Adding a new
column: add to `_SCHEMA` (fresh installs) **and** `_MIGRATIONS` (existing DBs).

---

## 7. Environment variables (`.env`)

```
API_ID, API_HASH          # my.telegram.org (userbot credentials)
BOT_TOKEN                 # @BotFather (control bot)
DB_PATH=taxi_bot.db
MIN_INTERVAL_SECONDS=30   # minimum interval users can set
SEND_DELAY_SECONDS=4      # delay between groups (flood protection)
TRIAL_DAYS=3              # free trial for new users
REFERRAL_DAYS=3           # bonus per invited user
SUPPORT_USERNAME=@...     # payment contact shown to users
ADMIN_IDS=123,456         # Telegram ids allowed to /broadcast, /announce_referral
# --- admin panel ---
ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_SECRET_KEY
ADMIN_HOST=127.0.0.1, ADMIN_PORT=8010
CURRENCY=so'm
ADMIN_CORS_ORIGINS=https://taxi.tezhisobchi.uz
```
`.env` is gitignored. Never commit it. On the server it lives at `/opt/taxi_yordamchi/.env`.

---

## 8. Key design decisions & gotchas (READ THIS)

- **Scheduler = per-user asyncio loop, NOT APScheduler.** `bot/scheduler.py` runs one
  `asyncio.Task` per active user: *send → sleep(interval) → repeat*. The interval is the gap
  **after** each send, so long sends (many groups / FloodWait) never cause skipped/overlapping
  cycles ("sleeping" bug that APScheduler had). `add_user_job()` sends immediately then loops;
  do NOT also call `run_now()` from the router (would double-send). Each cycle re-reads
  interval/active from the DB (dynamic). Invalid session → `active=0` + stop.
- **Login code invalidation.** If a user sends the login code as a **text message**, Telegram
  invalidates it *before* our bot receives it — we cannot fix it after the fact. Solution: the
  inline **numeric pad** (`keyboards.code_pad`, callbacks `cd:*`) enters digits via button
  presses, so the code never appears as text. Typed-with-spaces still works as a fallback;
  a pasted raw code triggers auto-resend + pad.
- **Single BOT_TOKEN.** Only ONE process may poll a given token. Never run the bot locally
  while the server bot is live — Telegram returns 409 conflict. Use a separate test bot token
  for local dev.
- **Telethon StringSession is stored in `users.session`** = full access to the driver's
  account. Treat the DB as a secret; back it up; consider encryption for hardening.
- **Menu is a persistent reply keyboard.** Button label text → action via
  `i18n.button_action()` + the `MenuButton` filter in the router. Labels are per-language,
  so matching is by reverse-lookup across all languages. Group/code/interval/lang/share use
  inline keyboards.
- **Subscription enforcement** happens in `scheduler._run_once` (skip send if
  `not db.subscription_ok(paid_until)`) and in the Start handler (block). The job is NOT
  removed on expiry — it auto-resumes when the admin extends `paid_until`.
- **i18n**: every user-facing string is a key in `bot/i18n.py` `TEXTS`; buttons in `BUTTONS`.
  Use `t(lang, key, **fmt)`. Add all 3 languages when adding a string.
- **Interval is in seconds** everywhere (`interval_seconds`). `interval_minutes` column is
  legacy/unused. Display via `i18n.fmt_interval(lang, seconds)`.

---

## 9. Admin / bot commands

- `/start [ref_<id>]` — main menu; processes referral on first start.
- `/id` — shows the user's Telegram id (needed for `ADMIN_IDS`).
- `/cancel` — cancel current flow.
- `/broadcast <text>` — (admin only) send text to all users.
- `/announce_referral` — (admin only) send the referral announcement to every user in their
  language, each with their personal invite link + share button.

---

## 10. Local development

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
cp .env.example .env          # fill API_ID/HASH, BOT_TOKEN (use a TEST bot!), admin creds
./.venv/bin/python -m bot.main      # run the bot (polling)

# Admin (serves API + built React on one port):
cd admin/frontend && npm install && npm run build && cd ../..
./.venv/bin/python -m admin.app     # http://localhost:8000  (ADMIN_PORT)
# Admin dev with hot reload: (terminal 2) cd admin/frontend && npm run dev  (port 5173, proxies /api)
```
`login.py` is a standalone terminal login that writes a session straight into the DB
(useful when the in-chat code flow is problematic).

---

## 11. Production deployment (Contabo VPS)

**Server:** Contabo Ubuntu 24.04, IPv4 `13.140.168.45` (host `vmi3562658`), SSH as `root`.
A second unrelated project ("tezkor-slide", Node.js on :3000, Docker) also runs here — do
NOT touch it. That's why the admin uses port **8010** (not 8000).

- **Code:** `/opt/taxi_yordamchi` (git clone of this public repo), venv in `.venv`.
- **Domain:** `taxi.tezhisobchi.uz` (A record → server IP; DNS managed at ahost.uz).
- **HTTPS:** Let's Encrypt via certbot (`certbot --nginx -d taxi.tezhisobchi.uz`).
- **Services (systemd, enabled = start on boot):**
  - `taxi-bot`  → `.venv/bin/python -m bot.main`
  - `taxi-admin`→ `.venv/bin/uvicorn admin.app:app --host 127.0.0.1 --port 8010`
- **nginx:** `/etc/nginx/sites-available/taxi` proxies `taxi.tezhisobchi.uz` → `127.0.0.1:8010`.
  The FastAPI backend serves the built React SPA itself (no Vercel needed).
- **Admin URL:** https://taxi.tezhisobchi.uz  (login: `ADMIN_USERNAME` / `ADMIN_PASSWORD`).

Full first-time setup steps are in `DEPLOY.md` (written DigitalOcean-style; the same steps
were applied to Contabo with port 8010 + the existing-nginx co-existence noted above).

---

## 12. CI/CD (auto-deploy)

`.github/workflows/deploy.yml` — on push to `main` (ignoring `**.md`), GitHub Actions SSHes
into the server and runs: `git reset --hard origin/main` → `pip install` → `npm build` →
`systemctl restart taxi-bot taxi-admin`.

GitHub secrets (repo → Settings → Secrets → Actions):
`SERVER_HOST=13.140.168.45`, `SERVER_USER=root`, `SERVER_SSH_KEY` (private key; public key in
server `/root/.ssh/authorized_keys`, generated as `/root/.ssh/taxi_deploy`).

**So the normal workflow is: edit code → `git push` → it's live in ~15-20s.** Watch runs at
`github.com/primerelay/taxi_yordamchi/actions`.

---

## 13. Common operations

```bash
# Logs (on server)
journalctl -u taxi-bot -f
journalctl -u taxi-admin -f

# Manual update (CI/CD does this automatically on push)
cd /opt/taxi_yordamchi && git pull && ./.venv/bin/pip install -r requirements.txt \
  && cd admin/frontend && npm install && npm run build \
  && cd ../.. && systemctl restart taxi-bot taxi-admin

# Backup DB (WAL — use .backup, not cp)
sqlite3 /opt/taxi_yordamchi/taxi_bot.db ".backup /root/taxi_backup_$(date +%F).db"

# Add an admin: edit ADMIN_IDS in /opt/taxi_yordamchi/.env then: systemctl restart taxi-bot
# Rotate deploy key: ssh-keygen again on server + update SERVER_SSH_KEY secret
```

---

## 14. How to add a feature (the pattern)

1. Add user-facing strings to `bot/i18n.py` (`TEXTS`, and `BUTTONS` if it's a menu button) —
   all 3 languages.
2. Build keyboards in `bot/keyboards.py` if needed.
3. Add handler logic in `bot/handlers/router.py` (menu actions go through `on_menu`; new
   commands/callbacks get their own handler). Keep menu-button handlers before state handlers.
4. DB changes: add column to `_SCHEMA` **and** `_MIGRATIONS` in `bot/db.py`; add query funcs.
5. Admin changes (if relevant): `admin/db.py` query + `admin/frontend/src/...` UI, then the
   frontend is rebuilt automatically on deploy.
6. Test locally (`py_compile`, run with a test token), then `git push` → auto-deploys.

Keep new code consistent with the existing style (Uzbek comments/user-text, English code).
