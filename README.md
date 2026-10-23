# 📚 Elektron Kutubxona va Kitob Qidiruv Telegram Boti

Ushbu loyiha **Telegram Bot API**, **Python (Aiogram 3.x)** va **SQLAlchemy (Asyncio)** texnologiyalari asosida Texnik Topshiriq (TZ) talablariga 100% mos ravishda to'liq ishlab chiqilgan va optimallashtirilgan.

Bot foydalanuvchilarga kitob nomi yoki muallifi bo'yicha elektron kitoblarni (PDF) tezkor topish, annotatsiyasi bilan tanishish va yuklab olish imkonini beradi. Administratorlar uchun esa ko'p bosqichli xavfsizlik (3 xil usulda autentifikatsiya), kitob qo'shish/tahrirlash/o'chirish, statistika va ommaviy xabar yuborish (broadcast) boshqaruv paneli mavjud.

---

## 🌟 Asosiy imkoniyatlar va Optimallashuvlar

### 1. Foydalanuvchi qismi (User Flow)
- **`/start` ekrani:** Foydalanuvchi ma'lumotlari (`telegram_id`, `username`, `full_name`) avtomatik bazaga yoziladi va `[ 🔍 Kitob qidirish ]` inline tugmasi taqdim etiladi. Adminlar uchun avtomatik `[ ⚡️ Administrator paneli 👑 ]` tugmasi chiqadi.
- **Aqlli qidiruv (Smart Fuzzy Search):** O'zbek alifbosidagi turli xil apostroflar (`'`, `‘`, `’`, `ʻ`, `ʼ`, `` ` ``) va imlo o'ziga xosliklarini normalizatsiya qilib qidiradi.
- **Inline Mode:** Foydalanuvchilar istalgan chatda (guruh, do'stlar) `@online_libraries_bot kitob_nomi` deb yozish orqali kitoblarni qidirib, to'g'ridan-to'g'ri ulasha oladilar.
- **Deep Linking:** Guruhlarga yuborilgan kitoblardagi "Yuklab olish" tugmasi bosilganda bot avtomatik `/start book_{id}` orqali ochilib, o'sha kitobni darhol foydalanuvchiga taqdim etadi.
- **Tezkor PDF yuklab olish:** Fayllar mahalliy diskda emas, Telegram serverlarida saqlanadi (`file_id` orqali), bu esa 50 MB gacha bo'lgan kitoblarni 1 soniyada yetkazib beradi va `downloads_count` hisoblagichini oshiradi.
- **Menyu tugmalari:**
  - `/start` — 📚 Bosh menyu va qidiruv
  - `/search` — 🔍 Kitob qidirish
  - `/top` — 🔥 Eng ko'p o'qilgan kitoblar
  - `/admin` — ⚡️ Administrator paneli
  - `/help` — ℹ️ Qo'llanma va yordam

### 2. Administrator tizimi va Xavfsizlik
- **3 xil usulda Autentifikatsiya (Middleware):**
  1. **Telegram ID (`user_id`):** Bazadagi adminlar ro'yxati yoki `.env` dagi `ADMIN_IDS` superadminlar bilan solishtiriladi.
  2. **Username (`@nik`):** Bazaga `@username` orqali kiritilgan admin birinchi marta murojaat qilganda uning Telegram ID raqami avtomatik bog'lab qo'yiladi.
  3. **Telefon raqami (`phone_number`):** ID yoki username orqali topilmagan foydalanuvchidan `[ 📱 Telefon raqamni yuborish ]` tugmasi orqali kontakt yoki matn so'raladi. Yuborilgan raqam bazaga mos kelsa, Telegram ID bog'lanib, admin paneli ochiladi.
- **Admin paneli funksiyalari (`/admin`):**
  - **➕ Kitob qo'shish (FSM [1/5 - 5/5]):** Nomi ➡️ Muallifi ➡️ Muqovasi ➡️ Mazmuni (**950 belgidan oshmasligi** qat'iy nazorat qilinadi) ➡️ PDF fayli ➡️ Tasdiqlash.
  - **✏️ Kitoblarni boshqarish:** Barcha kitoblar ro'yxati, istalgan maydonni alohida tahrirlash yoki o'chirish.
  - **👥 Adminlar boshqaruvi:** Yangi admin qo'shish (Telegram ID, `@username` yoki `+998...` telefon raqami orqali) va adminlarni o'chirish.
  - **📊 Statistika:** Jami foydalanuvchilar, 24 soatdagi yangilar, jami kitoblar, jami yuklab olishlar va eng ko'p o'qilgan Top-5 kitoblar.
  - **📢 Xabar yuborish (Broadcast):** Barcha foydalanuvchilarga matn yoki media xabarlar yuborish, bloklaganlarni chetlab o'tish va batafsil hisobot berish.
