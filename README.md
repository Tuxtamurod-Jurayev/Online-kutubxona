# 📚 Elektron Kutubxona va Kitob Qidiruv Telegram Boti

Ushbu loyiha **Telegram Bot API**, **Python (Aiogram 3.x)** va **SQLAlchemy (Asyncio)** texnologiyalari asosida Texnik Topshiriq (TZ) talablariga 100% mos ravishda ishlab chiqilgan.

Bot foydalanuvchilarga kitob nomi yoki muallifi bo'yicha elektron kitoblarni (PDF) tezkor topish, annotatsiyasi bilan tanishish va yuklab olish imkonini beradi. Administratorlar uchun esa ko'p bosqichli xavfsizlik (3 xil usulda autentifikatsiya), kitob qo'shish/tahrirlash/o'chirish, statistika va ommaviy xabar yuborish (broadcast) boshqaruv paneli mavjud.

---

## 🚀 Asosiy imkoniyatlar

### 1. Foydalanuvchi qismi (User Flow)
- **`/start` ekrani:** Foydalanuvchi ma'lumotlari (`telegram_id`, `username`, `full_name`) avtomatik bazaga yoziladi va `[ 🔍 Kitobni izlash ]` inline tugmasi taqdim etiladi.
- **Tezkor qidiruv (FSM):** Foydalanuvchi kitob nomi yoki muallif ismini yozadi. Qidiruv katta-kichik harflarni farqlamasdan qismiy moslik (`ILIKE`) bo'yicha amalga oshiriladi.
- **Qidiruv natijalari:**
  - **1 ta kitob topilsa:** Kitob muqovasi (rasmi), nomi, muallifi, annotatsiyasi va uning ostida `[ 📥 PDF yuklab olish ]` hamda `[ 🔍 Boshqa kitob izlash ]` tugmalari chiqadi.
  - **Bir nechta kitob topilsa:** Barcha topilgan kitoblar ro'yxati va qulay sahifalash (paginatsiya) bilan inline tugmalarda chiqariladi.
  - **Kitob topilmasa:** *"Kechirasiz, so'rovingiz bo'yicha kitob topilmadi..."* xabari va `[ 🔍 Qayta izlash ]` tugmasi chiqadi.
- **Tezkor PDF yuklab olish:** Fayllar mahalliy diskda emas, Telegram serverlarida saqlanadi (`file_id` orqali), bu esa 50 MB gacha bo'lgan kitoblarni soniyaning ulushlarida yetkazib beradi va `downloads_count` hisoblagichini oshiradi.

### 2. Administrator tizimi va Xavfsizlik
- **3 xil usulda Autentifikatsiya (Middleware):**
  1. **Telegram ID (`user_id`):** Bazadagi adminlar ro'yxati yoki `.env` dagi `ADMIN_IDS` superadminlar bilan solishtiriladi.
  2. **Username (`@nik`):** Bazaga `@username` orqali kiritilgan admin birinchi marta `/admin` yozganida uning Telegram ID raqami avtomatik bog'lab qo'yiladi.
  3. **Telefon raqami (`phone_number`):** ID yoki username orqali topilmagan foydalanuvchidan `[ 📱 Raqamni tasdiqlash ]` tugmasi orqali kontakt so'raladi. Yuborilgan raqam bazaga mos kelsa, Telegram ID bog'lanib, admin paneli ochiladi.
- **Admin paneli funksiyalari (`/admin`):**
  - **➕ Kitob qo'shish (FSM):**
    - 1-qadam: Kitob nomi
    - 2-qadam: Muallif ismi
    - 3-qadam: Kitob muqovasi (rasm)
    - 4-qadam: Kitob annotatsiyasi (Telegram cheklovi hisobga olingan holda **950 belgidan oshmasligi** nazorat qilinadi)
    - 5-qadam: Kitobning PDF fayli
    - Tasdiqlash va saqlash
  - **✏️ Kitoblarni boshqarish:** Barcha kitoblar ro'yxati, istalgan maydonni alohida tahrirlash (nomi, muallifi, tavsifi, muqovasi, PDF fayli) yoki bazadan butunlay o'chirish.
  - **👥 Adminlar boshqaruvi:** Yangi admin qo'shish (Telegram ID, `@username` yoki `+998...` telefon raqami orqali) va adminlarni o'chirish.
  - **📊 Statistika:** Jami foydalanuvchilar, 24 soatdagi yangilar, jami kitoblar, jami yuklab olishlar va eng ko'p o'qilgan Top-5 kitoblar.
  - **📢 Xabar yuborish (Broadcast):** Barcha foydalanuvchilarga matn yoki media xabarlar yuborish, bloklaganlarni chetlab o'tish va batafsil hisobot berish.
- **Anti-flood / Rate Limiting Middleware:** Soniyasiga 1-2 tadan ko'p so'rov yuborishdan himoyalangan.

---

## 🛠 Texnologiyalar steki

