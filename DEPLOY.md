# 🚀 Deploy qilish yo'riqnomasi

Bu hujjat loyihani ishlab chiqarishga chiqarishni tushuntiradi:

- **Bot + Admin backend (API)** → **DigitalOcean** droplet
- **Admin frontend (React)** → **Vercel**

## 🧭 Arxitektura (muhim!)

```
                          ┌─────────────────────────────────────┐
                          │        DigitalOcean droplet          │
   Telegram  ◀──polling──▶│  taxi-bot  (Telethon + aiogram)      │
                          │      │                               │
                          │      ▼  bir xil SQLite fayl          │
                          │  taxi_bot.db  (WAL rejimi)           │
                          │      ▲                               │
   Vercel (React) ──HTTPS─▶  taxi-admin (FastAPI API :8000)      │
        ▲                 │      └── nginx :443 (api.domen.uz)   │
        │                 └─────────────────────────────────────┘
   Brauzer (admin)
```

**Nega admin backend Vercel'da EMAS?** Admin API bot bilan **bir xil SQLite faylni**
o'qiydi. SQLite — lokal fayl, shuning uchun API bot bilan **bir serverda** (DigitalOcean)
turishi shart. Vercel'ga esa faqat React frontend (statik fayllar) joylanadi va u
API'ga internet orqali murojaat qiladi.

> Kelajakda frontend va backend'ni butunlay ajratmoqchi bo'lsangiz — SQLite'dan
> **PostgreSQL**'ga (masalan DigitalOcean Managed DB) o'tish kerak bo'ladi.

---

## 1-QISM · DigitalOcean (bot + admin API)

### 1.1. Droplet yaratish

1. DigitalOcean → **Create → Droplet**.
2. Image: **Ubuntu 24.04 LTS**. Plan: eng arzoni (1 GB RAM) yetarli.
3. SSH kalit qo'shing (parol o'rniga tavsiya etiladi).
4. Yaratilgach IP manzilni oling, masalan `203.0.113.10`.

### 1.2. Serverga kirish va boshlang'ich sozlash

```bash
ssh root@203.0.113.10

# Yangilash
apt update && apt upgrade -y

# Kerakli paketlar
apt install -y python3 python3-venv python3-pip git nginx

# Alohida foydalanuvchi (root'da ishlatmang)
adduser --disabled-password --gecos "" taxi
usermod -aG sudo taxi

# Firewall
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable
```

### 1.3. Kodni klonlash va o'rnatish

```bash
su - taxi
git clone <SIZNING_REPO_URL> /home/taxi/taxi_yordamchi
cd /home/taxi/taxi_yordamchi

python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt
```

### 1.4. `.env` faylini sozlash

```bash
cp .env.example .env
nano .env
```

To'ldiriladigan qiymatlar:

```ini
# Telegram
API_ID=1234567
API_HASH=...
BOT_TOKEN=...

# Baza (ikkala servis ham shu faylni ishlatadi)
DB_PATH=/home/taxi/taxi_yordamchi/taxi_bot.db

# Xavfsizlik
MIN_INTERVAL_MINUTES=5
SEND_DELAY_SECONDS=4

# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=juda_kuchli_parol_qoying
# Maxfiy kalitni generatsiya qiling (pastdagi buyruq natijasini qo'ying):
ADMIN_SECRET_KEY=...
ADMIN_HOST=127.0.0.1
ADMIN_PORT=8000
CURRENCY=so'm

# Vercel domenini keyin (2-qism) shu yerga qo'shasiz:
ADMIN_CORS_ORIGINS=https://taxi-admin.vercel.app
```

Maxfiy kalit generatsiya qilish:

```bash
./.venv/bin/python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 1.5. `systemd` servislari

**Bot servisi** — `/etc/systemd/system/taxi-bot.service`:

```bash
sudo nano /etc/systemd/system/taxi-bot.service
```

```ini
[Unit]
Description=Taxi Yordamchi bot
After=network.target

[Service]
Type=simple
User=taxi
WorkingDirectory=/home/taxi/taxi_yordamchi
ExecStart=/home/taxi/taxi_yordamchi/.venv/bin/python -m bot.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Admin API servisi** — `/etc/systemd/system/taxi-admin.service`:

```bash
sudo nano /etc/systemd/system/taxi-admin.service
```

```ini
[Unit]
Description=Taxi Yordamchi admin API
After=network.target

[Service]
Type=simple
User=taxi
WorkingDirectory=/home/taxi/taxi_yordamchi
ExecStart=/home/taxi/taxi_yordamchi/.venv/bin/uvicorn admin.app:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

> API `127.0.0.1` ga bog'lanadi — tashqaridan faqat nginx orqali (HTTPS bilan) ochiladi.

Ishga tushirish:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now taxi-bot taxi-admin

# Holatni tekshirish
sudo systemctl status taxi-bot
sudo systemctl status taxi-admin

# Loglar
journalctl -u taxi-bot -f
journalctl -u taxi-admin -f
```

