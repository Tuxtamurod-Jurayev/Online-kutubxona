from datetime import datetime, timedelta, timezone
from typing import List, Tuple
from sqlalchemy import select, func, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Admin, Book


# ==============================================================
# FOYDALANUVCHILAR (USERS) BILAN ISHLASH
# ==============================================================

async def upsert_user(session: AsyncSession, telegram_id: int, username: str | None, full_name: str) -> User:
    """Foydalanuvchini bazaga qo'shish yoki mavjud ma'lumotlarini yangilash"""
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        user.username = username
        user.full_name = full_name
    else:
        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            created_at=datetime.now(timezone.utc)
        )
        session.add(user)

    await session.commit()
    await session.refresh(user)
    return user


async def get_all_user_ids(session: AsyncSession) -> List[int]:
    """Barcha foydalanuvchilarning Telegram ID larini olish (Broadcast uchun)"""
    stmt = select(User.telegram_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_users_count(session: AsyncSession) -> int:
    """Jami foydalanuvchilar soni"""
    stmt = select(func.count(User.id))
    result = await session.execute(stmt)
    return result.scalar() or 0


async def get_new_users_count_24h(session: AsyncSession) -> int:
    """So'nggi 24 soat ichida qo'shilgan yangi foydalanuvchilar soni"""
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    stmt = select(func.count(User.id)).where(User.created_at >= since)
    result = await session.execute(stmt)
    return result.scalar() or 0


# ==============================================================
# ADMINISTRATORLAR (ADMINS) BILAN ISHLASH
# ==============================================================

def clean_phone(phone: str | None) -> str | None:
    """Telefon raqamidan faqat raqamlarni ajratib olish (masalan: +998 (90) 123-45-67 -> 998901234567)"""
    if not phone:
        return None
    cleaned = "".join(ch for ch in phone if ch.isdigit())
    return cleaned


def clean_username(username: str | None) -> str | None:
    """Username'dan @ belgisini olib tashlash va kichik harfga o'tkazish"""
    if not username:
        return None
    cleaned = username.strip().lstrip("@").lower()
    return cleaned if cleaned else None


async def check_admin_by_id(session: AsyncSession, telegram_id: int) -> Admin | None:
    """Telegram ID bo'yicha adminni qidirish"""
    stmt = select(Admin).where(Admin.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def check_and_link_admin_by_username(session: AsyncSession, telegram_id: int, username: str) -> Admin | None:
    """
    Agar admin @username orqali kiritilgan bo'lsa, foydalanuvchining joriy username'i
    tekshiriladi va uning telegram_id raqami avtomatik bog'lab qo'yiladi.
    """
    cleaned_user = clean_username(username)
    if not cleaned_user:
        return None

    # Katta-kichik harflarni farqlamasdan username qidirish
    stmt = select(Admin).where(func.lower(Admin.username) == cleaned_user)
    result = await session.execute(stmt)
    admin = result.scalar_one_or_none()

    if admin:
        if admin.telegram_id != telegram_id:
            admin.telegram_id = telegram_id
            await session.commit()
            await session.refresh(admin)
        return admin

    return None


async def check_and_link_admin_by_phone(session: AsyncSession, telegram_id: int, phone_number: str) -> Admin | None:
    """
    Telefon raqami bo'yicha adminni tekshirish va uning telegram_id raqamini bog'lash.
    """
    cleaned_p = clean_phone(phone_number)
    if not cleaned_p:
        return None

    stmt = select(Admin)
    result = await session.execute(stmt)
    admins = result.scalars().all()

    for admin in admins:
        if admin.phone_number and clean_phone(admin.phone_number) == cleaned_p:
            if admin.telegram_id != telegram_id:
                admin.telegram_id = telegram_id
                await session.commit()
                await session.refresh(admin)
            return admin

    return None


async def add_new_admin(
    session: AsyncSession,
    telegram_id: int | None = None,
    username: str | None = None,
    phone_number: str | None = None
) -> Admin:
    """Yangi admin qo'shish"""
    cleaned_u = clean_username(username)
    cleaned_p = clean_phone(phone_number)

    admin = Admin(
        telegram_id=telegram_id,
        username=cleaned_u,
        phone_number=cleaned_p,
        added_at=datetime.now(timezone.utc)
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


async def get_all_admins(session: AsyncSession) -> List[Admin]:
    """Barcha adminlar ro'yxatini olish"""
    stmt = select(Admin).order_by(Admin.id.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def delete_admin(session: AsyncSession, admin_id: int) -> bool:
    """Adminni ID orqali o'chirish"""
    stmt = select(Admin).where(Admin.id == admin_id)
    result = await session.execute(stmt)
    admin = result.scalar_one_or_none()
    if admin:
        await session.delete(admin)
        await session.commit()
        return True
    return False


# ==============================================================
# KITOBLAR (BOOKS) BILAN ISHLASH
# ==============================================================

async def search_books(
    session: AsyncSession,
    query: str,
    limit: int = 10,
    offset: int = 0
) -> Tuple[List[Book], int]:
    """
    Kitob nomi va muallifi bo'yicha qisman moslik (ILIKE / LIKE) bilan qidirish.
    Natija va umumiy topilgan sonini qaytaradi.
    """
    clean_query = query.strip()
    pattern = f"%{clean_query}%"

    filter_cond = or_(
        Book.title.ilike(pattern),
        Book.author.ilike(pattern)
    )

    # Jami sonini hisoblash
    count_stmt = select(func.count(Book.id)).where(filter_cond)
    total_count = (await session.execute(count_stmt)).scalar() or 0

    # Natijalarni yuklash
    stmt = (
        select(Book)
        .where(filter_cond)
        .order_by(Book.downloads_count.desc(), Book.id.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    books = list(result.scalars().all())

    return books, total_count


async def get_book_by_id(session: AsyncSession, book_id: int) -> Book | None:
    """ID orqali bitta kitobni olish"""
    stmt = select(Book).where(Book.id == book_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def add_book(
    session: AsyncSession,
    title: str,
    author: str,
    description: str,
    photo_file_id: str,
    pdf_file_id: str
) -> Book:
    """Yangi kitob qo'shish"""
    book = Book(
        title=title.strip(),
        author=author.strip(),
        description=description.strip(),
        photo_file_id=photo_file_id,
        pdf_file_id=pdf_file_id,
        downloads_count=0,
        created_at=datetime.now(timezone.utc)
    )
    session.add(book)
    await session.commit()
    await session.refresh(book)
    return book


async def update_book(session: AsyncSession, book_id: int, **kwargs) -> Book | None:
    """Kitob ma'lumotlarini yangilash"""
    stmt = select(Book).where(Book.id == book_id)
    result = await session.execute(stmt)
    book = result.scalar_one_or_none()

    if not book:
        return None

    for key, val in kwargs.items():
        if hasattr(book, key) and val is not None:
            setattr(book, key, val)

    await session.commit()
    await session.refresh(book)
    return book


async def delete_book(session: AsyncSession, book_id: int) -> bool:
    """Kitobni o'chirish"""
    stmt = select(Book).where(Book.id == book_id)
    result = await session.execute(stmt)
    book = result.scalar_one_or_none()
    if book:
        await session.delete(book)
        await session.commit()
        return True
    return False


async def increment_downloads(session: AsyncSession, book_id: int) -> int:
    """Kitob yuklab olinganida downloads_count ni 1 taga oshirish"""
    stmt = (
        update(Book)
        .where(Book.id == book_id)
        .values(downloads_count=Book.downloads_count + 1)
        .returning(Book.downloads_count)
    )
    result = await session.execute(stmt)
    await session.commit()
    count = result.scalar()
    return count if count is not None else 0


async def get_books_count(session: AsyncSession) -> int:
    """Jami kitoblar soni"""
    stmt = select(func.count(Book.id))
    result = await session.execute(stmt)
    return result.scalar() or 0


async def get_total_downloads(session: AsyncSession) -> int:
    """Barcha kitoblar bo'yicha jami yuklab olishlar soni"""
    stmt = select(func.sum(Book.downloads_count))
    result = await session.execute(stmt)
    return result.scalar() or 0


async def get_top_downloaded_books(session: AsyncSession, limit: int = 5) -> List[Book]:
    """Eng ko'p yuklab olingan kitoblar ro'yxati"""
    stmt = (
        select(Book)
        .order_by(Book.downloads_count.desc(), Book.id.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_all_books(session: AsyncSession, limit: int = 50, offset: int = 0) -> Tuple[List[Book], int]:
    """Admin panel uchun barcha kitoblarni olish"""
    count_stmt = select(func.count(Book.id))
    total = (await session.execute(count_stmt)).scalar() or 0

    stmt = select(Book).order_by(Book.id.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all()), total
