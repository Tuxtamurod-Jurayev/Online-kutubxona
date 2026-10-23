from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database.models import Book


def get_start_kb() -> InlineKeyboardMarkup:
    """Boshlang'ich ekran uchun inline tugma"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 Kitobni izlash", callback_data="search_book")
            ]
        ]
    )


def get_retry_search_kb() -> InlineKeyboardMarkup:
    """Kitob topilmaganda yoki qayta qidirish uchun inline tugma"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 Qayta izlash", callback_data="search_book")
            ]
        ]
    )


def get_single_book_kb(book_id: int) -> InlineKeyboardMarkup:
    """1 ta kitob topilganda uning ostida chiquvchi tugmalar"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📥 PDF yuklab olish", callback_data=f"download_pdf:{book_id}")
            ],
            [
                InlineKeyboardButton(text="🔍 Boshqa kitob izlash", callback_data="search_book")
            ]
        ]
    )


def get_search_results_kb(
    books: List[Book],
    total_count: int,
    page: int = 1,
    per_page: int = 5,
    query: str = ""
) -> InlineKeyboardMarkup:
    """
    Bir nechta kitob topilganda ro'yxat va paginatsiya tugmalari.
    """
    buttons = []
    start_index = (page - 1) * per_page

    for i, book in enumerate(books, start=start_index + 1):
        btn_text = f"{i}. {book.title} — {book.author}"
        # Telegram inline tugma matni 64 belgigacha qisqartirish
        if len(btn_text) > 60:
            btn_text = btn_text[:57] + "..."
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"view_book:{book.id}")])

    # Paginatsiya tugmalari
    total_pages = (total_count + per_page - 1) // per_page
    nav_buttons = []
    if total_pages > 1:
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"page:{page-1}"))
        nav_buttons.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"page:{page+1}"))
        buttons.append(nav_buttons)

    # Qayta izlash tugmasi
    buttons.append([InlineKeyboardButton(text="🔍 Yangi qidiruv", callback_data="search_book")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_phone_auth_kb() -> ReplyKeyboardMarkup:
    """Admin bo'lish uchun telefon raqamini tasdiqlash reply tugmasi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Raqamni tasdiqlash", request_contact=True)],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