### 1.6. Domen va nginx (admin API uchun)

1. Domeningizda **A-record** qo'shing: `api.domen.uz` → `203.0.113.10`.
2. Nginx konfiguratsiyasi — `/etc/nginx/sites-available/taxi-admin`:

```bash
sudo nano /etc/nginx/sites-available/taxi-admin
```

```nginx
server {
    listen 80;
    server_name api.domen.uz;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/taxi-admin /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

3. **HTTPS** (Let's Encrypt, bepul):

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.domen.uz
```

Endi API `https://api.domen.uz` da ishlaydi. Tekshiring:

```bash
curl https://api.domen.uz/api/stats   # 401 qaytishi kerak (avtorizatsiyasiz) — bu to'g'ri
```

---

## 2-QISM · Vercel (admin frontend)

### 2.1. Loyihani import qilish

1. Kodni GitHub'ga push qiling.
2. [vercel.com](https://vercel.com) → **Add New → Project** → reponi tanlang.
3. **Muhim sozlama:**
   - **Root Directory**: `admin/frontend`
   - **Framework Preset**: `Vite` (avtomatik aniqlanadi)
   - Build Command: `npm run build` · Output Directory: `dist` (avtomatik)

### 2.2. Environment variable

Vercel loyiha sozlamalarida **Environment Variables** bo'limiga qo'shing:

| Nomi            | Qiymati                    |
|-----------------|----------------------------|
| `VITE_API_BASE` | `https://api.domen.uz`     |

> `admin/frontend/vercel.json` allaqachon mavjud — u SPA routing (sahifa yangilanganda
> `/users/...` kabi yo'llarni `index.html` ga yo'naltirish)ni ta'minlaydi.

### 2.3. Deploy

**Deploy** tugmasini bosing. Vercel avtomatik build qiladi va domen beradi, masalan
`https://taxi-admin.vercel.app`.

### 2.4. Backend'da CORS'ni yangilash

DigitalOcean serverida `.env` dagi `ADMIN_CORS_ORIGINS` ni Vercel domeniga moslang
(agar 1-qismda boshqa qiymat qo'ygan bo'lsangiz):

```bash
ssh taxi@203.0.113.10
nano /home/taxi/taxi_yordamchi/.env
# ADMIN_CORS_ORIGINS=https://taxi-admin.vercel.app
sudo systemctl restart taxi-admin
```

Bir nechta domen bo'lsa vergul bilan: `https://a.vercel.app,https://admin.domen.uz`.

Endi `https://taxi-admin.vercel.app` ga kirib, `.env` dagi login/parol bilan
tizimga kirishingiz mumkin. ✅

---

## 🔄 Yangilash (keyingi deploylar)

**Backend/bot (DigitalOcean):**

```bash
ssh taxi@203.0.113.10
cd /home/taxi/taxi_yordamchi
git pull
./.venv/bin/pip install -r requirements.txt   # yangi kutubxona bo'lsa
sudo systemctl restart taxi-bot taxi-admin
```

**Frontend (Vercel):** GitHub'ga `git push` qilsangiz Vercel **avtomatik** qayta deploy qiladi.

---

## 💾 Bazani zaxiralash (backup)

SQLite WAL rejimida ishlagani uchun `.backup` buyrug'idan foydalaning (oddiy `cp` emas):

```bash
# Qo'lda zaxira
sqlite3 /home/taxi/taxi_yordamchi/taxi_bot.db ".backup /home/taxi/backup_$(date +%F).db"
```

Kunlik avtomatik zaxira (`crontab -e`):

```cron
0 3 * * * sqlite3 /home/taxi/taxi_yordamchi/taxi_bot.db ".backup /home/taxi/backups/db_$(date +\%F).db"
```

---

## ✅ Xavfsizlik nazorati (checklist)

- [ ] `ADMIN_PASSWORD` — kuchli, `ADMIN_SECRET_KEY` — tasodifiy 40+ belgili.
- [ ] Admin API faqat `127.0.0.1:8000` da (to'g'ridan-to'g'ri internetga ochiq emas).
- [ ] Nginx + HTTPS (certbot) yoqilgan; `http` → `https` ga yo'naltiriladi.
- [ ] `ADMIN_CORS_ORIGINS` faqat sizning Vercel domeningizga ruxsat beradi (`*` emas).
- [ ] `.env` va `*.db` git'ga tushmaydi (`.gitignore` da bor).
- [ ] Baza muntazam zaxiralanadi (Telethon session'lari — akkauntga to'liq kirish demak).
- [ ] SSH parol bilan emas, kalit bilan; `ufw` yoqilgan.
```
