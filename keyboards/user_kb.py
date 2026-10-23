from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database.models import Book


def get_start_kb(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Interaktiv boshlang'ich menyu tugmalari"""
    buttons = [
        [
            InlineKeyboardButton(text="🔍 Kitob qidirish", callback_data="search_book"),
            InlineKeyboardButton(text="🔥 Top kitoblar", callback_data="top_books")
        ]
    ]

    # Agar foydalanuvchi administrator bo'lsa, maxsus boshqaruv tugmasi chiqadi
    if is_admin:
        buttons.append([
            InlineKeyboardButton(text="⚡️ Administrator paneli 👑", callback_data="admin_open_from_start")
        ])

    buttons.append([
        InlineKeyboardButton(text="ℹ️ Bot haqida", callback_data="about_bot")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_retry_search_kb() -> InlineKeyboardMarkup:
    """Kitob topilmaganda yoki qayta qidirish uchun inline tugmalar"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 Qayta qidirish", callback_data="search_book"),
                InlineKeyboardButton(text="🔥 Top kitoblar", callback_data="top_books")
            ],
            [
                InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="back_to_home")
            ]
        ]
    )


def get_single_book_kb(book_id: int) -> InlineKeyboardMarkup:
    """1 ta kitob kartochkasi ostidagi tugmalar"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📥 PDF yuklab olish", callback_data=f"download_pdf:{book_id}")
            ],
            [
                InlineKeyboardButton(text="🔍 Boshqa kitob qidirish", callback_data="search_book"),
                InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="back_to_home")
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
        btn_text = f"📖 {i}. {book.title} — {book.author}"
        if len(btn_text) > 55:
            btn_text = btn_text[:52] + "..."
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

    # Qidiruv va uyga qaytish
    buttons.append([
        InlineKeyboardButton(text="🔍 Yangi qidiruv", callback_data="search_book"),
        InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="back_to_home")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_top_books_kb(books: List[Book]) -> InlineKeyboardMarkup:
    """Eng ko'p yuklangan top kitoblar ro'yxati tugmalari"""
    buttons = []
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for i, book in enumerate(books):
        m = medals[i] if i < len(medals) else "📖"
        btn_text = f"{m} {book.title} ({book.downloads_count} marta)"
        if len(btn_text) > 55:
            btn_text = btn_text[:52] + "..."
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"view_book:{book.id}")])

    buttons.append([
        InlineKeyboardButton(text="🔍 Kitob qidirish", callback_data="search_book"),
        InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="back_to_home")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_phone_auth_kb() -> ReplyKeyboardMarkup:
    """Admin bo'lish uchun telefon raqamini tasdiqlash reply tugmasi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
