-- ==============================================================
-- ELEKTRON KUTUBXONA TELEGRAM BOTI - DATABASE SCHEMA (PostgreSQL / Supabase)
-- ==============================================================

-- 1. Matnli qidiruvni (ILIKE / Trigram) tezlashtirish uchun pg_trgm kengaytmasi
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. Foydalanuvchilar jadvali (users)
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(100),
    full_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users (telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users (created_at);

-- 3. Administratorlar jadvali (admins)
CREATE TABLE IF NOT EXISTS admins (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    username VARCHAR(100),
    phone_number VARCHAR(20),
    added_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_admins_telegram_id ON admins (telegram_id);
CREATE INDEX IF NOT EXISTS idx_admins_username ON admins (username);
CREATE INDEX IF NOT EXISTS idx_admins_phone_number ON admins (phone_number);

-- 4. Kitoblar jadvali (books)
CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    photo_file_id VARCHAR(255) NOT NULL,
    pdf_file_id VARCHAR(255) NOT NULL,
    downloads_count INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Kitob nomi va muallifi bo'yicha tezkor trigram (fuzzy / ILIKE) indekslari
CREATE INDEX IF NOT EXISTS idx_books_title_trgm ON books USING gin (title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_books_author_trgm ON books USING gin (author gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_books_downloads ON books (downloads_count DESC);
CREATE INDEX IF NOT EXISTS idx_books_created_at ON books (created_at DESC);

-- ==============================================================
-- Dastlabki sinov uchun namunaviy ma'lumotlar (ixtiyoriy)
-- ==============================================================
-- INSERT INTO admins (username, phone_number) VALUES ('your_admin_username', '998901234567');