- **Til:** Python 3.11+ (Python 3.13 qo'llab-quvvatlanadi)
- **Telegram Bot Framework:** `aiogram 3.31+` (Asinxron FSM, Middlewares, Router)
- **ORM / DB Engine:** `SQLAlchemy 2.0 (Asyncio)` + `asyncpg` + `aiosqlite`
- **Ma'lumotlar bazasi:**
  - Ishlab chiqish / Sinov (Lokal): `SQLite` (`sqlite+aiosqlite:///bot.db`)
  - Ishlab chiqarish (Production): `PostgreSQL` yoki `Supabase` (`postgresql+asyncpg://...`) + `pg_trgm` kengaytmasi

---

## 📁 Loyiha tuzilmasi

```text
online-kutubxona/
├── .env.example          # Namuna muhit o'zgaruvchilari
├── .gitignore            # Git e'tiborsiz qoldiradigan fayllar
├── requirements.txt      # Kerakli Python kutubxonalari
├── schema.sql            # Supabase / PostgreSQL uchun to'liq SQL script
├── config.py             # Sozlamalar konfiguratsiyasi (pydantic-settings)
├── bot.py                # Asosiy ishga tushirish fayli
├── database/
│   ├── base.py           # DB Engine, async session maker, init_db
│   ├── models.py         # User, Admin, Book SQLAlchemy modellari
│   └── crud.py           # Bazadagi barcha amallar (qidiruv, adminlar, statistika)
├── middlewares/
│   ├── db.py             # Har bir so'rovga DB sessiyasini beruvchi middleware
│   ├── throttling.py     # Anti-flood / Rate limiting middleware
│   └── auth.py           # Admin autentifikatsiya middleware'i (3 usul)
├── filters/
│   └── admin.py          # Admin huquqini tekshiruvchi filtr
├── states/
│   └── states.py         # FSM holatlari (qidiruv, kitob qo'shish, admin boshqaruvi)
├── keyboards/
│   ├── user_kb.py        # Foydalanuvchi inline va reply tugmalari
│   └── admin_kb.py       # Admin paneli inline tugmalari
└── handlers/
    ├── user.py           # /start, kitob qidiruv, natijalarni ko'rish, PDF yuklab olish
    ├── admin_panel.py    # /admin, telefon autentifikatsiyasi, bosh menyu, statistika
    ├── admin_books.py    # Kitob qo'shish (FSM), tahrirlash, o'chirish
    ├── admin_manage.py   # Admin qo'shish va o'chirish
    └── admin_broadcast.py# Ommaviy xabar yuborish
```

---

## ⚙️ O'rnatish va Ishga tushirish

### 1. Virtual muhitni faollashtirish va kutubxonalarni o'rnatish

```bash
# Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Sozlamalarni sozlash (`.env`)

Loyiha ildizida `.env` faylini yarating (`.env.example` dan nusxa oling):

```env
# Telegram Bot Token (@BotFather orqali olinadi)
BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRstuVWXyz

# Super Admin Telegram ID raqamingiz (vergul bilan bir nechta yozish mumkin)
ADMIN_IDS=123456789

# Ma'lumotlar bazasi URL manzili
# Lokal SQLite uchun:
DATABASE_URL=sqlite+aiosqlite:///bot.db

# Yoki PostgreSQL / Supabase uchun:
# DATABASE_URL=postgresql+asyncpg://postgres:parol@db.supabase.co:5432/postgres

# Rate limit (sekundiga xabarlar chegarasi)
RATE_LIMIT=1.0
```

> **Maslahat:** O'zingizning Telegram ID raqamingizni bilish uchun Telegramda `@userinfobot` ga `/start` yuborishingiz mumkin.

### 3. Ma'lumotlar bazasini sozlash

- **Agar SQLite ishlatilsa:** Hech qanday qo'shimcha harakat talab etilmaydi! Bot birinchi marta ishga tushganda `bot.db` faylini va barcha jadvallarni o'zi avtomatik yaratadi.
- **Agar PostgreSQL yoki Supabase ishlatilsa:**
  `schema.sql` fayli ichidagi SQL so'rovlarini Supabase SQL Editor'ida yoki `psql` orqali ishga tushiring. Bu `pg_trgm` kengaytmasini va trigram indekslarini yaratadi.

### 4. Botni ishga tushirish

```bash
python bot.py
```

---

## 📖 Botdan foydalanish yo'riqnomasi

### Oddiy foydalanuvchi sifatida:
1. Botga `/start` yuboring.
2. `[ 🔍 Kitobni izlash ]` tugmasini bosing.
3. Kitob nomi (masalan: *"O'tkan kunlar"*) yoki muallif nomini (masalan: *"Abdulla Qodiriy"*) yuboring.
4. Topilgan kitobning `[ 📥 PDF yuklab olish ]` tugmasini bosing.

### Administrator sifatida:
1. Botga `/admin` buyrug'ini yuboring.
2. Agar `.env` da ID ko'rsatilgan bo'lsa, to'g'ridan-to'g'ri admin panel ochiladi.
3. Agar ID ko'rsatilmagan bo'lsa, `[ 📱 Raqamni tasdiqlash ]` tugmasini bosing (agar raqamingiz bazadagi adminlar ro'yxatida bo'lsa, sizga ruxsat beriladi).
4. Menyu orqali:
   - **➕ Kitob qo'shish:** Nomi -> Muallif -> Rasm -> Annotatsiya (950 belgigacha) -> PDF fayl -> Saqlash.
   - **✏️ Kitoblarni boshqarish:** Baza kitoblarini ko'rish, tahrirlash yoki o'chirish.
   - **👥 Adminlar boshqaruvi:** Yangi adminlarni ID, username yoki telefon orqali biriktirish.
   - **📊 Statistika:** Foydalanuvchilar, yuklashlar va Top-5 kitoblar hisobotini ko'rish.
   - **📢 Broadcast:** Foydalanuvchilarga ommaviy bildirishnoma tarqatish.