- **Anti-flood / Rate Limiting Middleware:** Soniyasiga 1-2 tadan ko'p so'rov yuborishdan himoyalangan.
- **Global Error Handler:** Kutilmagan xatoliklar yuz berganda bot to'xtab qolmaydi, xato loglanadi va foydalanuvchiga muloyim javob beriladi.

---

## 🛠 Texnologiyalar steki

- **Til:** Python 3.11+ (Python 3.13)
- **Telegram Bot Framework:** `aiogram 3.31+` (Asinxron FSM, Middlewares, Router, Inline Query)
- **ORM / DB Engine:** `SQLAlchemy 2.0 (Asyncio)` + `asyncpg` + `aiosqlite`
- **Ma'lumotlar bazasi:**
  - Lokal sinov uchun: `SQLite (WAL rejimi bilan)`
  - Production uchun: `PostgreSQL` / `Supabase` + `pg_trgm` kengaytmasi
- **Deployment:** Docker & docker-compose

---

## 📁 Loyiha tuzilmasi

```text
online-kutubxona/
├── .env.example          # Namuna muhit o'zgaruvchilari
├── .env                  # Maxfiy sozlamalar (git ga kirmaydi)
├── .gitignore            # Git istisno fayllari
├── Dockerfile            # Docker konteynerlashtirish fayli
├── docker-compose.yml    # Docker Compose orqali 1-click ishga tushirish
├── requirements.txt      # Kerakli Python kutubxonalari
├── schema.sql            # Supabase / PostgreSQL uchun to'liq SQL script
├── config.py             # Sozlamalar konfiguratsiyasi (pydantic-settings)
├── bot.py                # Asosiy ishga tushirish fayli
├── database/
│   ├── base.py           # DB Engine, connection pool, init_db, close_db
│   ├── models.py         # User, Admin, Book modellari
│   └── crud.py           # Aqlli qidiruv, CRUD amallari, statistika
├── middlewares/
│   ├── db.py             # DB sessiyasi middleware'i
│   ├── throttling.py     # Anti-flood / Rate limiting middleware
│   └── auth.py           # Admin autentifikatsiyasi
├── filters/
│   └── admin.py          # Admin filtri
├── states/
│   └── states.py         # FSM holatlari
├── keyboards/
│   ├── user_kb.py        # Foydalanuvchi tugmalari va inline menyu
│   └── admin_kb.py       # Admin paneli boshqaruv tugmalari
└── handlers/
    ├── user.py           # /start, /search, /top, /help, inline query, yuklab olish
    ├── admin_panel.py    # /admin, telefon autentifikatsiyasi, statistika
    ├── admin_books.py    # Kitob qo'shish, tahrirlash, o'chirish
    ├── admin_manage.py   # Admin qo'shish va o'chirish
    └── admin_broadcast.py# Ommaviy bildirishnoma tarqatish
```

---

## ⚙️ O'rnatish va Ishga tushirish

### 1-usul: Oddiy ishga tushirish (Local)

```bash
# Virtual muhitni faollashtirish
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Kutubxonalarni o'rnatish
pip install -r requirements.txt

# Botni ishga tushirish
python bot.py
```

### 2-usul: Docker orqali ishga tushirish (Production)

```bash
docker compose up -d --build
```

---

## 🔗 Havolalar
- **GitHub repozitoriyasi:** [https://github.com/Tuxtamurod-Jurayev/Online-kutubxona](https://github.com/Tuxtamurod-Jurayev/Online-kutubxona)
- **Telegram bot:** [@online_libraries_bot](https://t.me/online_libraries_bot)
